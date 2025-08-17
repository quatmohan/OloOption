# Cross-Symbol Analysis & Correlation Trading Guide

## Table of Contents
1. [Overview](#overview)
2. [Supported Symbol Combinations](#supported-symbol-combinations)
3. [Correlation Analysis](#correlation-analysis)
4. [Cross-Symbol Trading Strategies](#cross-symbol-trading-strategies)
5. [Risk Management](#risk-management)
6. [Performance Analysis](#performance-analysis)
7. [Advanced Techniques](#advanced-techniques)

## Overview

The options backtesting engine provides comprehensive cross-symbol analysis capabilities, allowing traders to:

- Analyze correlations between different underlying assets (QQQ vs SPY)
- Compare performance across different expiration types (0DTE vs 1DTE)
- Implement pairs trading and relative value strategies
- Manage risk across multiple symbols simultaneously
- Identify arbitrage and divergence opportunities

## Supported Symbol Combinations

### Primary Symbols
- **QQQ**: NASDAQ-100 ETF options (standard expiration)
- **SPY**: S&P 500 ETF options (standard expiration)
- **QQQ 1DTE**: QQQ options with 1-day-to-expiration
- **SPY 1DTE**: SPY options with 1-day-to-expiration

### Common Analysis Pairs
1. **QQQ vs SPY**: Tech vs broad market correlation
2. **QQQ vs QQQ 1DTE**: Same underlying, different expiration effects
3. **SPY vs SPY 1DTE**: Same underlying, different expiration effects
4. **QQQ 1DTE vs SPY 1DTE**: Cross-asset 1DTE comparison

## Correlation Analysis

### Basic Correlation Setup
```python
from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup

# Create strategies for correlation analysis
correlation_strategies = [
    StraddleSetup(
        setup_id="correlation_straddle",
        target_pct=0.40,
        stop_loss_pct=1.20,
        entry_timeindex=1000,
        scalping_price=0.35
    )
]

# Enable multi-symbol correlation tracking
engine = BacktestEngine(
    data_path="5SecData",
    setups=correlation_strategies,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1500.0
)

# Run multi-symbol backtest
results = engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)

# Access correlation data
for symbol, perf in results.symbol_performance.items():
    if perf.correlation_with_other_symbols:
        print(f"\n{symbol} correlations:")
        for other_symbol, correlation in perf.correlation_with_other_symbols.items():
            print(f"  vs {other_symbol}: {correlation:.3f}")
```

### Correlation Interpretation
- **+0.8 to +1.0**: Strong positive correlation (move together)
- **+0.4 to +0.8**: Moderate positive correlation
- **-0.4 to +0.4**: Weak correlation (independent movement)
- **-0.8 to -0.4**: Moderate negative correlation
- **-1.0 to -0.8**: Strong negative correlation (move opposite)

### Time-Based Correlation Analysis
```python
def analyze_intraday_correlations():
    """Analyze how correlations change throughout the trading day"""
    
    # Early day correlation (9:30-11:00 AM)
    early_day_engine = BacktestEngine(
        data_path="5SecData",
        setups=[correlation_strategy],
        enable_multi_symbol=True
    )
    
    # Modify entry times for early day analysis
    early_strategy = StraddleSetup(
        setup_id="early_correlation",
        target_pct=0.35,
        stop_loss_pct=1.00,
        entry_timeindex=100,    # Early entry
        close_timeindex=1800,   # Close at 11:00 AM
        scalping_price=0.40
    )
    
    # Mid-day correlation (11:00 AM - 2:00 PM)
    mid_day_strategy = StraddleSetup(
        setup_id="mid_correlation",
        target_pct=0.35,
        stop_loss_pct=1.00,
        entry_timeindex=1800,   # 11:00 AM entry
        close_timeindex=3600,   # Close at 2:00 PM
        scalping_price=0.40
    )
    
    # Late day correlation (2:00 PM - 4:00 PM)
    late_day_strategy = StraddleSetup(
        setup_id="late_correlation",
        target_pct=0.35,
        stop_loss_pct=1.00,
        entry_timeindex=3600,   # 2:00 PM entry
        close_timeindex=4650,   # Close at end of day
        scalping_price=0.40
    )
    
    # Run analysis for each time period
    time_periods = [
        ("Early Day", early_strategy),
        ("Mid Day", mid_day_strategy),
        ("Late Day", late_day_strategy)
    ]
    
    correlation_results = {}
    
    for period_name, strategy in time_periods:
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            enable_multi_symbol=True
        )
        
        results = engine.run_multi_symbol_backtest(
            symbols=["QQQ", "SPY"],
            start_date="2025-08-13",
            end_date="2025-08-15"
        )
        
        correlation_results[period_name] = results
        
        print(f"\n{period_name} Correlations:")
        for symbol, perf in results.symbol_performance.items():
            if perf.correlation_with_other_symbols:
                for other, corr in perf.correlation_with_other_symbols.items():
                    print(f"  {symbol} vs {other}: {corr:.3f}")
    
    return correlation_results
```

## Cross-Symbol Trading Strategies

### Pairs Trading Strategy
```python
class PairsTradingStrategy:
    """Implement pairs trading between QQQ and SPY"""
    
    def __init__(self):
        self.correlation_threshold = 0.7  # Minimum correlation for pairs trading
        self.divergence_threshold = 0.05  # Price divergence threshold
        
    def create_pairs_strategies(self):
        """Create complementary strategies for pairs trading"""
        
        # Long QQQ, Short SPY equivalent
        qqq_long_strategy = CEScalpingSetup(
            setup_id="pairs_qqq_long",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            max_reentries=2,
            scalping_price=0.30
        )
        
        # Short QQQ, Long SPY equivalent
        spy_long_strategy = PEScalpingSetup(
            setup_id="pairs_spy_long",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            max_reentries=2,
            scalping_price=0.30
        )
        
        return [qqq_long_strategy, spy_long_strategy]

# Usage example
pairs_trader = PairsTradingStrategy()
pairs_strategies = pairs_trader.create_pairs_strategies()

pairs_engine = BacktestEngine(
    data_path="5SecData",
    setups=pairs_strategies,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1000.0
)

pairs_results = pairs_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Relative Value Trading
```python
def create_relative_value_strategies():
    """Create strategies to exploit relative value differences"""
    
    # QQQ premium selling when QQQ IV > SPY IV
    qqq_premium_strategy = StraddleSetup(
        setup_id="qqq_relative_premium",
        target_pct=0.45,
        stop_loss_pct=1.35,
        entry_timeindex=1000,
        scalping_price=0.40  # Higher premium for QQQ
    )
    
    # SPY premium buying when SPY IV < QQQ IV
    spy_value_strategy = HedgedStraddleSetup(
        setup_id="spy_relative_value",
        target_pct=0.35,
        stop_loss_pct=1.05,
        entry_timeindex=1000,
        scalping_price=0.30,  # Lower premium for SPY
        hedge_strikes_away=4
    )
    
    return [qqq_premium_strategy, spy_value_strategy]

# Implement relative value trading
rv_strategies = create_relative_value_strategies()

rv_engine = BacktestEngine(
    data_path="5SecData",
    setups=rv_strategies,
    enable_multi_symbol=True,
    enable_dynamic_management=True  # Adapt to relative value changes
)

rv_results = rv_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Expiration Arbitrage
```python
def create_expiration_arbitrage_strategies():
    """Exploit differences between 0DTE and 1DTE options"""
    
    # 0DTE theta acceleration strategy
    dte_0_strategy = TimeDecaySetup(
        setup_id="dte_0_theta",
        target_pct=0.25,
        stop_loss_pct=0.75,
        entry_timeindex=4000,   # Late entry for 0DTE
        theta_acceleration_time=4400,
        high_theta_threshold=0.40
    )
    
    # 1DTE volatility strategy
    dte_1_strategy = VolatilitySkewSetup(
        setup_id="dte_1_vol",
        target_pct=0.35,
        stop_loss_pct=0.90,
        entry_timeindex=1000,   # Earlier entry for 1DTE
        skew_threshold=0.020,
        min_iv_difference=0.025
    )
    
    return [dte_0_strategy, dte_1_strategy]

# Run expiration arbitrage
exp_arb_strategies = create_expiration_arbitrage_strategies()

exp_arb_engine = BacktestEngine(
    data_path="5SecData",
    setups=exp_arb_strategies,
    enable_multi_symbol=True
)

# Test on same underlying with different expirations
exp_arb_results = exp_arb_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "QQQ 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Cross-Asset Momentum
```python
def create_cross_asset_momentum_strategies():
    """Create momentum strategies across different assets"""
    
    # QQQ momentum (tech-heavy, higher volatility)
    qqq_momentum = MomentumReversalSetup(
        setup_id="qqq_momentum",
        target_pct=0.40,
        stop_loss_pct=1.00,
        entry_timeindex=1000,
        strategy_type="MOMENTUM",
        momentum_threshold=0.008,  # Higher threshold for QQQ
        lookback_periods=8
    )
    
    # SPY momentum (broader market, more stable)
    spy_momentum = MomentumReversalSetup(
        setup_id="spy_momentum",
        target_pct=0.35,
        stop_loss_pct=0.90,
        entry_timeindex=1000,
        strategy_type="MOMENTUM",
        momentum_threshold=0.006,  # Lower threshold for SPY
        lookback_periods=12
    )
    
    # Cross-momentum confirmation strategy
    cross_momentum = GammaScalpingSetup(
        setup_id="cross_momentum_gamma",
        target_pct=0.25,
        stop_loss_pct=0.70,
        entry_timeindex=1200,
        delta_threshold=0.12,
        rebalance_frequency=45
    )
    
    return [qqq_momentum, spy_momentum, cross_momentum]

# Implement cross-asset momentum
momentum_strategies = create_cross_asset_momentum_strategies()

momentum_engine = BacktestEngine(
    data_path="5SecData",
    setups=momentum_strategies,
    enable_multi_symbol=True,
    enable_dynamic_management=True
)

momentum_results = momentum_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

## Risk Management

### Cross-Symbol Position Limits
```python
# Configure cross-symbol risk limits
def configure_cross_symbol_risk():
    """Configure comprehensive cross-symbol risk management"""
    
    # Conservative cross-symbol setup
    conservative_engine = BacktestEngine(
        data_path="5SecData",
        setups=strategies,
        daily_max_loss=400.0,           # Per-symbol daily limit
        enable_multi_symbol=True,
        cross_symbol_risk_limit=800.0   # Total cross-symbol limit (2x individual)
    )
    
    # Moderate cross-symbol setup
    moderate_engine = BacktestEngine(
        data_path="5SecData",
        setups=strategies,
        daily_max_loss=600.0,           # Per-symbol daily limit
        enable_multi_symbol=True,
        cross_symbol_risk_limit=1500.0  # Total cross-symbol limit (2.5x individual)
    )
    
    # Aggressive cross-symbol setup
    aggressive_engine = BacktestEngine(
        data_path="5SecData",
        setups=strategies,
        daily_max_loss=800.0,           # Per-symbol daily limit
        enable_multi_symbol=True,
        cross_symbol_risk_limit=2400.0  # Total cross-symbol limit (3x individual)
    )
    
    return conservative_engine, moderate_engine, aggressive_engine
```

### Correlation-Based Risk Adjustment
```python
def adjust_risk_for_correlation(correlation_matrix):
    """Adjust position sizes based on correlation levels"""
    
    risk_adjustments = {}
    
    for symbol1 in correlation_matrix:
        for symbol2, correlation in correlation_matrix[symbol1].items():
            if symbol1 != symbol2:
                # Reduce position size for highly correlated symbols
                if abs(correlation) > 0.8:
                    risk_adjustment = 0.6  # Reduce to 60% of normal size
                elif abs(correlation) > 0.6:
                    risk_adjustment = 0.8  # Reduce to 80% of normal size
                else:
                    risk_adjustment = 1.0  # Full size for low correlation
                
                risk_adjustments[f"{symbol1}_{symbol2}"] = risk_adjustment
    
    return risk_adjustments

# Example usage
correlation_matrix = {
    "QQQ": {"SPY": 0.85, "QQQ 1DTE": 0.95, "SPY 1DTE": 0.80},
    "SPY": {"QQQ": 0.85, "QQQ 1DTE": 0.82, "SPY 1DTE": 0.96},
    "QQQ 1DTE": {"QQQ": 0.95, "SPY": 0.82, "SPY 1DTE": 0.83},
    "SPY 1DTE": {"QQQ": 0.80, "SPY": 0.96, "QQQ 1DTE": 0.83}
}

risk_adjustments = adjust_risk_for_correlation(correlation_matrix)
print("Risk adjustments based on correlation:")
for pair, adjustment in risk_adjustments.items():
    print(f"  {pair}: {adjustment:.1%} of normal position size")
```

### Dynamic Cross-Symbol Risk Management
```python
class CrossSymbolRiskManager:
    """Advanced cross-symbol risk management"""
    
    def __init__(self, base_daily_limit=500.0, correlation_threshold=0.7):
        self.base_daily_limit = base_daily_limit
        self.correlation_threshold = correlation_threshold
        self.symbol_exposures = {}
        self.correlation_matrix = {}
    
    def calculate_effective_exposure(self, symbol_positions):
        """Calculate effective exposure considering correlations"""
        
        effective_exposure = 0.0
        
        for symbol1, exposure1 in symbol_positions.items():
            for symbol2, exposure2 in symbol_positions.items():
                if symbol1 != symbol2:
                    correlation = self.correlation_matrix.get(symbol1, {}).get(symbol2, 0.0)
                    # Add correlated exposure
                    effective_exposure += exposure1 * exposure2 * correlation
                else:
                    # Add direct exposure
                    effective_exposure += exposure1 ** 2
        
        return effective_exposure ** 0.5
    
    def should_reduce_positions(self, current_exposures):
        """Determine if positions should be reduced due to correlation"""
        
        effective_exposure = self.calculate_effective_exposure(current_exposures)
        total_limit = self.base_daily_limit * len(current_exposures)
        
        return effective_exposure > total_limit * 0.8  # 80% of total limit
    
    def get_position_size_multiplier(self, symbol, other_symbols_exposure):
        """Get position size multiplier based on other symbol exposures"""
        
        total_correlation_exposure = 0.0
        
        for other_symbol, exposure in other_symbols_exposure.items():
            correlation = self.correlation_matrix.get(symbol, {}).get(other_symbol, 0.0)
            total_correlation_exposure += abs(correlation) * exposure
        
        # Reduce position size if high correlation exposure
        if total_correlation_exposure > self.base_daily_limit * 0.5:
            return 0.5  # Reduce to 50%
        elif total_correlation_exposure > self.base_daily_limit * 0.3:
            return 0.7  # Reduce to 70%
        else:
            return 1.0  # Full size
```

## Performance Analysis

### Cross-Symbol Performance Metrics
```python
def analyze_cross_symbol_performance(results):
    """Comprehensive cross-symbol performance analysis"""
    
    print("Cross-Symbol Performance Analysis")
    print("=" * 50)
    
    # Overall performance
    print(f"Total P&L: ${results.total_pnl:.2f}")
    print(f"Total Trades: {results.total_trades}")
    print(f"Overall Win Rate: {results.win_rate:.1%}")
    print(f"Max Drawdown: ${results.max_drawdown:.2f}")
    
    # Symbol-specific performance
    if results.symbol_performance:
        print(f"\nSymbol Performance Breakdown:")
        print("-" * 40)
        print(f"{'Symbol':<12} {'P&L':<10} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 40)
        
        for symbol, perf in results.symbol_performance.items():
            print(f"{symbol:<12} ${perf.total_pnl:<9.2f} {perf.total_trades:<8} {perf.win_rate:<9.1%}")
    
    # Correlation analysis
    if results.symbol_performance:
        print(f"\nCorrelation Matrix:")
        print("-" * 30)
        
        symbols = list(results.symbol_performance.keys())
        
        # Print header
        print(f"{'Symbol':<12}", end="")
        for symbol in symbols:
            print(f"{symbol:<8}", end="")
        print()
        
        # Print correlation matrix
        for symbol1 in symbols:
            print(f"{symbol1:<12}", end="")
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    print(f"{'1.000':<8}", end="")
                else:
                    corr = results.symbol_performance[symbol1].correlation_with_other_symbols.get(symbol2, 0.0)
                    print(f"{corr:<8.3f}", end="")
            print()
    
    # Strategy performance across symbols
    if results.setup_performance:
        print(f"\nStrategy Performance Across Symbols:")
        print("-" * 50)
        
        for setup_id, setup_perf in results.setup_performance.items():
            print(f"\n{setup_id}:")
            print(f"  Total P&L: ${setup_perf.total_pnl:.2f}")
            print(f"  Win Rate: {setup_perf.win_rate:.1%}")
            
            if setup_perf.symbol_performance:
                print(f"  Symbol Breakdown:")
                for symbol, pnl in setup_perf.symbol_performance.items():
                    print(f"    {symbol}: ${pnl:.2f}")
    
    return results

# Usage
analyzed_results = analyze_cross_symbol_performance(multi_symbol_results)
```

### Correlation Stability Analysis
```python
def analyze_correlation_stability(results):
    """Analyze how correlations change over time"""
    
    if not hasattr(results, 'daily_results'):
        return
    
    daily_correlations = {}
    
    for daily_result in results.daily_results:
        date = daily_result.date
        
        # Extract daily correlations (would need to be tracked in engine)
        if hasattr(daily_result, 'daily_correlations'):
            daily_correlations[date] = daily_result.daily_correlations
    
    # Analyze correlation stability
    correlation_changes = {}
    
    for symbol_pair in daily_correlations.get(list(daily_correlations.keys())[0], {}):
        correlations = [daily_correlations[date][symbol_pair] for date in daily_correlations]
        
        if len(correlations) > 1:
            correlation_std = (sum((c - sum(correlations)/len(correlations))**2 for c in correlations) / len(correlations))**0.5
            correlation_changes[symbol_pair] = {
                'mean': sum(correlations) / len(correlations),
                'std': correlation_std,
                'stability': 'Stable' if correlation_std < 0.1 else 'Unstable'
            }
    
    print("Correlation Stability Analysis:")
    print("-" * 40)
    print(f"{'Pair':<15} {'Mean':<8} {'Std':<8} {'Stability':<10}")
    print("-" * 40)
    
    for pair, stats in correlation_changes.items():
        print(f"{pair:<15} {stats['mean']:<8.3f} {stats['std']:<8.3f} {stats['stability']:<10}")
    
    return correlation_changes
```

## Advanced Techniques

### Statistical Arbitrage
```python
def create_statistical_arbitrage_strategy():
    """Create statistical arbitrage strategy based on correlation breakdown"""
    
    # Strategy that profits when QQQ-SPY correlation breaks down
    stat_arb_strategies = [
        # Long QQQ when it underperforms relative to SPY
        CEScalpingSetup(
            setup_id="stat_arb_qqq_long",
            target_pct=0.35,
            stop_loss_pct=0.85,
            entry_timeindex=1000,
            max_reentries=2,
            scalping_price=0.25  # Lower threshold for stat arb
        ),
        
        # Short QQQ when it outperforms relative to SPY
        PEScalpingSetup(
            setup_id="stat_arb_qqq_short",
            target_pct=0.35,
            stop_loss_pct=0.85,
            entry_timeindex=1000,
            max_reentries=2,
            scalping_price=0.25
        ),
        
        # Hedge with SPY opposite positions
        HedgedStraddleSetup(
            setup_id="stat_arb_spy_hedge",
            target_pct=0.20,
            stop_loss_pct=0.60,
            entry_timeindex=1000,
            scalping_price=0.30,
            hedge_strikes_away=3
        )
    ]
    
    return stat_arb_strategies

# Implement statistical arbitrage
stat_arb_strategies = create_statistical_arbitrage_strategy()

stat_arb_engine = BacktestEngine(
    data_path="5SecData",
    setups=stat_arb_strategies,
    enable_multi_symbol=True,
    enable_dynamic_management=True,
    cross_symbol_risk_limit=1000.0
)

stat_arb_results = stat_arb_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Volatility Surface Arbitrage
```python
def create_volatility_surface_arbitrage():
    """Exploit differences in volatility surfaces across symbols"""
    
    vol_surface_strategies = [
        # QQQ volatility skew strategy
        VolatilitySkewSetup(
            setup_id="qqq_vol_surface",
            target_pct=0.30,
            stop_loss_pct=0.80,
            entry_timeindex=1000,
            skew_threshold=0.018,
            min_iv_difference=0.022
        ),
        
        # SPY volatility skew strategy
        VolatilitySkewSetup(
            setup_id="spy_vol_surface",
            target_pct=0.28,
            stop_loss_pct=0.75,
            entry_timeindex=1000,
            skew_threshold=0.015,  # Lower threshold for SPY
            min_iv_difference=0.020
        ),
        
        # Cross-surface arbitrage
        RatioSpreadSetup(
            setup_id="cross_surface_ratio",
            target_pct=0.40,
            stop_loss_pct=1.20,
            entry_timeindex=1200,
            ratio="1:2",
            unlimited_risk_protection=True
        )
    ]
    
    return vol_surface_strategies

# Implement volatility surface arbitrage
vol_surface_strategies = create_volatility_surface_arbitrage()

vol_surface_engine = BacktestEngine(
    data_path="5SecData",
    setups=vol_surface_strategies,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1200.0
)

vol_surface_results = vol_surface_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Cross-Expiration Calendar Spreads
```python
def create_cross_expiration_strategies():
    """Create strategies that exploit time decay differences between expirations"""
    
    calendar_strategies = [
        # Sell 0DTE, buy 1DTE (time decay calendar)
        TimeDecaySetup(
            setup_id="calendar_0dte_sell",
            target_pct=0.20,
            stop_loss_pct=0.60,
            entry_timeindex=4200,   # Late entry for 0DTE
            theta_acceleration_time=4500,
            high_theta_threshold=0.45
        ),
        
        # Complementary 1DTE position
        StraddleSetup(
            setup_id="calendar_1dte_buy",
            target_pct=0.15,
            stop_loss_pct=0.45,
            entry_timeindex=1000,   # Earlier entry for 1DTE
            scalping_price=0.25     # Lower premium for buying
        )
    ]
    
    return calendar_strategies

# Implement cross-expiration calendar spreads
calendar_strategies = create_cross_expiration_strategies()

calendar_engine = BacktestEngine(
    data_path="5SecData",
    setups=calendar_strategies,
    enable_multi_symbol=True
)

# Run on same underlying with different expirations
calendar_results = calendar_engine.run_multi_symbol_backtest(
    symbols=["QQQ", "QQQ 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

## Best Practices for Cross-Symbol Analysis

### 1. Correlation Monitoring
- Monitor correlations in real-time during backtests
- Adjust position sizes based on correlation changes
- Use correlation breakdowns as trading signals
- Account for time-of-day correlation variations

### 2. Risk Management
- Set appropriate cross-symbol risk limits
- Use correlation-adjusted position sizing
- Monitor effective exposure across all symbols
- Implement correlation-based stop-losses

### 3. Strategy Selection
- Use pairs trading for highly correlated symbols
- Use relative value strategies for moderately correlated symbols
- Use independent strategies for uncorrelated symbols
- Consider expiration effects in cross-expiration strategies

### 4. Performance Analysis
- Analyze performance by symbol and strategy combination
- Monitor correlation stability over time
- Track cross-symbol arbitrage opportunities
- Measure risk-adjusted returns across symbol pairs

### 5. Market Regime Considerations
- Correlations change with market regimes
- High volatility periods often increase correlations
- Crisis periods can cause correlation spikes
- Normal market periods allow for more diverse strategies

This guide provides comprehensive coverage of cross-symbol analysis and correlation trading techniques available in the options backtesting engine.