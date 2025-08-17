#!/usr/bin/env python3
"""
Core functionality tests for the backtesting engine
Tests the essential components that are known to be implemented
"""

import sys
import os
import unittest
import tempfile
import csv
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.data_loader import DataLoader
from backtesting_engine.position_manager import PositionManager
from backtesting_engine.models import MarketData, Position, Trade


class TestCoreDataLoading(unittest.TestCase):
    """Test core data loading functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(self.test_dir)
    
    def test_supported_symbols(self):
        """Test that all expected symbols are supported"""
        expected_symbols = ["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"]
        self.assertEqual(self.data_loader.get_supported_symbols(), expected_symbols)
    
    def test_file_suffix_mapping(self):
        """Test correct file suffix mapping for different symbols"""
        self.assertEqual(self.data_loader._get_file_suffix("QQQ"), "")
        self.assertEqual(self.data_loader._get_file_suffix("QQQ 1DTE"), "F")
        self.assertEqual(self.data_loader._get_file_suffix("SPY"), "B")
        self.assertEqual(self.data_loader._get_file_suffix("SPY 1DTE"), "M")
    
    def test_strikes_near_spot_selection(self):
        """Test strike selection near spot price"""
        option_chain = {
            "CE": {570.0: 12.0, 575.0: 8.5, 580.0: 5.2, 585.0: 2.8, 590.0: 1.1},
            "PE": {570.0: 1.1, 575.0: 2.1, 580.0: 4.8, 585.0: 7.9, 590.0: 12.0}
        }
        spot_price = 580.0
        
        strikes = self.data_loader.get_strikes_near_spot(spot_price, option_chain, num_strikes=3)
        
        self.assertEqual(len(strikes), 3)
        self.assertIn(580.0, strikes)  # Should include ATM
        self.assertTrue(all(isinstance(strike, float) for strike in strikes))
    
    def test_option_price_lookup(self):
        """Test direct option price lookup functionality"""
        option_data = {
            1000: {
                "CE": {580.0: 5.2, 585.0: 2.8},
                "PE": {575.0: 2.1, 580.0: 4.8}
            }
        }
        
        # Test successful lookup
        price = self.data_loader.get_option_price(option_data, 1000, "CE", 580.0)
        self.assertEqual(price, 5.2)
        
        # Test missing data
        price = self.data_loader.get_option_price(option_data, 1000, "CE", 590.0)
        self.assertIsNone(price)


class TestCorePositionManagement(unittest.TestCase):
    """Test core position management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.position_manager = PositionManager()
        
        self.market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 8.5, 580.0: 5.2, 585.0: 2.8},
                "PE": {575.0: 2.1, 580.0: 4.8, 585.0: 7.9}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
    
    def test_position_creation_and_tracking(self):
        """Test basic position creation and tracking"""
        position = Position(
            setup_id="test_setup",
            entry_timeindex=1000,
            entry_prices={"CE_580.0": 5.2, "PE_580.0": 4.8},
            strikes={"CE": 580.0, "PE": 580.0},
            quantity=1,
            target_pnl=50.0,
            stop_loss_pnl=-100.0,
            position_type="SELL"
        )
        
        position_id = self.position_manager.add_position(position)
        self.assertIsNotNone(position_id)
        self.assertIn(position_id, self.position_manager.positions)
    
    def test_pnl_calculation(self):
        """Test P&L calculation with price changes"""
        position = Position(
            setup_id="test_setup",
            entry_timeindex=1000,
            entry_prices={"CE_580.0": 5.2, "PE_580.0": 4.8},
            strikes={"CE": 580.0, "PE": 580.0},
            quantity=1,
            target_pnl=50.0,
            stop_loss_pnl=-100.0,
            position_type="SELL"
        )
        
        position_id = self.position_manager.add_position(position)
        
        # Update with new market data
        new_market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=585.0,
            option_prices={
                "CE": {575.0: 12.0, 580.0: 8.0, 585.0: 5.0},
                "PE": {575.0: 1.0, 580.0: 3.0, 585.0: 6.0}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        trades = self.position_manager.update_positions(new_market_data)
        
        # Check that position P&L was updated
        updated_position = self.position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_total_pnl_calculation(self):
        """Test total P&L calculation across multiple positions"""
        # Create multiple positions
        positions = [
            Position(
                setup_id="test_setup_1",
                entry_timeindex=1000,
                entry_prices={"CE_580.0": 5.2},
                strikes={"CE": 580.0},
                quantity=1,
                target_pnl=25.0,
                stop_loss_pnl=-50.0,
                position_type="SELL"
            ),
            Position(
                setup_id="test_setup_2",
                entry_timeindex=1000,
                entry_prices={"PE_580.0": 4.8},
                strikes={"PE": 580.0},
                quantity=1,
                target_pnl=25.0,
                stop_loss_pnl=-50.0,
                position_type="SELL"
            )
        ]
        
        for position in positions:
            self.position_manager.add_position(position)
        
        total_pnl = self.position_manager.get_total_pnl()
        self.assertIsInstance(total_pnl, float)
    
    def test_position_closure(self):
        """Test position closure functionality"""
        position = Position(
            setup_id="test_setup",
            entry_timeindex=1000,
            entry_prices={"CE_580.0": 5.2},
            strikes={"CE": 580.0},
            quantity=1,
            target_pnl=25.0,
            stop_loss_pnl=-50.0,
            position_type="SELL"
        )
        
        position_id = self.position_manager.add_position(position)
        
        # Close all positions
        trades = self.position_manager.close_all_positions(self.market_data, "TEST_CLOSE")
        
        self.assertGreater(len(trades), 0)
        self.assertEqual(len(self.position_manager.positions), 0)


class TestCoreStrategies(unittest.TestCase):
    """Test core strategy functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 8.5, 580.0: 5.2, 585.0: 2.8},
                "PE": {575.0: 2.1, 580.0: 4.8, 585.0: 7.9}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
    
    def test_straddle_setup_basic_functionality(self):
        """Test basic straddle setup functionality"""
        try:
            from backtesting_engine.strategies import StraddleSetup
            
            setup = StraddleSetup(
                setup_id="test_straddle",
                target_pct=50.0,
                stop_loss_pct=100.0,
                entry_timeindex=1000,
                scalping_price=0.40
            )
            
            # Test entry condition
            self.assertTrue(setup.check_entry_condition(1000))
            self.assertFalse(setup.check_entry_condition(999))
            
            # Test strike selection
            strikes = setup.select_strikes(self.market_data.spot_price, self.market_data.option_prices)
            self.assertIsInstance(strikes, dict)
            
            # Test position creation
            positions = setup.create_positions(self.market_data)
            self.assertIsInstance(positions, list)
            
        except ImportError:
            self.skipTest("StraddleSetup not available")
    
    def test_gamma_scalping_basic_functionality(self):
        """Test basic gamma scalping functionality if available"""
        try:
            from backtesting_engine.strategies import GammaScalpingSetup
            
            setup = GammaScalpingSetup(
                setup_id="test_gamma",
                target_pct=50.0,
                stop_loss_pct=100.0,
                entry_timeindex=1000,
                delta_threshold=0.10
            )
            
            # Test entry condition
            self.assertTrue(setup.check_entry_condition(1000))
            
            # Test position creation
            positions = setup.create_positions(self.market_data)
            self.assertIsInstance(positions, list)
            
            if positions:
                position = positions[0]
                self.assertEqual(position.position_type, "GAMMA_SCALP")
            
        except ImportError:
            self.skipTest("GammaScalpingSetup not available")


class TestCoreIntegration(unittest.TestCase):
    """Test integration between core components"""
    
    def test_data_loader_position_manager_integration(self):
        """Test integration between data loader and position manager"""
        # Create mock data
        option_data = {
            1000: {
                "CE": {580.0: 5.2, 585.0: 2.8},
                "PE": {575.0: 2.1, 580.0: 4.8}
            },
            1100: {
                "CE": {580.0: 4.8, 585.0: 2.5},
                "PE": {575.0: 2.3, 580.0: 5.0}
            }
        }
        
        data_loader = DataLoader()
        position_manager = PositionManager()
        
        # Test option price lookup
        price_1000 = data_loader.get_option_price(option_data, 1000, "CE", 580.0)
        price_1100 = data_loader.get_option_price(option_data, 1100, "CE", 580.0)
        
        self.assertEqual(price_1000, 5.2)
        self.assertEqual(price_1100, 4.8)
        
        # Create position using initial price
        position = Position(
            setup_id="integration_test",
            entry_timeindex=1000,
            entry_prices={"CE_580.0": price_1000},
            strikes={"CE": 580.0},
            quantity=1,
            target_pnl=25.0,
            stop_loss_pnl=-50.0,
            position_type="SELL"
        )
        
        position_id = position_manager.add_position(position)
        
        # Update with new market data
        market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=582.0,
            option_prices=option_data[1100],
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        trades = position_manager.update_positions(market_data)
        
        # Verify integration worked
        updated_position = position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)


def run_core_tests():
    """Run core functionality tests"""
    print("Running Core Functionality Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add core test classes
    test_classes = [
        TestCoreDataLoading,
        TestCorePositionManagement,
        TestCoreStrategies,
        TestCoreIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Core Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nCore Tests Result: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    run_core_tests()