#!/usr/bin/env python3
"""
Test script for GammaScalpingSetup strategy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.strategies import GammaScalpingSetup
from backtesting_engine.models import MarketData, Position

def test_gamma_scalping_setup():
    """Test basic functionality of GammaScalpingSetup"""
    
    # Create a gamma scalping setup
    setup = GammaScalpingSetup(
        setup_id="gamma_scalp_test",
        target_pct=50.0,
        stop_loss_pct=100.0,
        entry_timeindex=1000,
        delta_threshold=0.10,
        rebalance_frequency=60,
        max_rebalances=5
    )
    
    print(f"Created GammaScalpingSetup: {setup.setup_id}")
    print(f"Delta threshold: {setup.delta_threshold}")
    print(f"Max rebalances: {setup.max_rebalances}")
    
    # Test entry condition
    assert setup.check_entry_condition(1000) == True
    assert setup.check_entry_condition(999) == False
    print("✓ Entry condition check works")
    
    # Create mock market data
    market_data = MarketData(
        timestamp=1000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 8.5, 580.0: 5.2, 585.0: 2.8},
            "PE": {575.0: 2.1, 580.0: 4.8, 585.0: 7.9}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Test strike selection
    strikes = setup.select_strikes(market_data.spot_price, market_data.option_prices)
    print(f"Selected strikes: {strikes}")
    assert "CE" in strikes and "PE" in strikes
    assert strikes["CE"] == 580.0  # Should select ATM
    assert strikes["PE"] == 580.0  # Should select ATM
    print("✓ Strike selection works")
    
    # Test position creation
    positions = setup.create_positions(market_data)
    assert len(positions) == 1
    position = positions[0]
    assert position.setup_id == "gamma_scalp_test"
    assert position.position_type == "GAMMA_SCALP"
    assert len(position.entry_prices) == 2  # CE and PE
    print("✓ Position creation works")
    
    # Test delta estimation
    delta = setup._estimate_position_delta(market_data, strikes)
    print(f"Estimated delta: {delta}")
    assert isinstance(delta, float)
    print("✓ Delta estimation works")
    
    # Test gamma/theta P&L calculation
    setup.last_spot_price = 575.0  # Set previous spot price
    pnl_breakdown = setup.calculate_gamma_theta_pnl(market_data, position)
    print(f"P&L breakdown: {pnl_breakdown}")
    assert "gamma_pnl" in pnl_breakdown
    assert "theta_pnl" in pnl_breakdown
    assert "total_gamma_pnl" in pnl_breakdown
    assert "total_theta_pnl" in pnl_breakdown
    print("✓ Gamma/Theta P&L calculation works")
    
    # Test rebalancing condition
    rebalance_needed = setup.check_rebalancing_condition(1100, market_data, positions)
    print(f"Rebalancing needed: {rebalance_needed}")
    print("✓ Rebalancing condition check works")
    
    # Test priority closure check
    should_close = setup.should_prioritize_closure(4400)  # Close to market close
    assert should_close == True
    should_close = setup.should_prioritize_closure(2000)  # Early in day
    assert should_close == False
    print("✓ Priority closure check works")
    
    # Test daily state reset
    setup.rebalance_count = 3
    setup.gamma_pnl = 25.0
    setup.reset_daily_state()
    assert setup.rebalance_count == 0
    assert setup.gamma_pnl == 0.0
    print("✓ Daily state reset works")
    
    print("\n🎉 All GammaScalpingSetup tests passed!")

if __name__ == "__main__":
    test_gamma_scalping_setup()