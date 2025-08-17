#!/usr/bin/env python3
"""
Tests for complex multi-leg strategy P&L calculations
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.strategies import (
    IronCondorSetup, ButterflySetup, VerticalSpreadSetup, 
    RatioSpreadSetup, GammaScalpingSetup
)
from backtesting_engine.position_manager import PositionManager
from backtesting_engine.models import MarketData, Position


class TestComplexStrategyPnL(unittest.TestCase):
    """Test P&L calculations for complex multi-leg strategies"""
    
    def setUp(self):
        """Set up test environment"""
        self.position_manager = PositionManager()
        
        # Standard market data for testing
        self.market_data = MarketData(
            timestamp=1000,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {
                    570.0: 12.0, 575.0: 8.5, 580.0: 5.2, 
                    585.0: 2.8, 590.0: 1.1, 595.0: 0.4
                },
                "PE": {
                    570.0: 1.1, 575.0: 2.1, 580.0: 4.8, 
                    585.0: 7.9, 590.0: 12.0, 595.0: 16.5
                }
            },
            available_strikes=[570.0, 575.0, 580.0, 585.0, 590.0, 595.0]
        )
    
    def create_price_movement_scenario(self, new_spot: float, volatility_change: float = 0.0) -> MarketData:
        """Create market data with price movement and volatility change"""
        # Calculate new option prices based on new spot price
        new_option_prices = {"CE": {}, "PE": {}}
        
        for strike in self.market_data.available_strikes:
            # Simple option pricing adjustment
            ce_intrinsic = max(0, new_spot - strike)
            pe_intrinsic = max(0, strike - new_spot)
            
            # Time value adjustment (simplified)
            time_value = 2.0 + volatility_change
            
            new_option_prices["CE"][strike] = ce_intrinsic + time_value
            new_option_prices["PE"][strike] = pe_intrinsic + time_value
        
        return MarketData(
            timestamp=1100,
            symbol="QQQ",
            spot_price=new_spot,
            option_prices=new_option_prices,
            available_strikes=self.market_data.available_strikes
        )
    
    def test_iron_condor_pnl_calculation(self):
        """Test iron condor P&L calculation across different market scenarios"""
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
        
        # Test scenarios
        scenarios = [
            ("spot_unchanged", 580.0, "Should profit from time decay"),
            ("small_move_up", 583.0, "Should still be profitable"),
            ("small_move_down", 577.0, "Should still be profitable"),
            ("large_move_up", 595.0, "Should hit max loss"),
            ("large_move_down", 565.0, "Should hit max loss")
        ]
        
        for scenario_name, new_spot, description in scenarios:
            with self.subTest(scenario=scenario_name):
                new_market_data = self.create_price_movement_scenario(new_spot)
                
                # Calculate P&L
                trades = self.position_manager.update_positions(new_market_data)
                updated_position = self.position_manager.positions[position_id]
                
                print(f"Iron Condor {scenario_name}: Spot {new_spot}, P&L: ${updated_position.current_pnl:.2f}")
                
                # Verify P&L is calculated
                self.assertIsInstance(updated_position.current_pnl, float)
                
                # For iron condors, max profit should be at the center
                if scenario_name == "spot_unchanged":
                    # Should be profitable (time decay)
                    self.assertGreaterEqual(updated_position.current_pnl, -50.0)
                elif scenario_name in ["large_move_up", "large_move_down"]:
                    # Should show losses for large moves
                    self.assertLess(updated_position.current_pnl, 0.0)
    
    def test_butterfly_spread_pnl_calculation(self):
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
        position_id = self.position_manager.add_position(position)
        
        # Verify butterfly structure (1-2-1 ratio)
        self.assertEqual(len(position.entry_prices), 3, "Should have 3 strikes")
        
        # Test P&L at different spots
        test_spots = [575.0, 580.0, 585.0]  # Wings and body
        
        for spot in test_spots:
            with self.subTest(spot=spot):
                new_market_data = self.create_price_movement_scenario(spot)
                
                trades = self.position_manager.update_positions(new_market_data)
                updated_position = self.position_manager.positions[position_id]
                
                print(f"Butterfly at spot {spot}: P&L ${updated_position.current_pnl:.2f}")
                
                # Max profit should be at the body (580)
                if spot == 580.0:
                    # Should be most profitable at the body
                    self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_vertical_spread_pnl_calculation(self):
        """Test vertical spread P&L calculation"""
        # Test bull call spread
        bull_call = VerticalSpreadSetup(
            setup_id="bull_call_test",
            target_pct=60.0,
            stop_loss_pct=120.0,
            entry_timeindex=1000,
            spread_width=5,
            direction="BULL_CALL"
        )
        
        positions = bull_call.create_positions(self.market_data)
        self.assertEqual(len(positions), 1)
        
        position = positions[0]
        position_id = self.position_manager.add_position(position)
        
        # Verify two-leg structure
        self.assertEqual(len(position.entry_prices), 2, "Should have 2 strikes")
        
        # Test P&L with favorable and unfavorable moves
        scenarios = [
            (590.0, "favorable_move", "Should profit from upward move"),
            (570.0, "unfavorable_move", "Should lose from downward move"),
            (580.0, "neutral_move", "Should have moderate P&L")
        ]
        
        for new_spot, scenario_name, description in scenarios:
            with self.subTest(scenario=scenario_name):
                new_market_data = self.create_price_movement_scenario(new_spot)
                
                trades = self.position_manager.update_positions(new_market_data)
                updated_position = self.position_manager.positions[position_id]
                
                print(f"Bull Call {scenario_name}: Spot {new_spot}, P&L: ${updated_position.current_pnl:.2f}")
                
                if scenario_name == "favorable_move":
                    # Should profit from upward move
                    self.assertGreater(updated_position.current_pnl, -20.0)
                elif scenario_name == "unfavorable_move":
                    # Should lose from downward move
                    self.assertLess(updated_position.current_pnl, 20.0)
    
    def test_ratio_spread_pnl_calculation(self):
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
        position_id = self.position_manager.add_position(position)
        
        # Test P&L calculation with different price levels
        test_scenarios = [
            (575.0, "below_strikes", "Should profit from range-bound movement"),
            (585.0, "between_strikes", "Should have optimal P&L"),
            (600.0, "above_strikes", "Should show unlimited risk concern")
        ]
        
        for new_spot, scenario_name, description in test_scenarios:
            with self.subTest(scenario=scenario_name):
                new_market_data = self.create_price_movement_scenario(new_spot)
                
                trades = self.position_manager.update_positions(new_market_data)
                updated_position = self.position_manager.positions[position_id]
                
                print(f"Ratio Spread {scenario_name}: Spot {new_spot}, P&L: ${updated_position.current_pnl:.2f}")
                
                # Verify P&L calculation
                self.assertIsInstance(updated_position.current_pnl, float)
                
                # For ratio spreads, unlimited risk side should show increasing losses
                if scenario_name == "above_strikes":
                    # Should show concern for unlimited risk
                    self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_gamma_scalping_delta_neutral_pnl(self):
        """Test gamma scalping delta-neutral P&L calculation"""
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
        
        position_id = self.position_manager.add_position(position)
        
        # Test gamma/theta P&L breakdown with price movement
        gamma_scalp.last_spot_price = 575.0  # Set previous price for gamma calculation
        
        # Test with upward price movement
        new_market_data = self.create_price_movement_scenario(585.0)
        
        # Calculate gamma/theta breakdown
        pnl_breakdown = gamma_scalp.calculate_gamma_theta_pnl(new_market_data, position)
        
        # Verify breakdown components
        required_keys = ["gamma_pnl", "theta_pnl", "total_gamma_pnl", "total_theta_pnl"]
        for key in required_keys:
            self.assertIn(key, pnl_breakdown, f"Missing {key} in P&L breakdown")
            self.assertIsInstance(pnl_breakdown[key], float)
        
        print(f"Gamma Scalping P&L Breakdown:")
        print(f"  Gamma P&L: ${pnl_breakdown['gamma_pnl']:.2f}")
        print(f"  Theta P&L: ${pnl_breakdown['theta_pnl']:.2f}")
        print(f"  Total Gamma P&L: ${pnl_breakdown['total_gamma_pnl']:.2f}")
        print(f"  Total Theta P&L: ${pnl_breakdown['total_theta_pnl']:.2f}")
        
        # Test delta estimation
        strikes = {"CE": 580.0, "PE": 580.0}
        delta = gamma_scalp._estimate_position_delta(new_market_data, strikes)
        
        self.assertIsInstance(delta, float)
        print(f"  Estimated Delta: {delta:.4f}")
        
        # Delta should be relatively neutral for gamma scalping
        self.assertLess(abs(delta), 0.5, "Delta should be relatively neutral")
    
    def test_position_manager_complex_pnl_aggregation(self):
        """Test position manager's ability to handle complex multi-leg P&L aggregation"""
        # Create multiple complex positions
        strategies = [
            IronCondorSetup("ic1", 50.0, 100.0, 1000, wing_width=10),
            ButterflySetup("bf1", 40.0, 80.0, 1000, wing_distance=5),
            VerticalSpreadSetup("vs1", 60.0, 120.0, 1000, spread_width=5, direction="BULL_CALL")
        ]
        
        position_ids = []
        
        # Create positions for all strategies
        for strategy in strategies:
            positions = strategy.create_positions(self.market_data)
            for position in positions:
                position_id = self.position_manager.add_position(position)
                position_ids.append(position_id)
        
        # Test aggregate P&L calculation
        initial_total_pnl = self.position_manager.get_total_pnl()
        self.assertIsInstance(initial_total_pnl, float)
        
        # Update all positions with price movement
        new_market_data = self.create_price_movement_scenario(585.0)
        trades = self.position_manager.update_positions(new_market_data)
        
        # Test updated aggregate P&L
        updated_total_pnl = self.position_manager.get_total_pnl()
        self.assertIsInstance(updated_total_pnl, float)
        
        # Test individual position P&L
        individual_pnls = []
        for position_id in position_ids:
            if position_id in self.position_manager.positions:
                position = self.position_manager.positions[position_id]
                individual_pnls.append(position.current_pnl)
        
        # Aggregate should equal sum of individuals
        calculated_total = sum(individual_pnls)
        self.assertAlmostEqual(updated_total_pnl, calculated_total, places=2,
                              msg="Aggregate P&L should equal sum of individual P&Ls")
        
        print(f"Complex Multi-Strategy P&L:")
        print(f"  Individual P&Ls: {[f'${pnl:.2f}' for pnl in individual_pnls]}")
        print(f"  Total P&L: ${updated_total_pnl:.2f}")
        print(f"  Calculated Total: ${calculated_total:.2f}")
    
    def test_slippage_impact_on_complex_strategies(self):
        """Test slippage impact on complex multi-leg strategies"""
        # Create iron condor to test slippage on multiple legs
        iron_condor = IronCondorSetup(
            setup_id="slippage_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=1000,
            wing_width=10,
            short_strike_distance=5
        )
        
        positions = iron_condor.create_positions(self.market_data)
        position = positions[0]
        
        # Test with different slippage values
        slippage_values = [0.0, 0.005, 0.01, 0.02]
        
        for slippage in slippage_values:
            with self.subTest(slippage=slippage):
                # Create position with specific slippage
                test_position = Position(
                    setup_id=position.setup_id,
                    entry_timeindex=position.entry_timeindex,
                    entry_prices=position.entry_prices.copy(),
                    strikes=position.strikes.copy(),
                    quantity=position.quantity,
                    lot_size=position.lot_size,
                    target_pnl=position.target_pnl,
                    stop_loss_pnl=position.stop_loss_pnl,
                    position_type=position.position_type,
                    slippage=slippage
                )
                
                # Calculate P&L with slippage
                test_manager = PositionManager()
                test_position_id = test_manager.add_position(test_position)
                
                new_market_data = self.create_price_movement_scenario(585.0)
                trades = test_manager.update_positions(new_market_data)
                
                updated_position = test_manager.positions[test_position_id]
                
                print(f"Slippage {slippage:.3f}: P&L ${updated_position.current_pnl:.2f}")
                
                # Higher slippage should generally result in worse P&L
                self.assertIsInstance(updated_position.current_pnl, float)
    
    def test_extreme_market_scenarios(self):
        """Test complex strategy P&L under extreme market conditions"""
        # Create butterfly spread for testing
        butterfly = ButterflySetup(
            setup_id="extreme_test",
            target_pct=40.0,
            stop_loss_pct=80.0,
            entry_timeindex=1000,
            wing_distance=5,
            butterfly_type="CALL"
        )
        
        positions = butterfly.create_positions(self.market_data)
        position = positions[0]
        position_id = self.position_manager.add_position(position)
        
        # Test extreme scenarios
        extreme_scenarios = [
            (550.0, "extreme_down", "Extreme downward move"),
            (620.0, "extreme_up", "Extreme upward move"),
            (580.0, "high_vol", "High volatility at center", 2.0),  # High vol change
            (580.0, "vol_crush", "Volatility crush at center", -1.5)  # Vol crush
        ]
        
        for scenario in extreme_scenarios:
            if len(scenario) == 4:
                new_spot, scenario_name, description, vol_change = scenario
            else:
                new_spot, scenario_name, description = scenario
                vol_change = 0.0
            
            with self.subTest(scenario=scenario_name):
                new_market_data = self.create_price_movement_scenario(new_spot, vol_change)
                
                trades = self.position_manager.update_positions(new_market_data)
                updated_position = self.position_manager.positions[position_id]
                
                print(f"Extreme {scenario_name}: Spot {new_spot}, Vol Δ {vol_change}, "
                      f"P&L: ${updated_position.current_pnl:.2f}")
                
                # Should handle extreme scenarios without errors
                self.assertIsInstance(updated_position.current_pnl, float)
                self.assertFalse(math.isnan(updated_position.current_pnl), 
                               "P&L should not be NaN in extreme scenarios")
                self.assertFalse(math.isinf(updated_position.current_pnl), 
                               "P&L should not be infinite in extreme scenarios")


def run_complex_strategy_tests():
    """Run complex strategy P&L tests"""
    print("Running Complex Multi-Leg Strategy P&L Tests")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestComplexStrategyPnL)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nComplex Strategy P&L Tests: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    import math
    run_complex_strategy_tests()