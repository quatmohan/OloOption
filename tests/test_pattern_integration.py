#!/usr/bin/env python3
"""
Integration test for pattern recognition strategies with the backtesting engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.strategies import (
    MomentumReversalSetup, 
    VolatilitySkewSetup, 
    TimeDecaySetup,
    detect_put_call_parity_violation
)
from backtesting_engine.models import MarketData

def test_momentum_strategy_integration():
    """Test momentum strategy with realistic market data updates"""
    print("Testing MomentumReversalSetup integration...")
    
    # Create momentum strategy
    momentum_setup = MomentumReversalSetup(
        setup_id="momentum_integration",
        target_pct=50.0,
        stop_loss_pct=100.0,
        entry_timeindex=1000,
        strategy_type="MOMENTUM",
        momentum_threshold=0.01
    )
    
    # Simulate price movement with increasing momentum
    base_spot = 580.0
    for i in range(15):
        # Create accelerating upward price movement
        price_change = i * 0.05  # Accelerating change
        current_spot = base_spot + price_change
        
        market_data = MarketData(
            timestamp=1000 + i * 5,
            symbol="QQQ",
            spot_price=current_spot,
            option_prices={
                "CE": {575.0: 0.45, 580.0: 0.35, 585.0: 0.25},
                "PE": {575.0: 0.25, 580.0: 0.35, 585.0: 0.45}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        # Update price data
        momentum_setup.update_price_data(market_data)
        
        # Check entry condition after sufficient history
        if i >= 10:  # After building sufficient history
            entry_condition = momentum_setup.check_entry_condition(market_data.timestamp)
            if entry_condition:
                print(f"  Entry signal detected at timestamp {market_data.timestamp}")
                print(f"  Recent velocity: {momentum_setup.velocity_history[-1]:.4f}")
                
                # Test position creation
                positions = momentum_setup.create_positions(market_data)
                print(f"  Created {len(positions)} positions")
                if positions:
                    print(f"  Position strikes: {positions[0].strikes}")
                break
    
    print("MomentumReversalSetup integration test completed.\n")

def test_volatility_skew_integration():
    """Test volatility skew strategy with IV data updates"""
    print("Testing VolatilitySkewSetup integration...")
    
    # Create volatility skew strategy
    skew_setup = VolatilitySkewSetup(
        setup_id="skew_integration",
        target_pct=30.0,
        stop_loss_pct=60.0,
        entry_timeindex=1000,
        skew_threshold=0.02
    )
    
    # Build IV history with varying option prices
    for i in range(12):
        # Create IV skew by varying option prices differently across strikes
        market_data = MarketData(
            timestamp=1000 + i * 5,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {
                    575.0: 0.60 + i * 0.02,  # ITM call - increasing IV
                    580.0: 0.40 + i * 0.005,  # ATM call - stable IV
                    585.0: 0.25 + i * 0.001   # OTM call - minimal IV change
                },
                "PE": {
                    575.0: 0.25 + i * 0.001,  # OTM put - minimal IV change
                    580.0: 0.40 + i * 0.005,  # ATM put - stable IV
                    585.0: 0.60 + i * 0.02    # ITM put - increasing IV
                }
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        # Update IV data
        skew_setup.update_iv_data(market_data)
        
        # Check entry condition after building IV history
        if i >= 8:
            entry_condition = skew_setup.check_entry_condition(market_data.timestamp)
            if entry_condition:
                print(f"  Entry signal detected at timestamp {market_data.timestamp}")
                
                # Test position creation
                positions = skew_setup.create_positions(market_data)
                print(f"  Created {len(positions)} positions")
                if positions:
                    print(f"  Position strikes: {positions[0].strikes}")
                    print(f"  Position entry prices: {positions[0].entry_prices}")
                break
    
    print("VolatilitySkewSetup integration test completed.\n")

def test_time_decay_integration():
    """Test time decay strategy during theta acceleration period"""
    print("Testing TimeDecaySetup integration...")
    
    # Create time decay strategy
    time_decay_setup = TimeDecaySetup(
        setup_id="theta_integration",
        target_pct=40.0,
        stop_loss_pct=80.0,
        entry_timeindex=1000,
        theta_acceleration_time=4500,
        high_theta_threshold=0.45
    )
    
    # Test during different time periods
    test_times = [4000, 4500, 4600, 4650]  # Before, at, during, and near expiration
    
    for timestamp in test_times:
        market_data = MarketData(
            timestamp=timestamp,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 0.70, 580.0: 0.50, 585.0: 0.35},  # High premiums for theta
                "PE": {575.0: 0.35, 580.0: 0.50, 585.0: 0.70}
            },
            available_strikes=[575.0, 580.0, 585.0]
        )
        
        entry_condition = time_decay_setup.check_entry_condition(timestamp)
        theta_acceleration = time_decay_setup.calculate_theta_acceleration(timestamp)
        
        print(f"  Time {timestamp}: Entry={entry_condition}, Theta acceleration={theta_acceleration:.2f}")
        
        if entry_condition:
            positions = time_decay_setup.create_positions(market_data)
            if positions:
                print(f"    Created position with accelerated target: {positions[0].target_pnl:.2f}")
    
    print("TimeDecaySetup integration test completed.\n")

def test_put_call_parity_comprehensive():
    """Test put-call parity detection with various scenarios"""
    print("Testing comprehensive put-call parity detection...")
    
    # Test scenario 1: Normal parity (no violations)
    normal_data = MarketData(
        timestamp=2000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 6.00, 580.0: 2.00, 585.0: 0.50},
            "PE": {575.0: 1.00, 580.0: 2.00, 585.0: 5.50}  # Proper parity
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    violations = detect_put_call_parity_violation(normal_data)
    print(f"  Normal scenario: {len(violations)} violations found")
    
    # Test scenario 2: Clear violations
    violation_data = MarketData(
        timestamp=2000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 8.00, 580.0: 3.50, 585.0: 1.00},  # Calls overpriced
            "PE": {575.0: 0.20, 580.0: 1.50, 585.0: 4.00}   # Puts underpriced
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    violations = detect_put_call_parity_violation(violation_data)
    print(f"  Violation scenario: {len(violations)} violations found")
    for violation in violations[:2]:  # Show top 2
        print(f"    Strike {violation['strike']}: ${violation['violation_amount']:.2f} violation")
        print(f"    Action: {violation['arbitrage_type']}")
    
    print("Put-call parity comprehensive test completed.\n")

def main():
    """Run all integration tests"""
    print("Pattern Recognition Strategies Integration Tests")
    print("=" * 60)
    
    test_momentum_strategy_integration()
    test_volatility_skew_integration()
    test_time_decay_integration()
    test_put_call_parity_comprehensive()
    
    print("All integration tests completed successfully!")

if __name__ == "__main__":
    main()