#!/usr/bin/env python3
"""
Advanced Parameter Optimization Examples
Demonstrates systematic parameter optimization and strategy tuning
"""

import sys
import os
import itertools
from typing import Dict, List, Tuple, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import (
    StraddleSetup, HedgedStraddleSetup, CEScalpingSetup, PEScalpingSetup,
    IronCondorSetup, ButterflySetup, MomentumReversalSetup, VolatilitySkewSetup,
    TimeDecaySetup, GammaScalpingSetup
)
from backtesting_engine.reporting import BacktestReporter


def optimize_straddle_parameters():
    """
    Comprehensive parameter optimization for straddle strategies
    """
    print("🎯 Straddle Strategy Parameter Optimization")
    print("=" * 60)
    
    # Define parameter ranges to test
    parameter_ranges = {
        'target_pct': [0.25, 0.35, 0.50, 0.75, 1.00],
        'stop_loss_pct': [1.00, 1.50, 2.00, 2.50, 3.00],
        'entry_timeindex': [800, 1000, 1200, 1500, 2000],
        'scalping_price': [0.25, 0.30, 0.35, 0.40, 0.50]
    }
    
    print(f"Testing {len(parameter_ranges['target_pct']) * len(parameter_ranges['stop_loss_pct']) * len(parameter_ranges['entry_timeindex']) * len(parameter_ranges['scalping_price'])} parameter combinations...")
    
    best_params = None
    best_pnl = float('-inf')
    optimization_results = []
    
    # Test parameter combinations (sample subset for demonstration)
    test_combinations = [
        (0.35, 1.50, 1000, 0.35),
        (0.50, 2.00, 1200, 0.40),
        (0.25, 1.00, 800, 0.30),
        (0.75, 2.50, 1500, 0.45),
        (1.00, 3.00, 2000, 0.50)
    ]
    
    for target, stop_loss, entry_time, scalping_price in test_combinations:
        print(f"  Testing: target={target}, stop_loss={stop_loss}, entry={entry_time}, scalping_price={scalping_price}")
        
        # Create strategy with current parameters
        strategy = StraddleSetup(
            setup_id=f"straddle_opt_{target}_{stop_loss}_{entry_time}_{scalping_price}",
            target_pct=target,
            stop_loss_pct=stop_loss,
            entry_timeindex=entry_time,
            scalping_price=scalping_price,
            strike_selection="premium"
        )
        
        # Run backtest
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=500.0,
            enable_dynamic_management=False  # Disable for pure parameter testing
        )
        
        results = engine.run_backtest(
            symbols="QQQ",
            start_date="2025-08-13",
            end_date="2025-08-15"
        )
        
        # Calculate optimization metrics
        sharpe_ratio = calculate_sharpe_ratio(results)
        max_drawdown_ratio = results.max_drawdown / max(abs(results.total_pnl), 1)
        
        optimization_result = {
            'parameters': {
                'target_pct': target,
                'stop_loss_pct': stop_loss,
                'entry_timeindex': entry_time,
                'scalping_price': scalping_price
            },
            'total_pnl': results.total_pnl,
            'total_trades': results.total_trades,
            'win_rate': results.win_rate,
            'max_drawdown': results.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_ratio': max_drawdown_ratio,
            'profit_factor': calculate_profit_factor(results)
        }
        
        optimization_results.append(optimization_result)
        
        # Track best parameters by total P&L
        if results.total_pnl > best_pnl:
            best_pnl = results.total_pnl
            best_params = optimization_result
        
        print(f"    Result: ${results.total_pnl:.2f} P&L, {results.total_trades} trades, {results.win_rate:.1%} win rate")
    
    # Display optimization results
    print(f"\n📊 Straddle Parameter Optimization Results:")
    print("-" * 80)
    print(f"{'Target':<8} {'Stop':<8} {'Entry':<8} {'Scalp':<8} {'P&L':<10} {'Trades':<8} {'Win%':<8} {'Sharpe':<8}")
    print("-" * 80)
    
    # Sort by P&L
    sorted_results = sorted(optimization_results, key=lambda x: x['total_pnl'], reverse=True)
    
    for result in sorted_results:
        params = result['parameters']
        print(f"{params['target_pct']:<8.2f} {params['stop_loss_pct']:<8.2f} "
              f"{params['entry_timeindex']:<8} {params['scalping_price']:<8.2f} "
              f"${result['total_pnl']:<9.2f} {result['total_trades']:<8} "
              f"{result['win_rate']:<7.1%} {result['sharpe_ratio']:<7.2f}")
    
    print(f"\n🏆 Best Parameters (by P&L):")
    if best_params:
        params = best_params['parameters']
        print(f"   Target: {params['target_pct']}, Stop Loss: {params['stop_loss_pct']}")
        print(f"   Entry Time: {params['entry_timeindex']}, Scalping Price: {params['scalping_price']}")
        print(f"   Performance: ${best_params['total_pnl']:.2f} P&L, {best_params['win_rate']:.1%} win rate")
    
    return sorted_results


def optimize_multi_leg_strategies():
    """
    Parameter optimization for complex multi-leg strategies
    """
    print("\n🔧 Multi-Leg Strategy Parameter Optimization")
    print("=" * 60)
    
    # Iron Condor optimization
    print("🔹 Optimizing Iron Condor Parameters...")
    
    iron_condor_params = [
        {'wing_width': 8, 'short_strike_distance': 4, 'target_pct': 0.30},
        {'wing_width': 10, 'short_strike_distance': 5, 'target_pct': 0.35},
        {'wing_width': 12, 'short_strike_distance': 6, 'target_pct': 0.40},
        {'wing_width': 15, 'short_strike_distance': 7, 'target_pct': 0.45}
    ]
    
    iron_condor_results = []
    
    for params in iron_condor_params:
        strategy = IronCondorSetup(
            setup_id=f"ic_opt_{params['wing_width']}_{params['short_strike_distance']}",
            target_pct=params['target_pct'],
            stop_loss_pct=1.50,
            entry_timeindex=1200,
            wing_width=params['wing_width'],
            short_strike_distance=params['short_strike_distance']
        )
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=400.0
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        iron_condor_results.append({
            'params': params,
            'pnl': results.total_pnl,
            'trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Wing Width: {params['wing_width']}, Distance: {params['short_strike_distance']} "
              f"-> ${results.total_pnl:.2f} P&L")
    
    # Butterfly optimization
    print("\n🔹 Optimizing Butterfly Parameters...")
    
    butterfly_params = [
        {'wing_distance': 4, 'butterfly_type': 'CALL', 'target_pct': 0.35},
        {'wing_distance': 5, 'butterfly_type': 'CALL', 'target_pct': 0.40},
        {'wing_distance': 6, 'butterfly_type': 'CALL', 'target_pct': 0.45},
        {'wing_distance': 5, 'butterfly_type': 'PUT', 'target_pct': 0.40}
    ]
    
    butterfly_results = []
    
    for params in butterfly_params:
        strategy = ButterflySetup(
            setup_id=f"bf_opt_{params['wing_distance']}_{params['butterfly_type']}",
            target_pct=params['target_pct'],
            stop_loss_pct=1.20,
            entry_timeindex=1500,
            wing_distance=params['wing_distance'],
            butterfly_type=params['butterfly_type']
        )
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=400.0
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        butterfly_results.append({
            'params': params,
            'pnl': results.total_pnl,
            'trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Wing Distance: {params['wing_distance']}, Type: {params['butterfly_type']} "
              f"-> ${results.total_pnl:.2f} P&L")
    
    # Display best multi-leg parameters
    best_ic = max(iron_condor_results, key=lambda x: x['pnl'])
    best_bf = max(butterfly_results, key=lambda x: x['pnl'])
    
    print(f"\n🏆 Best Multi-Leg Parameters:")
    print(f"   Iron Condor: Wing Width {best_ic['params']['wing_width']}, "
          f"Distance {best_ic['params']['short_strike_distance']} -> ${best_ic['pnl']:.2f}")
    print(f"   Butterfly: Wing Distance {best_bf['params']['wing_distance']}, "
          f"Type {best_bf['params']['butterfly_type']} -> ${best_bf['pnl']:.2f}")
    
    return iron_condor_results, butterfly_results


def optimize_pattern_recognition_parameters():
    """
    Optimize parameters for pattern recognition strategies
    """
    print("\n🔍 Pattern Recognition Parameter Optimization")
    print("=" * 60)
    
    # Momentum strategy optimization
    print("🔹 Optimizing Momentum Strategy Parameters...")
    
    momentum_params = [
        {'momentum_threshold': 0.005, 'reversion_lookback': 8, 'strategy_type': 'MOMENTUM'},
        {'momentum_threshold': 0.007, 'reversion_lookback': 10, 'strategy_type': 'MOMENTUM'},
        {'momentum_threshold': 0.010, 'reversion_lookback': 12, 'strategy_type': 'REVERSION'},
        {'momentum_threshold': 0.008, 'reversion_lookback': 15, 'strategy_type': 'ADAPTIVE'}
    ]
    
    momentum_results = []
    
    for params in momentum_params:
        strategy = MomentumReversalSetup(
            setup_id=f"mom_opt_{params['momentum_threshold']}_{params['reversion_lookback']}",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1000,
            strategy_type=params['strategy_type'],
            momentum_threshold=params['momentum_threshold'],
            reversion_lookback=params['reversion_lookback']
        )
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=400.0
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        momentum_results.append({
            'params': params,
            'pnl': results.total_pnl,
            'trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Threshold: {params['momentum_threshold']:.3f}, Lookback: {params['reversion_lookback']}, "
              f"Type: {params['strategy_type']} -> ${results.total_pnl:.2f} P&L")
    
    # Volatility skew optimization
    print("\n🔹 Optimizing Volatility Skew Parameters...")
    
    vol_skew_params = [
        {'skew_threshold': 0.015},
        {'skew_threshold': 0.020},
        {'skew_threshold': 0.025},
        {'skew_threshold': 0.018}
    ]
    
    vol_skew_results = []
    
    for params in vol_skew_params:
        strategy = VolatilitySkewSetup(
            setup_id=f"vol_opt_{params['skew_threshold']}",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1500,
            skew_threshold=params['skew_threshold']
        )
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=400.0
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        vol_skew_results.append({
            'params': params,
            'pnl': results.total_pnl,
            'trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Skew Threshold: {params['skew_threshold']:.3f} -> ${results.total_pnl:.2f} P&L")
    
    # Display best pattern parameters
    best_momentum = max(momentum_results, key=lambda x: x['pnl'])
    best_vol_skew = max(vol_skew_results, key=lambda x: x['pnl'])
    
    print(f"\n🏆 Best Pattern Recognition Parameters:")
    print(f"   Momentum: Threshold {best_momentum['params']['momentum_threshold']:.3f}, "
          f"Lookback {best_momentum['params']['reversion_lookback']} -> ${best_momentum['pnl']:.2f}")
    print(f"   Vol Skew: Threshold {best_vol_skew['params']['skew_threshold']:.3f} -> ${best_vol_skew['pnl']:.2f}")
    
    return momentum_results, vol_skew_results


def optimize_risk_management_parameters():
    """
    Optimize risk management and position sizing parameters
    """
    print("\n⚠️  Risk Management Parameter Optimization")
    print("=" * 60)
    
    # Test different daily max loss limits
    daily_limits = [300.0, 500.0, 800.0, 1000.0, 1500.0]
    
    # Base strategy for testing
    base_strategy = StraddleSetup(
        setup_id="risk_opt_straddle",
        target_pct=0.40,
        stop_loss_pct=1.50,
        entry_timeindex=1000,
        scalping_price=0.35
    )
    
    risk_results = []
    
    print("🔹 Testing Daily Risk Limits...")
    
    for daily_limit in daily_limits:
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[base_strategy],
            daily_max_loss=daily_limit,
            enable_dynamic_management=False
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        # Calculate risk-adjusted metrics
        risk_adjusted_return = results.total_pnl / daily_limit if daily_limit > 0 else 0
        max_risk_utilization = results.max_drawdown / daily_limit if daily_limit > 0 else 0
        
        risk_results.append({
            'daily_limit': daily_limit,
            'total_pnl': results.total_pnl,
            'max_drawdown': results.max_drawdown,
            'risk_adjusted_return': risk_adjusted_return,
            'max_risk_utilization': max_risk_utilization,
            'total_trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Daily Limit: ${daily_limit:.0f} -> P&L: ${results.total_pnl:.2f}, "
              f"Max DD: ${results.max_drawdown:.2f}, Risk Adj: {risk_adjusted_return:.3f}")
    
    # Test different target/stop-loss ratios
    print("\n🔹 Testing Target/Stop-Loss Ratios...")
    
    ratio_tests = [
        {'target': 0.25, 'stop_loss': 0.75, 'ratio': '1:3'},
        {'target': 0.35, 'stop_loss': 1.05, 'ratio': '1:3'},
        {'target': 0.40, 'stop_loss': 1.20, 'ratio': '1:3'},
        {'target': 0.50, 'stop_loss': 1.00, 'ratio': '1:2'},
        {'target': 0.60, 'stop_loss': 0.60, 'ratio': '1:1'}
    ]
    
    ratio_results = []
    
    for ratio_test in ratio_tests:
        strategy = StraddleSetup(
            setup_id=f"ratio_opt_{ratio_test['ratio']}",
            target_pct=ratio_test['target'],
            stop_loss_pct=ratio_test['stop_loss'],
            entry_timeindex=1000,
            scalping_price=0.35
        )
        
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=500.0
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        ratio_results.append({
            'ratio': ratio_test['ratio'],
            'target': ratio_test['target'],
            'stop_loss': ratio_test['stop_loss'],
            'pnl': results.total_pnl,
            'trades': results.total_trades,
            'win_rate': results.win_rate
        })
        
        print(f"  Ratio {ratio_test['ratio']} (Target: ${ratio_test['target']:.2f}, "
              f"Stop: ${ratio_test['stop_loss']:.2f}) -> ${results.total_pnl:.2f} P&L")
    
    # Display optimal risk parameters
    best_risk_limit = max(risk_results, key=lambda x: x['risk_adjusted_return'])
    best_ratio = max(ratio_results, key=lambda x: x['pnl'])
    
    print(f"\n🏆 Optimal Risk Management Parameters:")
    print(f"   Daily Limit: ${best_risk_limit['daily_limit']:.0f} "
          f"(Risk-Adjusted Return: {best_risk_limit['risk_adjusted_return']:.3f})")
    print(f"   Target/Stop Ratio: {best_ratio['ratio']} "
          f"(Target: ${best_ratio['target']:.2f}, Stop: ${best_ratio['stop_loss']:.2f})")
    
    return risk_results, ratio_results


def run_comprehensive_optimization():
    """
    Run comprehensive parameter optimization across all strategy types
    """
    print("\n🎯 Comprehensive Parameter Optimization Suite")
    print("=" * 70)
    
    # Run all optimization modules
    straddle_results = optimize_straddle_parameters()
    ic_results, bf_results = optimize_multi_leg_strategies()
    momentum_results, vol_skew_results = optimize_pattern_recognition_parameters()
    risk_results, ratio_results = optimize_risk_management_parameters()
    
    # Create optimized strategy portfolio
    print(f"\n🏆 Creating Optimized Strategy Portfolio")
    print("=" * 50)
    
    # Use best parameters from each optimization
    optimized_strategies = [
        # Best straddle configuration
        StraddleSetup(
            setup_id="optimized_straddle",
            target_pct=straddle_results[0]['parameters']['target_pct'],
            stop_loss_pct=straddle_results[0]['parameters']['stop_loss_pct'],
            entry_timeindex=straddle_results[0]['parameters']['entry_timeindex'],
            scalping_price=straddle_results[0]['parameters']['scalping_price']
        ),
        
        # Best iron condor configuration
        IronCondorSetup(
            setup_id="optimized_iron_condor",
            target_pct=max(ic_results, key=lambda x: x['pnl'])['params']['target_pct'],
            stop_loss_pct=1.50,
            entry_timeindex=1200,
            wing_width=max(ic_results, key=lambda x: x['pnl'])['params']['wing_width'],
            short_strike_distance=max(ic_results, key=lambda x: x['pnl'])['params']['short_strike_distance']
        ),
        
        # Best momentum configuration
        MomentumReversalSetup(
            setup_id="optimized_momentum",
            target_pct=0.35,
            stop_loss_pct=0.90,
            entry_timeindex=1000,
            strategy_type=max(momentum_results, key=lambda x: x['pnl'])['params']['strategy_type'],
            momentum_threshold=max(momentum_results, key=lambda x: x['pnl'])['params']['momentum_threshold'],
            reversion_lookback=max(momentum_results, key=lambda x: x['pnl'])['params']['reversion_lookback']
        )
    ]
    
    # Test optimized portfolio
    print("🧪 Testing optimized strategy portfolio...")
    
    engine = BacktestEngine(
        data_path="5SecData",
        setups=optimized_strategies,
        daily_max_loss=max(risk_results, key=lambda x: x['risk_adjusted_return'])['daily_limit'],
        enable_dynamic_management=True
    )
    
    optimized_results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
    
    print(f"\n📊 Optimized Portfolio Performance:")
    print(f"   Total P&L: ${optimized_results.total_pnl:.2f}")
    print(f"   Total Trades: {optimized_results.total_trades}")
    print(f"   Win Rate: {optimized_results.win_rate:.1%}")
    print(f"   Max Drawdown: ${optimized_results.max_drawdown:.2f}")
    print(f"   Sharpe Ratio: {calculate_sharpe_ratio(optimized_results):.2f}")
    
    # Generate optimization report
    reporter = BacktestReporter(optimized_results)
    
    print(f"\n📊 Generating optimization reports...")
    report_summary = reporter.generate_full_report(
        symbols=["QQQ"],
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    return optimized_results


def calculate_sharpe_ratio(results) -> float:
    """Calculate Sharpe ratio for backtest results"""
    if not results.daily_results or len(results.daily_results) < 2:
        return 0.0
    
    daily_returns = [day.daily_pnl for day in results.daily_results]
    
    if len(daily_returns) < 2:
        return 0.0
    
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std_dev = variance ** 0.5
    
    return mean_return / std_dev if std_dev > 0 else 0.0


def calculate_profit_factor(results) -> float:
    """Calculate profit factor (gross profit / gross loss)"""
    if not results.trade_log:
        return 0.0
    
    gross_profit = sum(trade.pnl for trade in results.trade_log if trade.pnl > 0)
    gross_loss = abs(sum(trade.pnl for trade in results.trade_log if trade.pnl < 0))
    
    return gross_profit / gross_loss if gross_loss > 0 else float('inf')


if __name__ == "__main__":
    print("🎯 Advanced Parameter Optimization Examples")
    print("=" * 70)
    
    # Run individual optimization modules
    print("Running individual parameter optimizations...")
    optimize_straddle_parameters()
    optimize_multi_leg_strategies()
    optimize_pattern_recognition_parameters()
    optimize_risk_management_parameters()
    
    # Run comprehensive optimization
    optimized_results = run_comprehensive_optimization()
    
    print("\n✅ Parameter Optimization Examples Completed!")
    print("=" * 70)
    print(f"🏆 Final Optimized Portfolio Performance: ${optimized_results.total_pnl:.2f} P&L")