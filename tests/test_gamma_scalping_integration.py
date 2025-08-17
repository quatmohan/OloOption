#!/usr/bin/env python3
"""
Integration test for GammaScalpingSetup with PositionManager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.strategies import GammaScalpingSetup
from backtesting_engine.position_manager import PositionManager
from backtesting_engine.models import MarketData, Position

def test_gamma_scalping_integration():
    """Test gamma scalping integration with PositionManager"""
    
    print("🧪 Testing Gamma Scalping Integration")
    print("=" * 50)
    
    # Create gamma scalping setup
    setup = GammaScalpingSetup(
        setup_id="gamma_test",
        target_pct=50.0,
        stop_loss_pct=100.0,
        entry_timeindex=1000,
        delta_threshold=0.12,
        rebalance_frequency=60,
        max_rebalances=3
    )
    
    # Create position manager
    position_manager = PositionManager()
    
    # Create initial market data
    market_data_1 = MarketData(
        timestamp=1000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 8.5, 580.0: 5.2, 585.0: 2.8},
            "PE": {575.0: 2.1, 580.0: 4.8, 585.0: 7.9}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    print("1. Testing initial position creation...")
    
    # Test entry condition and position creation
    assert setup.check_entry_condition(1000) == True
    positions = setup.create_positions(market_data_1)
    assert len(positions) == 1
    
    position = positions[0]
    position_id = position_manager.add_position(position)
    print(f"   ✓ Created position {position_id} with type {position.position_type}")
    print(f"   ✓ Initial delta: {setup.current_delta:.3f}")
    
    # Test position update
    print("\n2. Testing position updates...")
    trades = position_manager.update_positions(market_data_1)
    assert len(trades) == 0  # No trades should be closed yet
    print("   ✓ Position updated, no closures")
    
    # Test gamma scalping specific updates
    gamma_trades = position_manager.update_gamma_scalping_positions(market_data_1, [setup])
    assert len(gamma_trades) == 0  # No rebalancing needed yet
    print("   ✓ Gamma scalping update completed")
    
    # Create market data with significant spot move to trigger rebalancing
    print("\n3. Testing rebalancing logic...")
    market_data_2 = MarketData(
        timestamp=1120,  # 2 minutes later
        symbol="QQQ",
        spot_price=590.0,  # Significant move up
        option_prices={
            "CE": {575.0: 18.5, 580.0: 15.2, 585.0: 12.8},
            "PE": {575.0: 0.5, 580.0: 2.1, 585.0: 4.2}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Update gamma scalping positions (should trigger rebalancing)
    gamma_trades = position_manager.update_gamma_scalping_positions(market_data_2, [setup])
    print(f"   ✓ Rebalancing check completed, trades: {len(gamma_trades)}")
    
    # Test gamma/theta P&L calculation
    print("\n4. Testing gamma/theta P&L calculation...")
    current_positions = list(position_manager.positions.values())
    if current_positions:
        pos = current_positions[0]
        pnl_breakdown = setup.calculate_gamma_theta_pnl(market_data_2, pos)
        print(f"   ✓ Gamma P&L: ${pnl_breakdown['gamma_pnl']:.2f}")
        print(f"   ✓ Theta P&L: ${pnl_breakdown['theta_pnl']:.2f}")
        print(f"   ✓ Total Gamma P&L: ${pnl_breakdown['total_gamma_pnl']:.2f}")
        print(f"   ✓ Total Theta P&L: ${pnl_breakdown['total_theta_pnl']:.2f}")
    
    # Test position manager gamma metrics
    print("\n5. Testing position manager gamma metrics...")
    metrics = position_manager.get_gamma_scalping_metrics()
    print(f"   ✓ Total Gamma P&L: ${metrics['total_gamma_pnl']:.2f}")
    print(f"   ✓ Total Theta P&L: ${metrics['total_theta_pnl']:.2f}")
    print(f"   ✓ Total Delta: {metrics['total_delta']:.3f}")
    print(f"   ✓ Gamma Positions: {metrics['gamma_positions']}")
    
    # Test priority closure near market close
    print("\n6. Testing priority closure logic...")
    market_data_close = MarketData(
        timestamp=4400,  # Near market close
        symbol="QQQ",
        spot_price=585.0,
        option_prices={
            "CE": {575.0: 15.0, 580.0: 10.0, 585.0: 6.0},
            "PE": {575.0: 1.0, 580.0: 3.0, 585.0: 6.0}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    should_prioritize = setup.should_prioritize_closure(4400)
    print(f"   ✓ Should prioritize closure: {should_prioritize}")
    
    # Force close all positions
    print("\n7. Testing position closure...")
    final_trades = position_manager.close_all_positions(market_data_close, "TEST_CLOSE")
    print(f"   ✓ Closed {len(final_trades)} positions")
    
    for trade in final_trades:
        print(f"   ✓ Trade P&L: ${trade.pnl:.2f}")
        print(f"   ✓ Gamma P&L: ${trade.gamma_pnl:.2f}")
        print(f"   ✓ Theta P&L: ${trade.theta_pnl:.2f}")
        print(f"   ✓ Final Delta: {trade.final_delta:.3f}")
        print(f"   ✓ Rebalances: {trade.rebalance_count}")
    
    # Test daily state reset
    print("\n8. Testing daily state reset...")
    setup.gamma_pnl = 100.0
    setup.rebalance_count = 2
    setup.reset_daily_state()
    assert setup.gamma_pnl == 0.0
    assert setup.rebalance_count == 0
    print("   ✓ Daily state reset completed")
    
    print("\n🎉 All gamma scalping integration tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    test_gamma_scalping_integration()