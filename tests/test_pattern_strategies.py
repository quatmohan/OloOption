#!/usr/bin/env python3
"""
Test script for the new pattern recognition strategies
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

def test_momentum_reversal_setup():
    """Test MomentumReversalSetup strategy"""
    print("Testing MomentumReversalSetup...")
    
    # Create momentum strategy
    momentum_setup = MomentumReversalSetup(
        setup_id="momentum_test",
        target_pct=50.0,
        stop_loss_pct=100.0,
        entry_timeindex=1000,
        strategy_type="MOMENTUM",
        momentum_threshold=0.01
    )
    
    # Create test market data
    market_data = MarketData(
        timestamp=1000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 0.45, 580.0: 0.35, 585.0: 0.25},
            "PE": {575.0: 0.25, 580.0: 0.35, 585.0: 0.45}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Test entry condition (should be False initially - no price history)
    entry_condition = momentum_setup.check_entry_condition(1000)
    print(f"Initial entry condition: {entry_condition}")
    
    # Update price data to build history
    for i in range(15):
        test_data = MarketData(
            timestamp=1000 + i * 5,
            symbol="QQQ",
            spot_price=580.0 + i * 0.1,  # Gradual price increase
            option_prices=market_data.option_prices,
            available_strikes=market_data.available_strikes
        )
        momentum_setup.update_price_data(test_data)
    
    # Test entry condition after building momentum
    entry_condition = momentum_setup.check_entry_condition(1070)
    print(f"Entry condition after momentum build: {entry_condition}")
    
    # Test position creation
    positions = momentum_setup.create_positions(market_data)
    print(f"Created {len(positions)} positions")
    if positions:
        print(f"Position strikes: {positions[0].strikes}")
        print(f"Position entry prices: {positions[0].entry_prices}")
    
    print("MomentumReversalSetup test completed.\n")

def test_volatility_skew_setup():
    """Test VolatilitySkewSetup strategy"""
    print("Testing VolatilitySkewSetup...")
    
    # Create volatility skew strategy
    skew_setup = VolatilitySkewSetup(
        setup_id="skew_test",
        target_pct=30.0,
        stop_loss_pct=60.0,
        entry_timeindex=1000,
        skew_threshold=0.03
    )
    
    # Create test market data with varying option prices to simulate IV skew
    market_data = MarketData(
        timestamp=1000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 0.60, 580.0: 0.40, 585.0: 0.25},  # Higher IV for ITM
            "PE": {575.0: 0.25, 580.0: 0.40, 585.0: 0.60}   # Higher IV for ITM
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Build IV history by updating with varying prices
    for i in range(10):
        test_data = MarketData(
            timestamp=1000 + i * 5,
            symbol="QQQ",
            spot_price=580.0,
            option_prices={
                "CE": {575.0: 0.60 + i * 0.01, 580.0: 0.40, 585.0: 0.25 - i * 0.005},
                "PE": {575.0: 0.25 - i * 0.005, 580.0: 0.40, 585.0: 0.60 + i * 0.01}
            },
            available_strikes=market_data.available_strikes
        )
        skew_setup.update_iv_data(test_data)
    
    # Test entry condition
    entry_condition = skew_setup.check_entry_condition(1050)
    print(f"Entry condition: {entry_condition}")
    
    # Test position creation
    positions = skew_setup.create_positions(market_data)
    print(f"Created {len(positions)} positions")
    if positions:
        print(f"Position strikes: {positions[0].strikes}")
        print(f"Position entry prices: {positions[0].entry_prices}")
    
    print("VolatilitySkewSetup test completed.\n")

def test_time_decay_setup():
    """Test TimeDecaySetup strategy"""
    print("Testing TimeDecaySetup...")
    
    # Create time decay strategy
    time_decay_setup = TimeDecaySetup(
        setup_id="theta_test",
        target_pct=40.0,
        stop_loss_pct=80.0,
        entry_timeindex=1000,
        theta_acceleration_time=4500,
        high_theta_threshold=0.50
    )
    
    # Create test market data with high premium options
    market_data = MarketData(
        timestamp=4550,  # Near theta acceleration time
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 0.70, 580.0: 0.55, 585.0: 0.40},  # High premiums
            "PE": {575.0: 0.40, 580.0: 0.55, 585.0: 0.70}
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Test entry condition during theta acceleration period
    entry_condition = time_decay_setup.check_entry_condition(4550)
    print(f"Entry condition during theta acceleration: {entry_condition}")
    
    # Test theta acceleration calculation
    acceleration = time_decay_setup.calculate_theta_acceleration(4550)
    print(f"Theta acceleration factor: {acceleration:.2f}")
    
    # Test position creation
    positions = time_decay_setup.create_positions(market_data)
    print(f"Created {len(positions)} positions")
    if positions:
        print(f"Position strikes: {positions[0].strikes}")
        print(f"Position target P&L (accelerated): {positions[0].target_pnl}")
    
    print("TimeDecaySetup test completed.\n")

def test_put_call_parity_detection():
    """Test put-call parity violation detection"""
    print("Testing put-call parity violation detection...")
    
    # Create market data with potential parity violation
    market_data = MarketData(
        timestamp=2000,
        symbol="QQQ",
        spot_price=580.0,
        option_prices={
            "CE": {575.0: 6.50, 580.0: 2.50, 585.0: 0.50},  # Call prices
            "PE": {575.0: 0.30, 580.0: 1.80, 585.0: 4.80}   # Put prices - potential violation
        },
        available_strikes=[575.0, 580.0, 585.0]
    )
    
    # Detect violations
    violations = detect_put_call_parity_violation(market_data)
    print(f"Found {len(violations)} put-call parity violations")
    
    for violation in violations:
        print(f"Strike {violation['strike']}: Violation amount ${violation['violation_amount']:.2f}")
        print(f"  Arbitrage type: {violation['arbitrage_type']}")
        print(f"  Call: ${violation['call_price']:.2f}, Put: ${violation['put_price']:.2f}")
    
    print("Put-call parity detection test completed.\n")

def main():
    """Run all tests"""
    print("Testing Pattern Recognition Strategies")
    print("=" * 50)
    
    test_momentum_reversal_setup()
    test_volatility_skew_setup()
    test_time_decay_setup()
    test_put_call_parity_detection()
    
    print("All tests completed successfully!")

if __name__ == "__main__":
    main()