#!/usr/bin/env python3
"""
Advanced Pattern Recognition Strategy Examples
Demonstrates sophisticated pattern detection and market condition analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import (
    MomentumReversalSetup, VolatilitySkewSetup, TimeDecaySetup,
    GammaScalpingSetup, StraddleSetup, HedgedStraddleSetup
)
from backtesting_engine.reporting import BacktestReporter
from backtesting_engine.models import MarketData


def example_momentum_pattern_strategies():
    """
    Advanced momentum and mean reversion pattern detection strategies
    """
    print("📈 Momentum Pattern Recognition Strategies")
    print("=" * 60)
    
    momentum_strategies = [
        # Pure momentum following
        MomentumReversalSetup(
            setup_id="pure_momentum_follow",
            target_pct=0.40,
            stop_loss_pct=0.90,
            entry_timeindex=1000,
            strategy_type="MOMENTUM",
            momentum_threshold=0.008,  # Strong momentum threshold
            lookback_periods=10,  # Short lookback for responsiveness
            velocity_smoothing=3  # Light smoothing
        ),
        
        # Mean reversion after momentum exhaustion
        MomentumReversalSetup(
            setup_id="momentum_exhaustion_reversion",
            target_pct=0.35,
            stop_loss_pct=0.85,
            entry_timeindex=1500,
            strategy_type="REVERSION",
            momentum_threshold=0.012,  # Higher threshold for exhaustion
            reversion_lookback=20,  # Longer lookback for reversion
            max_velocity_threshold=0.015  # Maximum velocity before reversion
        ),
        
        # Adaptive momentum/reversion switching
        MomentumReversalSetup(
            setup_id="adaptive_momentum_reversion",
            target_pct=0.38,
            stop_loss_pct=0.95,
            entry_timeindex=2000,
            strategy_type="ADAPTIVE",  # Switches based on market conditions
            momentum_threshold=0.006,
            adaptive_threshold_multiplier=1.5,  # Adjusts thresholds dynamically
            regime_sensitivity=0.8  # How quickly to adapt to regime changes
        ),
        
        # Velocity acceleration detection
        MomentumReversalSetup(
            setup_id="velocity_acceleration",
            target_pct=0.42,
            stop_loss_pct=1.00,
            entry_timeindex=2500,
            strategy_type="ACCELERATION",  # Detects acceleration patterns
            momentum_threshold=0.005,
            acceleration_threshold=0.003,  # Rate of velocity change
            min_acceleration_periods=5  # Minimum periods of acceleration
        )
    ]
    
    return momentum_strategies


def example_volatility_pattern_strategies():
    """
    Advanced volatility skew and relative IV pattern strategies
    """
    print("⚡ Volatility Pattern Recognition Strategies")
    print("=" * 60)
    
    volatility_strategies = [
        # Classic volatility skew exploitation
        VolatilitySkewSetup(
            setup_id="classic_vol_skew",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1000,
            skew_threshold=0.025,  # Strong skew threshold
            min_iv_difference=0.03,
            skew_persistence_periods=8  # How long skew must persist
        ),
        
        # Put-call skew divergence
        VolatilitySkewSetup(
            setup_id="put_call_skew_divergence",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1500,
            skew_threshold=0.020,
            put_call_skew_focus=True,  # Focus on put-call skew specifically
            min_put_call_iv_diff=0.025,
            skew_mean_reversion_threshold=0.015  # When to expect reversion
        ),
        
        # Strike-to-strike IV compression/expansion
        VolatilitySkewSetup(
            setup_id="iv_compression_expansion",
            target_pct=0.32,
            stop_loss_pct=0.85,
            entry_timeindex=2000,
            skew_threshold=0.018,
            iv_compression_detection=True,  # Detect IV compression patterns
            compression_threshold=0.012,
            expansion_threshold=0.022
        ),
        
        # Time-based volatility patterns
        VolatilitySkewSetup(
            setup_id="time_based_vol_patterns",
            target_pct=0.28,
            stop_loss_pct=0.75,
            entry_timeindex=2500,
            skew_threshold=0.015,
            time_of_day_adjustment=True,  # Adjust for time-of-day effects
            morning_vol_multiplier=1.2,  # Higher vol in morning
            afternoon_vol_multiplier=0.9,  # Lower vol in afternoon
            eod_vol_spike_detection=True  # Detect end-of-day vol spikes
        )
    ]
    
    return volatility_strategies


def example_time_decay_pattern_strategies():
    """
    Advanced time decay and theta acceleration pattern strategies
    """
    print("⏰ Time Decay Pattern Recognition Strategies")
    print("=" * 60)
    
    time_decay_strategies = [
        # Classic theta acceleration
        TimeDecaySetup(
            setup_id="classic_theta_acceleration",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            theta_acceleration_time=4400,  # When theta accelerates
            high_theta_threshold=0.35,
            theta_acceleration_multiplier=2.0  # How much theta accelerates
        ),
        
        # Intraday theta patterns
        TimeDecaySetup(
            setup_id="intraday_theta_patterns",
            target_pct=0.25,
            stop_loss_pct=0.70,
            entry_timeindex=1500,
            theta_acceleration_time=4200,
            intraday_theta_tracking=True,  # Track theta throughout day
            lunch_theta_slowdown=True,  # Account for lunch slowdown
            eod_theta_spike=True,  # End-of-day theta acceleration
            theta_pattern_lookback=15  # Periods to analyze theta patterns
        ),
        
        # Theta-gamma interaction
        TimeDecaySetup(
            setup_id="theta_gamma_interaction",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=2000,
            theta_acceleration_time=4300,
            gamma_theta_correlation=True,  # Consider gamma-theta relationship
            high_gamma_theta_boost=1.3,  # Theta boost in high gamma
            low_gamma_theta_reduction=0.8,  # Theta reduction in low gamma
            gamma_threshold=0.05  # Gamma level threshold
        ),
        
        # Weekend/expiration effects
        TimeDecaySetup(
            setup_id="expiration_effects",
            target_pct=0.28,
            stop_loss_pct=0.75,
            entry_timeindex=2500,
            theta_acceleration_time=4500,
            expiration_day_effects=True,  # Special handling for expiration day
            weekend_theta_adjustment=True,  # Account for weekend theta
            expiration_hour_multiplier=3.0,  # Massive acceleration in final hour
            assignment_risk_management=True  # Manage assignment risk
        )
    ]
    
    return time_decay_strategies


def example_cross_pattern_strategies():
    """
    Strategies that combine multiple pattern recognition techniques
    """
    print("🔗 Cross-Pattern Recognition Strategies")
    print("=" * 60)
    
    cross_pattern_strategies = [
        # Momentum + Volatility combination
        MomentumReversalSetup(
            setup_id="momentum_vol_combo",
            target_pct=0.40,
            stop_loss_pct=1.00,
            entry_timeindex=1000,
            strategy_type="MOMENTUM",
            momentum_threshold=0.007,
            volatility_confirmation=True,  # Require vol confirmation
            min_vol_for_momentum=0.15,  # Minimum volatility for momentum trades
            vol_momentum_correlation=0.6  # Required correlation
        ),
        
        # Volatility + Time decay combination
        VolatilitySkewSetup(
            setup_id="vol_theta_combo",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1500,
            skew_threshold=0.020,
            theta_acceleration_boost=True,  # Boost when theta accelerates
            theta_vol_interaction=True,  # Consider theta-vol interaction
            late_day_vol_skew_focus=True  # Focus on late-day skew
        ),
        
        # Triple pattern confirmation
        GammaScalpingSetup(
            setup_id="triple_pattern_gamma",
            target_pct=0.30,
            stop_loss_pct=0.85,
            entry_timeindex=2000,
            delta_threshold=0.15,
            momentum_confirmation=True,  # Require momentum confirmation
            volatility_confirmation=True,  # Require volatility confirmation
            time_decay_awareness=True,  # Consider time decay effects
            pattern_confluence_required=2  # Need 2 of 3 patterns to confirm
        ),
        
        # Market microstructure patterns
        StraddleSetup(
            setup_id="microstructure_patterns",
            target_pct=0.32,
            stop_loss_pct=0.88,
            entry_timeindex=2500,
            scalping_price=0.35,
            bid_ask_spread_analysis=True,  # Analyze bid-ask spreads
            volume_pattern_detection=True,  # Detect volume patterns
            price_level_clustering=True,  # Detect price clustering
            market_maker_behavior_analysis=True  # Analyze MM behavior
        )
    ]
    
    return cross_pattern_strategies


def run_pattern_recognition_backtests():
    """
    Run comprehensive pattern recognition strategy backtests
    """
    print("\n🔍 Running Pattern Recognition Strategy Backtests")
    print("=" * 70)
    
    # Get all pattern strategy categories
    pattern_categories = {
        "MOMENTUM": example_momentum_pattern_strategies(),
        "VOLATILITY": example_volatility_pattern_strategies(),
        "TIME_DECAY": example_time_decay_pattern_strategies(),
        "CROSS_PATTERN": example_cross_pattern_strategies()
    }
    
    category_results = {}
    
    # Test each pattern category
    for category_name, strategies in pattern_categories.items():
        print(f"\n🧪 Testing {category_name} pattern strategies...")
        
        # Create engine with pattern recognition focus
        engine = BacktestEngine(
            data_path="5SecData",
            setups=strategies,
            daily_max_loss=600.0,
            enable_dynamic_management=True,  # Allow pattern adaptation
            enable_multi_symbol=False  # Focus on single symbol for pattern analysis
        )
        
        # Run backtest
        results = engine.run_backtest(
            symbols="QQQ",  # Use QQQ for pattern testing
            start_date="2025-08-13",
            end_date="2025-08-15"
        )
        
        category_results[category_name] = results
        
        print(f"   {category_name} Results: ${results.total_pnl:.2f} P&L, "
              f"{results.total_trades} trades, {results.win_rate:.1%} win rate")
        
        # Show best pattern strategies
        if results.setup_performance:
            best_strategies = sorted(
                results.setup_performance.items(),
                key=lambda x: x[1].total_pnl,
                reverse=True
            )[:2]
            
            print(f"   Top 2 pattern strategies:")
            for setup_id, perf in best_strategies:
                print(f"     {setup_id}: ${perf.total_pnl:.2f} ({perf.total_trades} trades)")
    
    # Compare pattern category performance
    print(f"\n📊 Pattern Recognition Performance Comparison:")
    print("-" * 70)
    print(f"{'Category':<15} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Trade':<10}")
    print("-" * 70)
    
    for category_name, results in category_results.items():
        avg_trade = results.total_pnl / max(results.total_trades, 1)
        print(f"{category_name:<15} ${results.total_pnl:<9.2f} {results.total_trades:<8} "
              f"{results.win_rate:<9.1%} ${avg_trade:<9.2f}")
    
    return category_results


def example_pattern_discovery_analysis():
    """
    Example showing how to discover new patterns in the data
    """
    print("\n🔍 Pattern Discovery Analysis Example")
    print("=" * 70)
    
    # Create pattern discovery focused strategies
    discovery_strategies = [
        # Broad pattern detection
        MomentumReversalSetup(
            setup_id="pattern_discovery_momentum",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            strategy_type="DISCOVERY",  # Discovery mode
            momentum_threshold=0.005,
            pattern_logging=True,  # Log all patterns detected
            discovery_sensitivity=0.7  # High sensitivity for discovery
        ),
        
        # Volatility pattern discovery
        VolatilitySkewSetup(
            setup_id="pattern_discovery_vol",
            target_pct=0.25,
            stop_loss_pct=0.70,
            entry_timeindex=1500,
            skew_threshold=0.015,
            pattern_discovery_mode=True,  # Discovery mode
            log_all_skew_events=True,  # Log all skew events
            discovery_threshold_reduction=0.5  # Lower thresholds for discovery
        ),
        
        # Time pattern discovery
        TimeDecaySetup(
            setup_id="pattern_discovery_time",
            target_pct=0.28,
            stop_loss_pct=0.75,
            entry_timeindex=2000,
            theta_acceleration_time=4000,  # Earlier detection
            pattern_discovery_mode=True,
            log_time_patterns=True,  # Log time-based patterns
            intraday_pattern_analysis=True  # Analyze intraday patterns
        )
    ]
    
    print("🔍 Running pattern discovery analysis...")
    
    # Run with enhanced logging and analysis
    engine = BacktestEngine(
        data_path="5SecData",
        setups=discovery_strategies,
        daily_max_loss=500.0,
        enable_dynamic_management=True,
        pattern_discovery_mode=True  # Enable pattern discovery
    )
    
    results = engine.run_backtest(
        symbols="QQQ",
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    print(f"\n📈 Pattern Discovery Results:")
    print(f"   Total P&L: ${results.total_pnl:.2f}")
    print(f"   Total Trades: {results.total_trades}")
    print(f"   Patterns Discovered: {len(results.discovered_patterns) if hasattr(results, 'discovered_patterns') else 'N/A'}")
    
    # Generate pattern discovery report
    reporter = BacktestReporter(results)
    
    print(f"\n📊 Generating pattern discovery reports...")
    report_summary = reporter.generate_full_report(
        symbols=["QQQ"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    return results


def demonstrate_pattern_validation():
    """
    Demonstrate how to validate discovered patterns
    """
    print("\n✅ Pattern Validation Example")
    print("=" * 70)
    
    # Create validation-focused strategies
    validation_strategies = [
        # Validate momentum patterns
        MomentumReversalSetup(
            setup_id="validate_momentum_pattern",
            target_pct=0.35,
            stop_loss_pct=0.85,
            entry_timeindex=1000,
            strategy_type="VALIDATION",  # Validation mode
            momentum_threshold=0.007,
            pattern_validation=True,  # Enable pattern validation
            validation_confidence_threshold=0.75,  # Required confidence
            historical_pattern_matching=True  # Match against historical patterns
        ),
        
        # Validate volatility patterns
        VolatilitySkewSetup(
            setup_id="validate_vol_pattern",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1500,
            skew_threshold=0.020,
            pattern_validation=True,
            validation_lookback=50,  # Periods to validate against
            pattern_consistency_threshold=0.8  # Required consistency
        )
    ]
    
    print("✅ Running pattern validation analysis...")
    
    engine = BacktestEngine(
        data_path="5SecData",
        setups=validation_strategies,
        daily_max_loss=400.0,
        enable_dynamic_management=True,
        pattern_validation_mode=True  # Enable validation mode
    )
    
    results = engine.run_backtest(
        symbols="QQQ",
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    print(f"\n📊 Pattern Validation Results:")
    print(f"   Validated Patterns: {results.validated_patterns if hasattr(results, 'validated_patterns') else 'N/A'}")
    print(f"   Validation Accuracy: {results.validation_accuracy if hasattr(results, 'validation_accuracy') else 'N/A'}")
    print(f"   P&L from Validated Patterns: ${results.total_pnl:.2f}")
    
    return results


if __name__ == "__main__":
    print("🎯 Advanced Pattern Recognition Strategy Examples")
    print("=" * 70)
    
    # Show individual pattern categories
    example_momentum_pattern_strategies()
    print()
    example_volatility_pattern_strategies()
    print()
    example_time_decay_pattern_strategies()
    print()
    example_cross_pattern_strategies()
    
    # Run comprehensive pattern backtests
    pattern_results = run_pattern_recognition_backtests()
    
    # Demonstrate pattern discovery
    discovery_results = example_pattern_discovery_analysis()
    
    # Demonstrate pattern validation
    validation_results = demonstrate_pattern_validation()
    
    print("\n✅ Advanced Pattern Recognition Examples Completed!")
    print("=" * 70)
    
    # Final analysis
    if pattern_results:
        best_category = max(pattern_results.items(), key=lambda x: x[1].total_pnl)
        print(f"\n🏆 Best Performing Pattern Category:")
        print(f"   {best_category[0]}: ${best_category[1].total_pnl:.2f} P&L")
    
    print(f"\n🔍 Pattern Discovery Performance:")
    print(f"   ${discovery_results.total_pnl:.2f} P&L from pattern discovery")
    
    print(f"\n✅ Pattern Validation Performance:")
    print(f"   ${validation_results.total_pnl:.2f} P&L from validated patterns")