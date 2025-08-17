#!/usr/bin/env python3
"""
Regime-Specific Strategy Examples
Demonstrates dynamic strategy adaptation based on market regime detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import (
    StraddleSetup, HedgedStraddleSetup, CEScalpingSetup, PEScalpingSetup,
    IronCondorSetup, ButterflySetup, VerticalSpreadSetup, RatioSpreadSetup,
    MomentumReversalSetup, VolatilitySkewSetup, TimeDecaySetup, GammaScalpingSetup
)
from backtesting_engine.reporting import BacktestReporter


def example_trending_market_strategies():
    """
    Strategies optimized for trending market conditions
    """
    print("📈 Trending Market Strategy Configuration")
    print("=" * 60)
    
    # Strategies that perform well in trending markets
    trending_strategies = [
        # Directional scalping strategies
        CEScalpingSetup(
            setup_id="trending_ce_scalping",
            target_pct=0.35,  # Higher targets in trending markets
            stop_loss_pct=0.80,  # Tighter stops to ride trends
            entry_timeindex=1000,
            max_reentries=3,  # More re-entries in trending markets
            reentry_gap=240,  # Shorter gaps between entries
            scalping_price=0.30  # Lower premium threshold for more entries
        ),
        
        PEScalpingSetup(
            setup_id="trending_pe_scalping",
            target_pct=0.35,
            stop_loss_pct=0.80,
            entry_timeindex=1500,
            max_reentries=3,
            reentry_gap=240,
            scalping_price=0.30
        ),
        
        # Momentum-based strategies
        MomentumReversalSetup(
            setup_id="trending_momentum",
            target_pct=0.45,
            stop_loss_pct=1.00,
            entry_timeindex=1200,
            strategy_type="MOMENTUM",  # Follow momentum in trending markets
            momentum_threshold=0.006,  # Lower threshold to catch trends early
            reversion_lookback=8  # Shorter lookback for responsiveness
        ),
        
        # Vertical spreads for directional plays
        VerticalSpreadSetup(
            setup_id="trending_vertical_spread",
            target_pct=0.40,
            stop_loss_pct=1.20,
            entry_timeindex=1800,
            spread_width=5,
            direction="BULL_CALL"  # Assume uptrend for example
        ),
        
        # Gamma scalping to capture movement
        GammaScalpingSetup(
            setup_id="trending_gamma_scalping",
            target_pct=0.25,
            stop_loss_pct=0.70,
            entry_timeindex=2000,
            delta_threshold=0.12,  # Tighter delta management in trends
            rebalance_frequency=45  # More frequent rebalancing
        )
    ]
    
    return trending_strategies


def example_ranging_market_strategies():
    """
    Strategies optimized for ranging/sideways market conditions
    """
    print("📊 Ranging Market Strategy Configuration")
    print("=" * 60)
    
    # Strategies that perform well in ranging markets
    ranging_strategies = [
        # Premium selling strategies
        StraddleSetup(
            setup_id="ranging_straddle",
            target_pct=0.50,  # Higher targets in ranging markets
            stop_loss_pct=1.80,  # Wider stops for range-bound action
            entry_timeindex=1000,
            strike_selection="premium",
            scalping_price=0.45  # Higher premium threshold
        ),
        
        HedgedStraddleSetup(
            setup_id="ranging_hedged_straddle",
            target_pct=0.40,
            stop_loss_pct=1.50,
            entry_timeindex=1500,
            scalping_price=0.40,
            hedge_strikes_away=6  # Wider hedges for ranging markets
        ),
        
        # Iron condors for range-bound profits
        IronCondorSetup(
            setup_id="ranging_iron_condor",
            target_pct=0.35,
            stop_loss_pct=1.40,
            entry_timeindex=1200,
            wing_width=12,  # Wider wings for ranging markets
            short_strike_distance=6  # Further from spot
        ),
        
        # Butterflies for low volatility
        ButterflySetup(
            setup_id="ranging_butterfly",
            target_pct=0.45,
            stop_loss_pct=1.20,
            entry_timeindex=1800,
            wing_distance=6,
            butterfly_type="CALL"
        ),
        
        # Time decay strategies
        TimeDecaySetup(
            setup_id="ranging_time_decay",
            target_pct=0.35,
            stop_loss_pct=1.00,
            entry_timeindex=2200,
            theta_acceleration_time=4400,
            high_theta_threshold=0.40
        )
    ]
    
    return ranging_strategies


def example_high_volatility_strategies():
    """
    Strategies optimized for high volatility conditions
    """
    print("⚡ High Volatility Strategy Configuration")
    print("=" * 60)
    
    # Strategies that perform well in high volatility
    high_vol_strategies = [
        # Volatility skew exploitation
        VolatilitySkewSetup(
            setup_id="high_vol_skew",
            target_pct=0.40,
            stop_loss_pct=1.00,
            entry_timeindex=1000,
            skew_threshold=0.025  # Higher threshold for high vol
        ),
        
        # Ratio spreads for volatility capture
        RatioSpreadSetup(
            setup_id="high_vol_ratio_spread",
            target_pct=0.50,
            stop_loss_pct=1.50,
            entry_timeindex=1500,
            ratio="1:2",
            spread_type="CALL"
        ),
        
        # Momentum reversal in high vol
        MomentumReversalSetup(
            setup_id="high_vol_reversion",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1200,
            strategy_type="REVERSION",  # Mean reversion in high vol
            momentum_threshold=0.010,  # Higher threshold for high vol
            reversion_lookback=15
        ),
        
        # Aggressive gamma scalping
        GammaScalpingSetup(
            setup_id="high_vol_gamma",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1800,
            delta_threshold=0.20,  # Wider delta bands for high vol
            rebalance_frequency=30  # More frequent rebalancing
        ),
        
        # Hedged positions for protection
        HedgedStraddleSetup(
            setup_id="high_vol_hedged",
            target_pct=0.25,  # Lower target due to hedge cost
            stop_loss_pct=1.00,
            entry_timeindex=2000,
            scalping_price=0.50,  # Higher premium in high vol
            hedge_strikes_away=4  # Closer hedges for protection
        )
    ]
    
    return high_vol_strategies


def example_low_volatility_strategies():
    """
    Strategies optimized for low volatility conditions
    """
    print("🔇 Low Volatility Strategy Configuration")
    print("=" * 60)
    
    # Strategies that perform well in low volatility
    low_vol_strategies = [
        # Premium selling with tight management
        StraddleSetup(
            setup_id="low_vol_straddle",
            target_pct=0.30,  # Lower targets in low vol
            stop_loss_pct=1.20,  # Tighter stops
            entry_timeindex=1000,
            scalping_price=0.25  # Lower premium threshold
        ),
        
        # Iron condors with tight wings
        IronCondorSetup(
            setup_id="low_vol_iron_condor",
            target_pct=0.25,
            stop_loss_pct=1.00,
            entry_timeindex=1500,
            wing_width=8,  # Tighter wings
            short_strike_distance=4
        ),
        
        # Butterflies for precise targeting
        ButterflySetup(
            setup_id="low_vol_butterfly",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1200,
            wing_distance=4,  # Tighter wings
            butterfly_type="PUT"
        ),
        
        # Time decay acceleration
        TimeDecaySetup(
            setup_id="low_vol_theta",
            target_pct=0.25,
            stop_loss_pct=0.75,
            entry_timeindex=1800,
            theta_acceleration_time=4300,
            high_theta_threshold=0.30
        ),
        
        # Conservative scalping
        CEScalpingSetup(
            setup_id="low_vol_ce_scalping",
            target_pct=0.20,
            stop_loss_pct=0.60,
            entry_timeindex=2200,
            max_reentries=1,  # Fewer re-entries in low vol
            reentry_gap=600,  # Longer gaps
            scalping_price=0.25
        )
    ]
    
    return low_vol_strategies


def run_regime_specific_backtests():
    """
    Run backtests for each regime-specific strategy configuration
    """
    print("\n🔄 Running Regime-Specific Strategy Backtests")
    print("=" * 70)
    
    # Get strategy configurations for each regime
    regime_strategies = {
        "TRENDING": example_trending_market_strategies(),
        "RANGING": example_ranging_market_strategies(),
        "HIGH_VOL": example_high_volatility_strategies(),
        "LOW_VOL": example_low_volatility_strategies()
    }
    
    regime_results = {}
    
    # Test each regime configuration
    for regime_name, strategies in regime_strategies.items():
        print(f"\n🧪 Testing {regime_name} strategies...")
        
        # Create engine with dynamic management to adapt to actual market conditions
        engine = BacktestEngine(
            data_path="5SecData",
            setups=strategies,
            daily_max_loss=800.0,
            enable_dynamic_management=True,  # Let it adapt within the regime focus
            enable_multi_symbol=False  # Focus on single symbol for regime analysis
        )
        
        # Run backtest
        results = engine.run_backtest(
            symbols="QQQ",  # Use QQQ for regime testing
            start_date="2025-08-13",
            end_date="2025-08-15"
        )
        
        regime_results[regime_name] = results
        
        print(f"   {regime_name} Results: ${results.total_pnl:.2f} P&L, "
              f"{results.total_trades} trades, {results.win_rate:.1%} win rate")
        
        # Show top performing strategies in this regime
        if results.setup_performance:
            top_strategies = sorted(
                results.setup_performance.items(),
                key=lambda x: x[1].total_pnl,
                reverse=True
            )[:3]
            
            print(f"   Top 3 strategies:")
            for setup_id, perf in top_strategies:
                print(f"     {setup_id}: ${perf.total_pnl:.2f}")
    
    # Compare regime performance
    print(f"\n📊 Regime Strategy Performance Comparison:")
    print("-" * 70)
    print(f"{'Regime':<12} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Max DD':<10}")
    print("-" * 70)
    
    for regime_name, results in regime_results.items():
        print(f"{regime_name:<12} ${results.total_pnl:<9.2f} {results.total_trades:<8} "
              f"{results.win_rate:<9.1%} ${results.max_drawdown:<9.2f}")
    
    return regime_results


def example_dynamic_regime_adaptation():
    """
    Example showing how strategies adapt dynamically to changing market regimes
    """
    print("\n🔄 Dynamic Regime Adaptation Example")
    print("=" * 70)
    
    # Create a mixed strategy portfolio that can adapt to different regimes
    adaptive_strategies = [
        # Base strategies that work across regimes
        StraddleSetup(
            setup_id="adaptive_straddle",
            target_pct=0.40,
            stop_loss_pct=1.20,
            entry_timeindex=1000,
            scalping_price=0.35
        ),
        
        # Momentum strategy that adapts direction
        MomentumReversalSetup(
            setup_id="adaptive_momentum",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1500,
            strategy_type="ADAPTIVE",  # Will switch between momentum and reversion
            momentum_threshold=0.007
        ),
        
        # Volatility strategy that adjusts to skew changes
        VolatilitySkewSetup(
            setup_id="adaptive_vol_skew",
            target_pct=0.30,
            stop_loss_pct=0.85,
            entry_timeindex=2000,
            skew_threshold=0.020
        ),
        
        # Gamma scalping with adaptive delta management
        GammaScalpingSetup(
            setup_id="adaptive_gamma",
            target_pct=0.25,
            stop_loss_pct=0.70,
            entry_timeindex=1200,
            delta_threshold=0.15,  # Will be adjusted based on regime
            rebalance_frequency=60
        )
    ]
    
    # Run with full dynamic management enabled
    print("🤖 Running backtest with full dynamic regime adaptation...")
    
    engine = BacktestEngine(
        data_path="5SecData",
        setups=adaptive_strategies,
        daily_max_loss=1000.0,
        enable_dynamic_management=True,  # Full dynamic adaptation
        enable_multi_symbol=True,
        cross_symbol_risk_limit=1500.0
    )
    
    # Run across multiple symbols to see regime differences
    results = engine.run_multi_symbol_backtest(
        symbols=["QQQ", "SPY"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    # Analyze dynamic adaptation performance
    print(f"\n📈 Dynamic Adaptation Results:")
    print(f"   Total P&L: ${results.total_pnl:.2f}")
    print(f"   Total Trades: {results.total_trades}")
    print(f"   Win Rate: {results.win_rate:.1%}")
    print(f"   Max Drawdown: ${results.max_drawdown:.2f}")
    
    if results.dynamic_adjustment_performance:
        dap = results.dynamic_adjustment_performance
        print(f"\n🔧 Dynamic Adjustment Analysis:")
        print(f"   Total Parameter Adjustments: {dap.total_adjustments}")
        print(f"   Improvement over Static: ${dap.static_vs_dynamic_comparison:.2f}")
        print(f"   Regime Detection Accuracy: {dap.regime_accuracy:.1%}")
        
        if dap.adjustment_performance:
            print(f"   Adjustment Impact by Type:")
            for adj_type, impact in dap.adjustment_performance.items():
                print(f"     {adj_type}: ${impact:.2f} average impact")
    
    # Show regime-specific performance
    if results.regime_performance:
        print(f"\n🌡️  Performance by Market Regime:")
        for regime, regime_perf in results.regime_performance.items():
            print(f"   {regime}: ${regime_perf.total_pnl:.2f} P&L, "
                  f"{regime_perf.total_trades} trades, "
                  f"{regime_perf.win_rate:.1%} win rate")
    
    # Generate comprehensive regime analysis report
    reporter = BacktestReporter(results)
    
    print(f"\n📊 Generating dynamic regime adaptation reports...")
    report_summary = reporter.generate_full_report(
        symbols=["QQQ", "SPY"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    return results


if __name__ == "__main__":
    print("🎯 Regime-Specific Strategy Examples")
    print("=" * 70)
    
    # Show individual regime strategy configurations
    example_trending_market_strategies()
    print()
    example_ranging_market_strategies()
    print()
    example_high_volatility_strategies()
    print()
    example_low_volatility_strategies()
    
    # Run comparative backtests
    regime_results = run_regime_specific_backtests()
    
    # Demonstrate dynamic adaptation
    adaptive_results = example_dynamic_regime_adaptation()
    
    print("\n✅ Regime-Specific Strategy Examples Completed!")
    print("=" * 70)
    
    # Final comparison
    print(f"\n🏆 Best Performing Regime Configuration:")
    if regime_results:
        best_regime = max(regime_results.items(), key=lambda x: x[1].total_pnl)
        print(f"   {best_regime[0]}: ${best_regime[1].total_pnl:.2f} P&L")
    
    print(f"\n🤖 Dynamic Adaptation Performance:")
    print(f"   ${adaptive_results.total_pnl:.2f} P&L with automatic regime adaptation")