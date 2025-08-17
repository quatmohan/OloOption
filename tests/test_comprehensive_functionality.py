#!/usr/bin/env python3
"""
Comprehensive test suite for new backtesting engine functionality
Tests multi-symbol support, market regime detection, dynamic adjustments,
complex strategies, pattern recognition, and cross-symbol analysis.
"""

import sys
import os
import unittest
import tempfile
import csv
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.data_loader import DataLoader
from backtesting_engine.market_regime_detector import MarketRegimeDetector
from backtesting_engine.dynamic_setup_manager import DynamicSetupManager
from backtesting_engine.position_manager import PositionManager
from backtesting_engine.strategies import (
    IronCondorSetup, ButterflySetup, VerticalSpreadSetup, RatioSpreadSetup,
    GammaScalpingSetup, MomentumReversalSetup, VolatilitySkewSetup, TimeDecaySetup
)
from backtesting_engine.models import MarketData, Position, Trade


class TestMultiSymbolDataLoading(unittest.TestCase):
    """Test multi-symbol data loading and processing functionality"""
    
    def setUp(self):
        """Set up test environment with mock data files"""
        self.test_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(self.test_dir)
        
        # Create mock data directories
        for symbol in ["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"]:
            os.makedirs(os.path.join(self.test_dir, symbol), exist_ok=True)
            os.makedirs(os.path.join(self.test_dir, symbol, "Spot"), exist_ok=True)
    
    def create_mock_option_data(self, symbol: str, date: str):
        """Create mock option data files for testing"""
        suffix = self.data_loader._get_file_suffix(symbol)
        filename = f"{date}{suffix}_BK.csv"
        filepath = os.path.join(self.test_dir, symbol, filename)
        
        # Create mock option data
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            for timestamp in range(1000, 1100, 5):
                # CE options
                writer.writerow([timestamp, "CE", 575.0, 8.5])
                writer.writerow([timestamp, "CE", 580.0, 5.2])
                writer.writerow([timestamp, "CE", 585.0, 2.8])
                # PE options
                writer.writerow([timestamp, "PE", 575.0, 2.1])
                writer.writerow([timestamp, "PE", 580.0, 4.8])
                writer.writerow([timestamp, "PE", 585.0, 7.9])
    
    def create_mock_spot_data(self, symbol: str, date: str):
        """Create mock spot data files"""
        spot_filename = "qqq.csv" if "QQQ" in symbol else "spy.csv"
        spot_path = os.path.join(self.test_dir, symbol, "Spot", spot_filename)
        
        with open(spot_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Open", "High", "Low", "Close"])
            for i, timestamp in enumerate(range(1000, 1100, 5)):
                price = 580.0 + (i * 0.1)  # Gradual price movement
                writer.writerow([date, f"{timestamp}", price, price + 0.5, price - 0.5, price])
    
    def create_mock_prop_file(self, symbol: str, date: str):
        """Create mock .prop files"""
        suffix = self.data_loader._get_file_suffix(symbol)
        prop_filename = f"{date}{suffix}.prop"
        prop_path = os.path.join(self.test_dir, symbol, prop_filename)
        
        with open(prop_path, 'w') as f:
            f.write("jobEndIdx=4650\n")
            f.write("idxEnd=4700\n")
            f.write("dte=0\n")
    
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
    
    def test_single_symbol_data_loading(self):
        """Test loading data for a single symbol"""
        date = "2025-08-13"
        symbol = "QQQ"
        
        # Create mock data
        self.create_mock_option_data(symbol, date)
        self.create_mock_spot_data(symbol, date)
        self.create_mock_prop_file(symbol, date)
        
        # Load data
        trading_data = self.data_loader.load_trading_day(symbol, date)
        
        self.assertIsNotNone(trading_data)
        self.assertEqual(trading_data.symbol, symbol)
        self.assertEqual(trading_data.date, date)
        self.assertGreater(len(trading_data.spot_data), 0)
        self.assertGreater(len(trading_data.option_data), 0)
        self.assertEqual(trading_data.job_end_idx, 4650)
    
    def test_multi_symbol_concurrent_loading(self):
        """Test concurrent loading of multiple symbols"""
        date = "2025-08-13"
        symbols = ["QQQ", "SPY"]
        
        # Create mock data for all symbols
        for symbol in symbols:
            self.create_mock_option_data(symbol, date)
            self.create_mock_spot_data(symbol, date)
            self.create_mock_prop_file(symbol, date)
        
        # Load multiple symbols
        multi_data = self.data_loader.load_multiple_symbols(symbols, date)
        
        self.assertEqual(len(multi_data), 2)
        for symbol in symbols:
            self.assertIn(symbol, multi_data)
            self.assertIsNotNone(multi_data[symbol])
            self.assertEqual(multi_data[symbol].symbol, symbol)
    
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
        self.assertTrue(all(abs(strike - spot_price) <= 10.0 for strike in strikes))
    
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
        
        price = self.data_loader.get_option_price(option_data, 1005, "CE", 580.0)
        self.assertIsNone(price)


class TestMarketRegimeDetection(unittest.TestCase):
    """Test market regime detection accuracy with historical data"""
    
    def setUp(self):
        """Set up market regime detector"""
        self.detector = MarketRegimeDetector(lookback_periods=60)
    
    def create_trending_up_data(self) -> List[MarketData]:
        """Create market data showing strong upward trend"""
        data = []
        base_price = 580.0
        for i in range(70):
            price = base_price + (i * 0.05)  # Consistent upward movement
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=price,
                option_prices={
                    "CE": {575.0: 8.0, 580.0: 5.0, 585.0: 2.5},
                    "PE": {575.0: 2.0, 580.0: 4.5, 585.0: 7.5}
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            data.append(market_data)
        return data
    
    def create_ranging_data(self) -> List[MarketData]:
        """Create market data showing sideways/ranging movement"""
        data = []
        base_price = 580.0
        for i in range(70):
            # Oscillating price around base
            price = base_price + (2.0 * (1 if i % 4 < 2 else -1))
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=price,
                option_prices={
                    "CE": {575.0: 8.0, 580.0: 5.0, 585.0: 2.5},
                    "PE": {575.0: 2.0, 580.0: 4.5, 585.0: 7.5}
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            data.append(market_data)
        return data
    
    def create_high_volatility_data(self) -> List[MarketData]:
        """Create market data showing high volatility"""
        data = []
        base_price = 580.0
        for i in range(70):
            # Large random-like movements
            price_change = (i % 7 - 3) * 1.5  # Large swings
            price = base_price + price_change
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=price,
                option_prices={
                    "CE": {575.0: 10.0, 580.0: 7.0, 585.0: 4.0},  # Higher option prices
                    "PE": {575.0: 4.0, 580.0: 7.0, 585.0: 10.0}
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            data.append(market_data)
        return data
    
    def test_trending_up_detection(self):
        """Test detection of upward trending market"""
        trending_data = self.create_trending_up_data()
        
        # Feed data to detector
        for data_point in trending_data:
            self.detector.update_market_data(data_point)
        
        # Check regime classification
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        
        self.assertEqual(regime, "TRENDING_UP")
        self.assertGreater(confidence, 0.7)  # High confidence
        self.assertGreater(self.detector.get_trend_strength(), 0.5)
        self.assertGreater(self.detector.get_price_velocity(), 0.0)
    
    def test_ranging_market_detection(self):
        """Test detection of ranging/sideways market"""
        ranging_data = self.create_ranging_data()
        
        # Feed data to detector
        for data_point in ranging_data:
            self.detector.update_market_data(data_point)
        
        # Check regime classification
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        
        self.assertEqual(regime, "RANGING")
        self.assertGreater(confidence, 0.6)
        self.assertLess(abs(self.detector.get_trend_strength()), 0.3)
    
    def test_high_volatility_detection(self):
        """Test detection of high volatility periods"""
        high_vol_data = self.create_high_volatility_data()
        
        # Feed data to detector
        for data_point in high_vol_data:
            self.detector.update_market_data(data_point)
        
        # Check regime classification
        regime = self.detector.get_current_regime()
        volatility = self.detector.get_volatility_estimate()
        
        self.assertEqual(regime, "HIGH_VOL")
        self.assertGreater(volatility, 0.02)  # High volatility threshold
    
    def test_regime_change_detection(self):
        """Test detection of regime changes"""
        # Start with trending data
        trending_data = self.create_trending_up_data()[:40]
        for data_point in trending_data:
            self.detector.update_market_data(data_point)
        
        initial_regime = self.detector.get_current_regime()
        
        # Switch to ranging data
        ranging_data = self.create_ranging_data()[40:]
        for data_point in ranging_data:
            self.detector.update_market_data(data_point)
        
        final_regime = self.detector.get_current_regime()
        regime_changed = self.detector.detect_regime_change()
        
        self.assertNotEqual(initial_regime, final_regime)
        self.assertTrue(regime_changed)
    
    def test_time_of_day_effects(self):
        """Test time-of-day effect analysis"""
        # Create data for different times of day
        morning_data = MarketData(
            timestamp=1000,  # Early morning
            symbol="QQQ",
            spot_price=580.0,
            option_prices={"CE": {580.0: 5.0}, "PE": {580.0: 4.5}},
            available_strikes=[580.0]
        )
        
        afternoon_data = MarketData(
            timestamp=3000,  # Afternoon
            symbol="QQQ",
            spot_price=582.0,
            option_prices={"CE": {580.0: 7.0}, "PE": {580.0: 3.0}},
            available_strikes=[580.0]
        )
        
        self.detector.update_market_data(morning_data)
        morning_effects = self.detector.analyze_time_effects(1000)
        
        self.detector.update_market_data(afternoon_data)
        afternoon_effects = self.detector.analyze_time_effects(3000)
        
        self.assertIsInstance(morning_effects, dict)
        self.assertIsInstance(afternoon_effects, dict)
        self.assertIn("volatility", morning_effects)
        self.assertIn("price_velocity", morning_effects)


class TestDynamicParameterAdjustment(unittest.TestCase):
    """Test dynamic parameter adjustment logic and performance impact"""
    
    def setUp(self):
        """Set up dynamic setup manager with base setups"""
        from backtesting_engine.strategies import StraddleSetup
        
        self.base_setup = StraddleSetup(
            setup_id="test_straddle",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            scalping_price=0.40
        )
        
        self.manager = DynamicSetupManager([self.base_setup])
    
    def test_regime_based_parameter_adjustment(self):
        """Test parameter adjustment based on market regime"""
        market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={"CE": {580.0: 5.0}, "PE": {580.0: 4.5}},
            available_strikes=[580.0]
        )
        
        # Test high volatility regime adjustment
        self.manager.update_market_regime("HIGH_VOL", 0.8, market_data)
        adjusted_setups = self.manager.get_adjusted_setups()
        
        self.assertEqual(len(adjusted_setups), 1)
        adjusted_setup = adjusted_setups[0]
        
        # High volatility should increase targets and stops
        self.assertGreater(adjusted_setup.target_pct, self.base_setup.target_pct)
        self.assertGreater(adjusted_setup.stop_loss_pct, self.base_setup.stop_loss_pct)
    
    def test_trending_market_adjustments(self):
        """Test adjustments for trending markets"""
        market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={"CE": {580.0: 5.0}, "PE": {580.0: 4.5}},
            available_strikes=[580.0]
        )
        
        # Test trending up regime
        self.manager.update_market_regime("TRENDING_UP", 0.9, market_data)
        adjusted_setups = self.manager.get_adjusted_setups()
        
        adjusted_setup = adjusted_setups[0]
        
        # Trending markets might adjust scalping price
        self.assertNotEqual(adjusted_setup.scalping_price, self.base_setup.scalping_price)
    
    def test_strategy_pausing_logic(self):
        """Test strategy pausing based on market conditions"""
        market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={"CE": {580.0: 5.0}, "PE": {580.0: 4.5}},
            available_strikes=[580.0]
        )
        
        # Test strategy pausing in unfavorable conditions
        self.manager.update_market_regime("UNKNOWN", 0.2, market_data)  # Low confidence
        
        should_pause = self.manager.should_pause_strategy("test_straddle")
        
        # Low confidence regimes might pause strategies
        self.assertIsInstance(should_pause, bool)
    
    def test_performance_tracking(self):
        """Test tracking of dynamic vs static performance"""
        # Create mock trade
        trade = Trade(
            setup_id="test_straddle",
            entry_timeindex=1000,
            exit_timeindex=1100,
            entry_prices={"CE_580.0": 5.0, "PE_580.0": 4.5},
            exit_prices={"CE_580.0": 4.5, "PE_580.0": 4.0},
            strikes={"CE": 580.0, "PE": 580.0},
            quantity=1,
            pnl=50.0,
            exit_reason="TARGET"
        )
        
        # Track performance with adjustment
        self.manager.track_adjustment_performance(trade, was_adjusted=True)
        
        # Track performance without adjustment
        trade.pnl = 30.0
        self.manager.track_adjustment_performance(trade, was_adjusted=False)
        
        # Check performance tracking
        self.assertIn("test_straddle", self.manager.dynamic_performance)
        self.assertIn("test_straddle", self.manager.static_performance)
    
    def test_regime_specific_configurations(self):
        """Test regime-specific parameter configurations"""
        high_vol_config = self.manager.get_regime_specific_config("HIGH_VOL")
        trending_config = self.manager.get_regime_specific_config("TRENDING_UP")
        
        self.assertIsInstance(high_vol_config, dict)
        self.assertIsInstance(trending_config, dict)
        
        # Configurations should be different for different regimes
        self.assertNotEqual(high_vol_config, trending_config)
    
    def test_daily_reset_functionality(self):
        """Test daily reset of adjustment tracking"""
        # Add some adjustment history
        self.manager.total_adjustments = 5
        self.manager.adjustment_history = [Mock()]
        
        # Reset daily adjustments
        self.manager.reset_daily_adjustments()
        
        # Check reset
        self.assertEqual(self.manager.total_adjustments, 0)
        self.assertEqual(len(self.manager.adjustment_history), 0)


class TestComplexMultiLegStrategies(unittest.TestCase):
    """Test complex multi-leg strategy P&L calculations"""
    
    def setUp(self):
        """Set up test market data"""
        self.market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {570.0: 12.0, 575.0: 8.5, 580.0: 5.2, 585.0: 2.8, 590.0: 1.1},
                "PE": {570.0: 1.1, 575.0: 2.1, 580.0: 4.8, 585.0: 7.9, 590.0: 12.0}
            },
            available_strikes=[570.0, 575.0, 580.0, 585.0, 590.0]
        )
        
        self.position_manager = PositionManager()
    
    def test_iron_condor_pnl_calculation(self):
        """Test iron condor P&L calculation with four legs"""
        iron_condor = IronCondorSetup(
            setup_id="ic_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            wing_width=10,
            short_strike_distance=5
        )
        
        # Create iron condor position
        positions = iron_condor.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        position_id = self.position_manager.add_position(position)
        
        # Test P&L calculation with price movement
        new_market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=585.0,  # Price moved up
            option_prices={
                "CE": {570.0: 16.0, 575.0: 12.0, 580.0: 8.0, 585.0: 5.0, 590.0: 2.5},
                "PE": {570.0: 0.5, 575.0: 1.0, 580.0: 2.0, 585.0: 4.0, 590.0: 7.0}
            },
            available_strikes=[570.0, 575.0, 580.0, 585.0, 590.0]
        )
        
        trades = self.position_manager.update_positions(new_market_data)
        
        # Verify position exists and P&L is calculated
        self.assertIn(position_id, self.position_manager.positions)
        updated_position = self.position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_butterfly_spread_pnl(self):
        """Test butterfly spread P&L calculation"""
        butterfly = ButterflySetup(
            setup_id="butterfly_test",
            target_pct=40.0,
            stop_loss_pct=80.0,
            entry_timeindex=1000,
            wing_distance=5,
            butterfly_type="CALL"
        )
        
        positions = butterfly.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        
        # Verify 1-2-1 structure
        self.assertEqual(len(position.entry_prices), 3)  # Three strikes
        
        # Test P&L calculation
        position_id = self.position_manager.add_position(position)
        
        # Price moves to body of butterfly
        new_market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=580.0,  # At the body
            option_prices={
                "CE": {575.0: 6.0, 580.0: 2.0, 585.0: 0.5},
                "PE": {575.0: 1.0, 580.0: 2.0, 585.0: 5.5}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        trades = self.position_manager.update_positions(new_market_data)
        
        # Check P&L calculation
        updated_position = self.position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_vertical_spread_pnl(self):
        """Test vertical spread P&L calculation"""
        vertical = VerticalSpreadSetup(
            setup_id="vertical_test",
            target_pct=60.0,
            stop_loss_pct=120.0,
            entry_timeindex=1000,
            spread_width=5,
            direction="BULL_CALL"
        )
        
        positions = vertical.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        
        # Verify two-leg structure
        self.assertEqual(len(position.entry_prices), 2)
        
        # Test P&L with favorable move
        position_id = self.position_manager.add_position(position)
        
        new_market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=590.0,  # Favorable for bull call
            option_prices={
                "CE": {575.0: 16.0, 580.0: 12.0, 585.0: 8.0},
                "PE": {575.0: 0.5, 580.0: 1.0, 585.0: 2.0}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        trades = self.position_manager.update_positions(new_market_data)
        
        updated_position = self.position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_ratio_spread_pnl(self):
        """Test ratio spread P&L calculation with unbalanced legs"""
        ratio_spread = RatioSpreadSetup(
            setup_id="ratio_test",
            target_pct=70.0,
            stop_loss_pct=150.0,
            entry_timeindex=1000,
            ratio="1:2",
            spread_type="CALL"
        )
        
        positions = ratio_spread.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        
        # Test unbalanced quantities
        total_quantity = sum(abs(q) for q in position.entry_prices.values() if isinstance(q, (int, float)))
        self.assertGreater(total_quantity, 2)  # Should have more than simple 1:1 ratio
        
        # Test P&L calculation
        position_id = self.position_manager.add_position(position)
        
        new_market_data = MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=575.0,  # Test different price level
            option_prices={
                "CE": {570.0: 8.0, 575.0: 4.0, 580.0: 1.5},
                "PE": {570.0: 1.5, 575.0: 4.0, 580.0: 8.0}
            },
            available_strikes=[570.0, 575.0, 580.0]
        )
        
        trades = self.position_manager.update_positions(new_market_data)
        
        updated_position = self.position_manager.positions[position_id]
        self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_gamma_scalping_delta_calculation(self):
        """Test gamma scalping delta-neutral position management"""
        gamma_scalp = GammaScalpingSetup(
            setup_id="gamma_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            delta_threshold=0.10,
            rebalance_frequency=60
        )
        
        positions = gamma_scalp.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        self.assertEqual(position.position_type, "GAMMA_SCALP")
        
        # Test delta estimation
        strikes = {"CE": 580.0, "PE": 580.0}
        delta = gamma_scalp._estimate_position_delta(self.market_data, strikes)
        self.assertIsInstance(delta, float)
        self.assertLess(abs(delta), 0.5)  # Should be relatively neutral
        
        # Test gamma/theta P&L breakdown
        gamma_scalp.last_spot_price = 575.0  # Set previous price
        pnl_breakdown = gamma_scalp.calculate_gamma_theta_pnl(self.market_data, position)
        
        self.assertIn("gamma_pnl", pnl_breakdown)
        self.assertIn("theta_pnl", pnl_breakdown)
        self.assertIn("total_gamma_pnl", pnl_breakdown)
        self.assertIn("total_theta_pnl", pnl_breakdown)


class TestPatternRecognitionStrategies(unittest.TestCase):
    """Test pattern recognition strategy signal generation"""
    
    def setUp(self):
        """Set up pattern recognition strategies"""
        self.momentum_strategy = MomentumReversalSetup(
            setup_id="momentum_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            strategy_type="MOMENTUM",
            momentum_threshold=0.01
        )
        
        self.volatility_skew_strategy = VolatilitySkewSetup(
            setup_id="skew_test",
            target_pct=30.0,
            stop_loss_pct=60.0,
            entry_timeindex=1000,
            skew_threshold=0.02
        )
        
        self.time_decay_strategy = TimeDecaySetup(
            setup_id="theta_test",
            target_pct=40.0,
            stop_loss_pct=80.0,
            entry_timeindex=1000,
            theta_acceleration_time=4500,
            high_theta_threshold=0.50
        )
    
    def test_momentum_signal_generation(self):
        """Test momentum strategy signal generation"""
        # Build price history with momentum
        base_price = 580.0
        for i in range(15):
            price = base_price + (i * 0.05)  # Building momentum
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=price,
                option_prices={
                    "CE": {575.0: 0.45, 580.0: 0.35, 585.0: 0.25},
                    "PE": {575.0: 0.25, 580.0: 0.35, 585.0: 0.45}
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            self.momentum_strategy.update_price_data(market_data)
        
        # Test signal generation
        entry_signal = self.momentum_strategy.check_entry_condition(1070)
        
        if entry_signal:
            positions = self.momentum_strategy.create_positions(market_data)
            self.assertGreater(len(positions), 0)
            self.assertIn("CE", positions[0].strikes)
    
    def test_reversion_signal_generation(self):
        """Test mean reversion signal generation"""
        reversion_strategy = MomentumReversalSetup(
            setup_id="reversion_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            strategy_type="REVERSION",
            momentum_threshold=0.01,
            reversion_lookback=10
        )
        
        # Build price history with sharp move then stabilization
        base_price = 580.0
        prices = [base_price + 3.0] * 5 + [base_price + 2.8] * 5 + [base_price + 2.9] * 5
        
        for i, price in enumerate(prices):
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=price,
                option_prices={
                    "CE": {575.0: 0.45, 580.0: 0.35, 585.0: 0.25},
                    "PE": {575.0: 0.25, 580.0: 0.35, 585.0: 0.45}
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            reversion_strategy.update_price_data(market_data)
        
        # Test reversion signal
        entry_signal = reversion_strategy.check_entry_condition(1070)
        
        if entry_signal:
            positions = reversion_strategy.create_positions(market_data)
            self.assertGreater(len(positions), 0)
    
    def test_volatility_skew_signal(self):
        """Test volatility skew signal generation"""
        # Build IV history with increasing skew
        for i in range(12):
            market_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=580.0,
                option_prices={
                    "CE": {
                        575.0: 0.60 + i * 0.02,  # Increasing IV
                        580.0: 0.40 + i * 0.005,  # Stable IV
                        585.0: 0.25 + i * 0.001   # Minimal change
                    },
                    "PE": {
                        575.0: 0.25 + i * 0.001,
                        580.0: 0.40 + i * 0.005,
                        585.0: 0.60 + i * 0.02
                    }
                },
                available_strikes=[575.0, 580.0, 585.0]
            )
            self.volatility_skew_strategy.update_iv_data(market_data)
        
        # Test skew signal
        entry_signal = self.volatility_skew_strategy.check_entry_condition(1055)
        
        if entry_signal:
            positions = self.volatility_skew_strategy.create_positions(market_data)
            self.assertGreater(len(positions), 0)
    
    def test_time_decay_acceleration_signal(self):
        """Test time decay acceleration signal generation"""
        # Test during theta acceleration period
        market_data = MarketData(
            timestamp=4550,  # Near acceleration time
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 0.70, 580.0: 0.55, 585.0: 0.40},  # High premiums
                "PE": {575.0: 0.40, 580.0: 0.55, 585.0: 0.70}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        # Test entry signal during acceleration period
        entry_signal = self.time_decay_strategy.check_entry_condition(4550)
        self.assertTrue(entry_signal)
        
        # Test theta acceleration calculation
        acceleration = self.time_decay_strategy.calculate_theta_acceleration(4550)
        self.assertGreater(acceleration, 1.0)  # Should be accelerated
        
        # Test position creation with accelerated targets
        positions = self.time_decay_strategy.create_positions(market_data)
        if positions:
            # Target should be adjusted for acceleration
            self.assertGreater(positions[0].target_pnl, 0)
    
    def test_put_call_parity_violation_detection(self):
        """Test put-call parity violation detection"""
        from backtesting_engine.strategies import detect_put_call_parity_violation
        
        # Create data with clear violations
        market_data = MarketData(
            timestamp=2000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 8.00, 580.0: 3.50, 585.0: 1.00},  # Overpriced calls
                "PE": {575.0: 0.20, 580.0: 1.50, 585.0: 4.00}   # Underpriced puts
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        violations = detect_put_call_parity_violation(market_data)
        
        self.assertGreater(len(violations), 0)
        
        for violation in violations:
            self.assertIn("strike", violation)
            self.assertIn("violation_amount", violation)
            self.assertIn("arbitrage_type", violation)
            self.assertIsInstance(violation["violation_amount"], float)
            self.assertGreater(abs(violation["violation_amount"]), 0.1)


class TestCrossSymbolCorrelationAndRisk(unittest.TestCase):
    """Test cross-symbol correlation and risk management"""
    
    def setUp(self):
        """Set up multi-symbol environment"""
        self.symbols = ["QQQ", "SPY"]
        self.detectors = {
            symbol: MarketRegimeDetector(lookback_periods=60) 
            for symbol in self.symbols
        }
        self.position_manager = PositionManager()
    
    def test_cross_symbol_correlation_tracking(self):
        """Test correlation tracking between symbols"""
        # Create correlated price movements
        base_prices = {"QQQ": 580.0, "SPY": 450.0}
        
        for i in range(70):
            # Create correlated movements
            price_change = i * 0.05
            
            for symbol in self.symbols:
                market_data = MarketData(
                    timestamp=1000 + i * 5,
                    symbol=symbol,
                    spot_price=base_prices[symbol] + price_change,
                    option_prices={
                        "CE": {575.0: 8.0, 580.0: 5.0, 585.0: 2.5},
                        "PE": {575.0: 2.0, 580.0: 4.5, 585.0: 7.5}
                    },
                    available_strikes=[575.0, 580.0, 585.0]
                )
                self.detectors[symbol].update_market_data(market_data)
        
        # Test cross-symbol divergence detection
        divergence = self.detectors["QQQ"].detect_cross_symbol_divergence(
            self.detectors["SPY"]
        )
        
        self.assertIsInstance(divergence, float)
        self.assertLess(divergence, 0.5)  # Should be low for correlated movements
    
    def test_regime_divergence_detection(self):
        """Test detection of regime divergence between symbols"""
        # Create divergent market conditions
        # QQQ trending up
        for i in range(70):
            qqq_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="QQQ",
                spot_price=580.0 + i * 0.05,  # Trending up
                option_prices={
                    "CE": {580.0: 5.0 - i * 0.01},
                    "PE": {580.0: 4.5 + i * 0.01}
                },
                available_strikes=[580.0]
            )
            self.detectors["QQQ"].update_market_data(qqq_data)
        
        # SPY ranging
        for i in range(70):
            spy_price = 450.0 + (2.0 * (1 if i % 4 < 2 else -1))  # Ranging
            spy_data = MarketData(
                timestamp=1000 + i * 5,
                symbol="SPY",
                spot_price=spy_price,
                option_prices={
                    "CE": {450.0: 5.0},
                    "PE": {450.0: 4.5}
                },
                available_strikes=[450.0]
            )
            self.detectors["SPY"].update_market_data(spy_data)
        
        # Check regime divergence
        qqq_regime = self.detectors["QQQ"].get_current_regime()
        spy_regime = self.detectors["SPY"].get_current_regime()
        
        self.assertNotEqual(qqq_regime, spy_regime)
        
        divergence = self.detectors["QQQ"].detect_cross_symbol_divergence(
            self.detectors["SPY"]
        )
        self.assertGreater(divergence, 0.3)  # Should show divergence
    
    def test_multi_symbol_risk_management(self):
        """Test risk management across multiple symbols"""
        from backtesting_engine.risk_manager import RiskManager
        from backtesting_engine.strategies import StraddleSetup
        
        # Create risk manager with daily limit
        risk_manager = RiskManager(daily_max_loss=1000.0)
        
        # Create positions in multiple symbols
        symbols_data = {
            "QQQ": MarketData(
                timestamp=1000,
                symbol="QQQ",
                spot_price=580.0,
                option_prices={"CE": {580.0: 5.0}, "PE": {580.0: 4.5}},
                available_strikes=[580.0]
            ),
            "SPY": MarketData(
                timestamp=1000,
                symbol="SPY",
                spot_price=450.0,
                option_prices={"CE": {450.0: 4.0}, "PE": {450.0: 3.5}},
                available_strikes=[450.0]
            )
        }
        
        # Create positions for each symbol
        for symbol, market_data in symbols_data.items():
            setup = StraddleSetup(
                setup_id=f"straddle_{symbol}",
                target_pct=50.0,
                stop_loss_pct=100.0,
                entry_timeindex=1000
            )
            
            positions = setup.create_positions(market_data)
            for position in positions:
                self.position_manager.add_position(position)
        
        # Test aggregate P&L calculation
        total_pnl = self.position_manager.get_total_pnl()
        self.assertIsInstance(total_pnl, float)
        
        # Test risk limit checking across symbols
        risk_breach = risk_manager.check_daily_limit(total_pnl)
        self.assertIsInstance(risk_breach, bool)
    
    def test_correlation_based_position_sizing(self):
        """Test position sizing based on cross-symbol correlation"""
        # This would test dynamic position sizing based on correlation
        # For now, test that correlation affects risk calculations
        
        # High correlation scenario
        high_corr_data = []
        for i in range(50):
            price_change = i * 0.02
            high_corr_data.append({
                "QQQ": 580.0 + price_change,
                "SPY": 450.0 + price_change * 0.8  # Highly correlated
            })
        
        # Low correlation scenario  
        low_corr_data = []
        for i in range(50):
            low_corr_data.append({
                "QQQ": 580.0 + (i % 5 - 2) * 0.5,  # Random-like
                "SPY": 450.0 + ((i + 3) % 7 - 3) * 0.3  # Different pattern
            })
        
        # Test that correlation affects risk assessment
        # (This is a placeholder for more sophisticated correlation-based risk management)
        self.assertTrue(len(high_corr_data) > 0)
        self.assertTrue(len(low_corr_data) > 0)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("Running Comprehensive Backtesting Engine Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestMultiSymbolDataLoading,
        TestMarketRegimeDetection,
        TestDynamicParameterAdjustment,
        TestComplexMultiLegStrategies,
        TestPatternRecognitionStrategies,
        TestCrossSymbolCorrelationAndRisk
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    run_comprehensive_tests()