#!/usr/bin/env python3
"""
Advanced Multi-Symbol Backtesting Examples
Demonstrates comprehensive multi-symbol strategies across QQQ, SPY, QQQ 1DTE, and SPY 1DTE
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


def example_comprehensive_multi_symbol_backtest():
    """
    Comprehensive example showing all supported symbols and advanced strategies
    """
    print("🚀 Advanced Multi-Symbol Backtesting Example")
    print("=" * 70)
    
    # Create diverse strategy portfolio optimized for different market conditions
    strategies = [
        # Traditional strategies - work across all symbols
        StraddleSetup(
            setup_id="multi_straddle_premium",
            target_pct=0.50,  # 50% profit target
            stop_loss_pct=2.0,  # $2.00 stop loss
            entry_timeindex=1000,
            strike_selection="premium",
            scalping_price=0.40
        ),
        
        HedgedStraddleSetup(
            setup_id="multi_hedged_straddle",
            target_pct=0.35,  # Lower target due to hedge cost
            stop_loss_pct=1.50,  # Lower stop due to hedge protection
            entry_timeindex=1500,
            strike_selection="premium",
            scalping_price=0.35,
            hedge_strikes_away=5
        ),
        
        # Scalping strategies - good for trending markets
        CEScalpingSetup(
            setup_id="multi_ce_scalping",
            target_pct=0.25,
            stop_loss_pct=0.75,
            entry_timeindex=2000,
            max_reentries=2,
            reentry_gap=300,
            scalping_price=0.30
        ),
        
        PEScalpingSetup(
            setup_id="multi_pe_scalping",
            target_pct=0.25,
            stop_loss_pct=0.75,
            entry_timeindex=2500,
            max_reentries=2,
            reentry_gap=300,
            scalping_price=0.30
        ),
        
        # Advanced multi-leg strategies
        IronCondorSetup(
            setup_id="multi_iron_condor",
            target_pct=0.30,
            stop_loss_pct=1.20,
            entry_timeindex=1200,
            wing_width=10,
            short_strike_distance=5
        ),
        
        ButterflySetup(
            setup_id="multi_butterfly",
            target_pct=0.40,
            stop_loss_pct=1.00,
            entry_timeindex=1800,
            wing_distance=5,
            butterfly_type="CALL"
        ),
        
        # Pattern recognition strategies
        MomentumReversalSetup(
            setup_id="multi_momentum_reversal",
            target_pct=0.35,
            stop_loss_pct=0.85,
            entry_timeindex=1000,
            strategy_type="MOMENTUM",
            momentum_threshold=0.005
        ),
        
        VolatilitySkewSetup(
            setup_id="multi_vol_skew",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            skew_threshold=0.02
        ),
        
        # Intraday gamma scalping
        GammaScalpingSetup(
            setup_id="multi_gamma_scalping",
            target_pct=0.20,
            stop_loss_pct=0.60,
            entry_timeindex=1000,
            delta_threshold=0.15,
            rebalance_frequency=60  # Every 5 minutes
        )
    ]
    
    print(f"Created {len(strategies)} advanced trading strategies")
    
    # Configure multi-symbol engine with dynamic management
    engine = BacktestEngine(
        data_path="5SecData",
        setups=strategies,
        daily_max_loss=1000.0,
        enable_dynamic_management=True,
        enable_multi_symbol=True,
        cross_symbol_risk_limit=2000.0
    )
    
    # Define all supported symbols
    all_symbols = ["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"]
    
    print(f"\n📊 Running backtest across {len(all_symbols)} symbols:")
    for symbol in all_symbols:
        print(f"   - {symbol}")
    
    # Run comprehensive multi-symbol backtest
    results = engine.run_multi_symbol_backtest(
        symbols=all_symbols,
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    # Generate comprehensive analytics
    reporter = BacktestReporter(results)
    
    print("\n📈 Multi-Symbol Performance Summary")
    print("=" * 70)
    reporter.print_quick_summary()
    
    # Symbol-specific performance breakdown
    if results.symbol_performance:
        print("\n🎯 Performance by Symbol:")
        print("-" * 50)
        for symbol, perf in results.symbol_performance.items():
            print(f"{symbol:>12}: {perf.total_trades:>3} trades | "
                  f"P&L: ${perf.total_pnl:>8.2f} | "
                  f"Win Rate: {perf.win_rate:>5.1%}")
            
            # Show correlations with other symbols
            if perf.correlation_with_other_symbols:
                correlations = []
                for other_symbol, corr in perf.correlation_with_other_symbols.items():
                    correlations.append(f"{other_symbol}: {corr:.2f}")
                if correlations:
                    print(f"             Correlations: {', '.join(correlations)}")
    
    # Strategy performance across symbols
    print("\n⚙️  Strategy Performance Across Symbols:")
    print("-" * 50)
    for setup_id, setup_perf in results.setup_performance.items():
        print(f"{setup_id:>25}: {setup_perf.total_trades:>3} trades | "
              f"P&L: ${setup_perf.total_pnl:>8.2f} | "
              f"Win Rate: {setup_perf.win_rate:>5.1%}")
        
        # Show symbol-specific performance for this strategy
        if setup_perf.symbol_performance:
            symbol_details = []
            for symbol, pnl in setup_perf.symbol_performance.items():
                symbol_details.append(f"{symbol}: ${pnl:.2f}")
            if symbol_details:
                print(f"                          Symbol P&L: {', '.join(symbol_details)}")
    
    # Dynamic adjustment performance
    if results.dynamic_adjustment_performance:
        dap = results.dynamic_adjustment_performance
        print(f"\n🔄 Dynamic Management Performance:")
        print(f"   Total Adjustments: {dap.total_adjustments}")
        print(f"   Static vs Dynamic Improvement: ${dap.static_vs_dynamic_comparison:.2f}")
        print(f"   Regime Detection Accuracy: {dap.regime_accuracy:.1%}")
        
        if dap.adjustment_performance:
            print("   Adjustment Type Performance:")
            for adj_type, performance in dap.adjustment_performance.items():
                print(f"     {adj_type}: ${performance:.2f} avg impact")
    
    # Generate comprehensive reports
    print(f"\n📊 Generating comprehensive analytics reports...")
    report_summary = reporter.generate_full_report(
        symbols=all_symbols,
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    print("\n✅ Advanced Multi-Symbol Backtest Completed!")
    print(f"   Final P&L: ${results.total_pnl:.2f}")
    print(f"   Total Trades: {results.total_trades}")
    print(f"   Overall Win Rate: {results.win_rate:.1%}")
    print(f"   Max Drawdown: ${results.max_drawdown:.2f}")


def example_symbol_specific_optimization():
    """
    Example showing how to optimize strategies for specific symbols and expiration types
    """
    print("\n" + "=" * 70)
    print("🎯 Symbol-Specific Strategy Optimization Example")
    print("=" * 70)
    
    # QQQ-optimized strategies (higher volatility, tech-focused)
    qqq_strategies = [
        StraddleSetup(
            setup_id="qqq_optimized_straddle",
            target_pct=0.60,  # Higher target for QQQ volatility
            stop_loss_pct=2.50,  # Wider stop for volatility
            entry_timeindex=1000,
            scalping_price=0.45  # Higher premium threshold
        ),
        
        MomentumReversalSetup(
            setup_id="qqq_momentum",
            target_pct=0.40,
            stop_loss_pct=1.00,
            entry_timeindex=1500,
            strategy_type="MOMENTUM",
            momentum_threshold=0.008  # Higher threshold for QQQ
        )
    ]
    
    # SPY-optimized strategies (more stable, broader market)
    spy_strategies = [
        IronCondorSetup(
            setup_id="spy_iron_condor",
            target_pct=0.35,
            stop_loss_pct=1.40,
            entry_timeindex=1200,
            wing_width=8,  # Tighter wings for SPY
            short_strike_distance=4
        ),
        
        TimeDecaySetup(
            setup_id="spy_time_decay",
            target_pct=0.30,
            stop_loss_pct=0.90,
            entry_timeindex=1000,
            theta_acceleration_time=4500,
            high_theta_threshold=0.35
        )
    ]
    
    # 1DTE-optimized strategies (faster time decay)
    dte_1_strategies = [
        TimeDecaySetup(
            setup_id="1dte_theta_acceleration",
            target_pct=0.25,  # Lower target for faster decay
            stop_loss_pct=0.75,
            entry_timeindex=1000,
            theta_acceleration_time=4200,  # Earlier acceleration
            high_theta_threshold=0.30
        ),
        
        GammaScalpingSetup(
            setup_id="1dte_gamma_scalping",
            target_pct=0.20,
            stop_loss_pct=0.50,
            entry_timeindex=1500,
            delta_threshold=0.10,  # Tighter delta management
            rebalance_frequency=30  # More frequent rebalancing
        )
    ]
    
    # Run symbol-specific backtests
    symbols_and_strategies = [
        ("QQQ", qqq_strategies, "QQQ-optimized strategies"),
        ("SPY", spy_strategies, "SPY-optimized strategies"),
        ("QQQ 1DTE", dte_1_strategies, "1DTE-optimized strategies (QQQ)"),
        ("SPY 1DTE", dte_1_strategies, "1DTE-optimized strategies (SPY)")
    ]
    
    all_results = {}
    
    for symbol, strategies, description in symbols_and_strategies:
        print(f"\n🔍 Testing {description} on {symbol}")
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=strategies,
            daily_max_loss=500.0,
            enable_dynamic_management=True
        )
        
        results = engine.run_backtest(
            symbols=symbol,
            start_date="2025-08-13",
            end_date="2025-08-15"
        )
        
        all_results[symbol] = results
        
        print(f"   Results: ${results.total_pnl:.2f} P&L, "
              f"{results.total_trades} trades, "
              f"{results.win_rate:.1%} win rate")
    
    # Compare symbol-specific performance
    print(f"\n📊 Symbol-Specific Optimization Results:")
    print("-" * 60)
    print(f"{'Symbol':<12} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Trade':<10}")
    print("-" * 60)
    
    for symbol, results in all_results.items():
        avg_trade = results.total_pnl / max(results.total_trades, 1)
        print(f"{symbol:<12} ${results.total_pnl:<9.2f} {results.total_trades:<8} "
              f"{results.win_rate:<9.1%} ${avg_trade:<9.2f}")
    
    print("\n✅ Symbol-Specific Optimization Example Completed!")


def example_cross_symbol_correlation_analysis():
    """
    Example demonstrating cross-symbol correlation analysis and trading
    """
    print("\n" + "=" * 70)
    print("🔗 Cross-Symbol Correlation Analysis Example")
    print("=" * 70)
    
    # Create correlation-aware strategies
    correlation_strategies = [
        # Pairs trading between QQQ and SPY
        StraddleSetup(
            setup_id="qqq_spy_pairs_long",
            target_pct=0.40,
            stop_loss_pct=1.20,
            entry_timeindex=1000,
            scalping_price=0.35
        ),
        
        # Divergence trading between 0DTE and 1DTE
        HedgedStraddleSetup(
            setup_id="dte_divergence_hedge",
            target_pct=0.30,
            stop_loss_pct=1.00,
            entry_timeindex=1500,
            scalping_price=0.30,
            hedge_strikes_away=4
        ),
        
        # Volatility spread between symbols
        VolatilitySkewSetup(
            setup_id="cross_symbol_vol_spread",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=2000,
            skew_threshold=0.015
        )
    ]
    
    # Run multi-symbol backtest with correlation tracking
    engine = BacktestEngine(
        data_path="5SecData",
        setups=correlation_strategies,
        daily_max_loss=800.0,
        enable_dynamic_management=True,
        enable_multi_symbol=True,
        cross_symbol_risk_limit=1500.0
    )
    
    print("🔍 Running correlation analysis across all symbols...")
    
    results = engine.run_multi_symbol_backtest(
        symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    # Analyze correlations
    print("\n📈 Cross-Symbol Correlation Analysis:")
    print("-" * 50)
    
    if results.symbol_performance:
        for symbol, perf in results.symbol_performance.items():
            if perf.correlation_with_other_symbols:
                print(f"\n{symbol} correlations:")
                for other_symbol, correlation in perf.correlation_with_other_symbols.items():
                    correlation_strength = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.4 else "Weak"
                    correlation_direction = "Positive" if correlation > 0 else "Negative"
                    print(f"   vs {other_symbol}: {correlation:>6.3f} ({correlation_strength} {correlation_direction})")
    
    # Generate correlation-specific reports
    reporter = BacktestReporter(results)
    
    print(f"\n📊 Generating correlation analysis reports...")
    report_summary = reporter.generate_full_report(
        symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    print("\n✅ Cross-Symbol Correlation Analysis Completed!")
    print(f"   Total P&L: ${results.total_pnl:.2f}")
    print(f"   Cross-Symbol Trades: {results.total_trades}")


if __name__ == "__main__":
    # Run all advanced multi-symbol examples
    example_comprehensive_multi_symbol_backtest()
    example_symbol_specific_optimization()
    example_cross_symbol_correlation_analysis()
    
    print("\n" + "=" * 70)
    print("🎉 All Advanced Multi-Symbol Examples Completed!")
    print("=" * 70)