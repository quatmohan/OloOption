# Advanced Options Backtesting Engine Usage Guide

## Table of Contents
1. [Multi-Symbol Backtesting](#multi-symbol-backtesting)
2. [Advanced Strategy Configurations](#advanced-strategy-configurations)
3. [Market Regime Detection & Dynamic Adaptation](#market-regime-detection--dynamic-adaptation)
4. [Pattern Recognition Strategies](#pattern-recognition-strategies)
5. [Cross-Symbol Analysis & Correlation Trading](#cross-symbol-analysis--correlation-trading)
6. [Parameter Optimization](#parameter-optimization)
7. [Advanced Reporting & Analytics](#advanced-reporting--analytics)

## Multi-Symbol Backtesting

The backtesting engine supports comprehensive multi-symbol analysis across all available data sources:

### Supported Symbols
- **QQQ**: Standard expiration QQQ options
- **SPY**: Standard expiration SPY options  
- **QQQ 1DTE**: 1-day-to-expiration QQQ options
- **SPY 1DTE**: 1-day-to-expiration SPY options

### Basic Multi-Symbol Setup

```python
from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup

# Create strategies that work across all symbols
strategies = [
    StraddleSetup(
        setup_id="multi_symbol_straddle",
        target_pct=0.50,
        stop_loss_pct=2.0,
        entry_timeindex=1000,
        scalping_price=0.40
    )
]

# Configure multi-symbol engine
engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=1000.0,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=2000.0
)

# Run across all symbols
results = engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Symbol-Specific Optimization

Different symbols have different characteristics and may require optimized parameters:

```python
# QQQ-optimized strategies (higher volatility)
qqq_strategies = [
    StraddleSetup(
        setup_id="qqq_optimized",
        target_pct=0.60,        # Higher target for QQQ volatility
        stop_loss_pct=2.50,     # Wider stop for volatility
        scalping_price=0.45     # Higher premium threshold
    )
]

# SPY-optimized strategies (more stable)
spy_strategies = [
    IronCondorSetup(
        setup_id="spy_iron_condor",
        target_pct=0.35,
        stop_loss_pct=1.40,
        wing_width=8,           # Tighter wings for SPY
        short_strike_distance=4
    )
]

# 1DTE-optimized strategies (faster time decay)
dte_1_strategies = [
    TimeDecaySetup(
        setup_id="1dte_theta",
        target_pct=0.25,        # Lower target for faster decay
        theta_acceleration_time=4200,  # Earlier acceleration
        high_theta_threshold=0.30
    )
]
```

## Advanced Strategy Configurations

### Traditional Strategies

#### Straddle Strategies
```python
# Premium-based straddle
premium_straddle = StraddleSetup(
    setup_id="premium_straddle",
    target_pct=0.50,
    stop_loss_pct=2.0,
    entry_timeindex=1000,
    strike_selection="premium",  # Select by premium threshold
    scalping_price=0.40         # Minimum premium required
)

# Distance-based straddle
distance_straddle = StraddleSetup(
    setup_id="distance_straddle",
    target_pct=0.50,
    stop_loss_pct=2.0,
    entry_timeindex=1000,
    strike_selection="distance", # Select by distance from spot
    strikes_away=2              # 2 strikes away from spot
)
```

#### Hedged Straddle Strategies
```python
hedged_straddle = HedgedStraddleSetup(
    setup_id="hedged_straddle",
    target_pct=0.40,            # Lower target due to hedge cost
    stop_loss_pct=1.50,         # Lower stop due to hedge protection
    entry_timeindex=1000,
    scalping_price=0.35,
    hedge_strikes_away=5        # Hedge 5 strikes OTM
)
```

#### Scalping Strategies with Re-entry
```python
# CE Scalping with re-entry
ce_scalping = CEScalpingSetup(
    setup_id="ce_scalping",
    target_pct=0.30,
    stop_loss_pct=0.80,
    entry_timeindex=1000,
    max_reentries=3,            # Maximum 3 re-entries
    reentry_gap=300,            # 300 timeindex gap between entries
    scalping_price=0.30
)

# PE Scalping with re-entry
pe_scalping = PEScalpingSetup(
    setup_id="pe_scalping",
    target_pct=0.30,
    stop_loss_pct=0.80,
    entry_timeindex=1500,
    max_reentries=2,
    reentry_gap=240,
    scalping_price=0.35
)
```

### Advanced Multi-Leg Strategies

#### Iron Condor
```python
iron_condor = IronCondorSetup(
    setup_id="iron_condor",
    target_pct=0.35,
    stop_loss_pct=1.40,
    entry_timeindex=1200,
    wing_width=10,              # Distance between short and long strikes
    short_strike_distance=5     # Distance of short strikes from spot
)
```

#### Butterfly Spreads
```python
# Call Butterfly
call_butterfly = ButterflySetup(
    setup_id="call_butterfly",
    target_pct=0.45,
    stop_loss_pct=1.20,
    entry_timeindex=1500,
    wing_distance=5,            # Distance between body and wings
    butterfly_type="CALL"       # CALL or PUT butterfly
)

# Put Butterfly
put_butterfly = ButterflySetup(
    setup_id="put_butterfly",
    target_pct=0.40,
    stop_loss_pct=1.10,
    entry_timeindex=1800,
    wing_distance=4,
    butterfly_type="PUT"
)
```

#### Vertical Spreads
```python
# Bull Call Spread
bull_call = VerticalSpreadSetup(
    setup_id="bull_call_spread",
    target_pct=0.40,
    stop_loss_pct=1.20,
    entry_timeindex=1000,
    spread_width=5,             # Strike width
    direction="BULL_CALL"       # Direction and type
)

# Bear Put Spread
bear_put = VerticalSpreadSetup(
    setup_id="bear_put_spread",
    target_pct=0.35,
    stop_loss_pct=1.00,
    entry_timeindex=1500,
    spread_width=5,
    direction="BEAR_PUT"
)
```

#### Ratio Spreads
```python
ratio_spread = RatioSpreadSetup(
    setup_id="ratio_spread",
    target_pct=0.50,
    stop_loss_pct=1.50,
    entry_timeindex=1200,
    ratio="1:2",                # 1 long, 2 short
    spread_type="CALL",         # CALL or PUT
    unlimited_risk_protection=True  # Enable stop-loss protection
)
```

### Intraday Gamma Scalping
```python
gamma_scalping = GammaScalpingSetup(
    setup_id="gamma_scalping",
    target_pct=0.25,
    stop_loss_pct=0.70,
    entry_timeindex=1000,
    delta_threshold=0.15,       # Delta threshold for rebalancing
    rebalance_frequency=60      # Rebalance every 5 minutes
)
```

## Market Regime Detection & Dynamic Adaptation

### Enabling Dynamic Management
```python
engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=1000.0,
    enable_dynamic_management=True,  # Enable regime detection
    enable_multi_symbol=True
)
```

### Market Regimes Detected
- **TRENDING_UP**: Strong upward price movement
- **TRENDING_DOWN**: Strong downward price movement
- **RANGING**: Sideways/choppy price action
- **HIGH_VOL**: High volatility periods
- **LOW_VOL**: Low volatility periods

### Regime-Specific Strategy Configurations

#### Trending Market Strategies
```python
trending_strategies = [
    # Directional scalping
    CEScalpingSetup(
        setup_id="trending_ce",
        target_pct=0.35,        # Higher targets in trends
        stop_loss_pct=0.80,     # Tighter stops
        max_reentries=3,        # More re-entries
        reentry_gap=240,        # Shorter gaps
        scalping_price=0.30     # Lower premium threshold
    ),
    
    # Momentum following
    MomentumReversalSetup(
        setup_id="trending_momentum",
        strategy_type="MOMENTUM",
        momentum_threshold=0.006,  # Lower threshold for early entry
        lookback_periods=8         # Shorter lookback for responsiveness
    )
]
```

#### Ranging Market Strategies
```python
ranging_strategies = [
    # Premium selling
    StraddleSetup(
        setup_id="ranging_straddle",
        target_pct=0.50,        # Higher targets in ranging
        stop_loss_pct=1.80,     # Wider stops
        scalping_price=0.45     # Higher premium threshold
    ),
    
    # Iron condors
    IronCondorSetup(
        setup_id="ranging_condor",
        wing_width=12,          # Wider wings for ranging
        short_strike_distance=6  # Further from spot
    )
]
```

#### High Volatility Strategies
```python
high_vol_strategies = [
    # Volatility skew exploitation
    VolatilitySkewSetup(
        setup_id="high_vol_skew",
        skew_threshold=0.025,   # Higher threshold for high vol
        min_iv_difference=0.03
    ),
    
    # Ratio spreads
    RatioSpreadSetup(
        setup_id="high_vol_ratio",
        ratio="1:2",
        unlimited_risk_protection=True
    )
]
```

#### Low Volatility Strategies
```python
low_vol_strategies = [
    # Tight premium selling
    StraddleSetup(
        setup_id="low_vol_straddle",
        target_pct=0.30,        # Lower targets
        stop_loss_pct=1.20,     # Tighter stops
        scalping_price=0.25     # Lower premium threshold
    ),
    
    # Butterflies
    ButterflySetup(
        setup_id="low_vol_butterfly",
        wing_distance=4,        # Tighter wings
        target_pct=0.35
    )
]
```

## Pattern Recognition Strategies

### Momentum and Mean Reversion
```python
# Pure momentum following
momentum_follow = MomentumReversalSetup(
    setup_id="momentum_follow",
    strategy_type="MOMENTUM",
    momentum_threshold=0.008,   # Strong momentum threshold
    lookback_periods=10,        # Short lookback for responsiveness
    velocity_smoothing=3        # Light smoothing
)

# Mean reversion after exhaustion
momentum_reversion = MomentumReversalSetup(
    setup_id="momentum_reversion",
    strategy_type="REVERSION",
    momentum_threshold=0.012,   # Higher threshold for exhaustion
    reversion_lookback=20,      # Longer lookback for reversion
    max_velocity_threshold=0.015  # Maximum velocity before reversion
)

# Adaptive switching
adaptive_momentum = MomentumReversalSetup(
    setup_id="adaptive_momentum",
    strategy_type="ADAPTIVE",  # Switches based on conditions
    momentum_threshold=0.006,
    adaptive_threshold_multiplier=1.5,
    regime_sensitivity=0.8
)
```

### Volatility Skew Strategies
```python
# Classic skew exploitation
vol_skew = VolatilitySkewSetup(
    setup_id="vol_skew",
    skew_threshold=0.025,       # Strong skew threshold
    min_iv_difference=0.03,
    skew_persistence_periods=8  # How long skew must persist
)

# Put-call skew focus
put_call_skew = VolatilitySkewSetup(
    setup_id="put_call_skew",
    skew_threshold=0.020,
    put_call_skew_focus=True,   # Focus on put-call skew
    min_put_call_iv_diff=0.025,
    skew_mean_reversion_threshold=0.015
)

# Time-based volatility patterns
time_vol_patterns = VolatilitySkewSetup(
    setup_id="time_vol_patterns",
    time_of_day_adjustment=True,  # Adjust for time effects
    morning_vol_multiplier=1.2,   # Higher vol in morning
    afternoon_vol_multiplier=0.9, # Lower vol in afternoon
    eod_vol_spike_detection=True  # Detect end-of-day spikes
)
```

### Time Decay Strategies
```python
# Classic theta acceleration
theta_acceleration = TimeDecaySetup(
    setup_id="theta_acceleration",
    theta_acceleration_time=4400,  # When theta accelerates
    high_theta_threshold=0.35,
    theta_acceleration_multiplier=2.0
)

# Intraday theta patterns
intraday_theta = TimeDecaySetup(
    setup_id="intraday_theta",
    intraday_theta_tracking=True,  # Track theta throughout day
    lunch_theta_slowdown=True,     # Account for lunch slowdown
    eod_theta_spike=True,          # End-of-day acceleration
    theta_pattern_lookback=15
)

# Expiration effects
expiration_effects = TimeDecaySetup(
    setup_id="expiration_effects",
    expiration_day_effects=True,   # Special expiration handling
    weekend_theta_adjustment=True, # Account for weekend theta
    expiration_hour_multiplier=3.0, # Final hour acceleration
    assignment_risk_management=True
)
```

## Cross-Symbol Analysis & Correlation Trading

### Correlation Analysis Setup
```python
# Enable cross-symbol correlation tracking
engine = BacktestEngine(
    data_path="5SecData",
    setups=correlation_strategies,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1500.0  # Aggregate risk limit
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
        for other_symbol, correlation in perf.correlation_with_other_symbols.items():
            print(f"{symbol} vs {other_symbol}: {correlation:.3f}")
```

### Pairs Trading Strategies
```python
# QQQ-SPY pairs trading
pairs_strategy = StraddleSetup(
    setup_id="qqq_spy_pairs",
    target_pct=0.40,
    stop_loss_pct=1.20,
    entry_timeindex=1000,
    scalping_price=0.35
)

# Divergence trading between 0DTE and 1DTE
divergence_strategy = HedgedStraddleSetup(
    setup_id="dte_divergence",
    target_pct=0.30,
    stop_loss_pct=1.00,
    hedge_strikes_away=4
)
```

### Cross-Symbol Risk Management
```python
# Configure cross-symbol risk limits
engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=800.0,           # Per-symbol daily limit
    cross_symbol_risk_limit=1500.0, # Total cross-symbol limit
    enable_multi_symbol=True
)
```

## Parameter Optimization

### Basic Parameter Optimization
```python
# Define parameter ranges
parameter_ranges = {
    'target_pct': [0.25, 0.35, 0.50, 0.75],
    'stop_loss_pct': [1.00, 1.50, 2.00, 2.50],
    'entry_timeindex': [800, 1000, 1200, 1500],
    'scalping_price': [0.25, 0.30, 0.35, 0.40]
}

# Test combinations
best_params = None
best_pnl = float('-inf')

for target, stop_loss, entry_time, scalping_price in parameter_combinations:
    strategy = StraddleSetup(
        setup_id=f"opt_{target}_{stop_loss}_{entry_time}_{scalping_price}",
        target_pct=target,
        stop_loss_pct=stop_loss,
        entry_timeindex=entry_time,
        scalping_price=scalping_price
    )
    
    engine = BacktestEngine(data_path="5SecData", setups=[strategy])
    results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
    
    if results.total_pnl > best_pnl:
        best_pnl = results.total_pnl
        best_params = {
            'target_pct': target,
            'stop_loss_pct': stop_loss,
            'entry_timeindex': entry_time,
            'scalping_price': scalping_price
        }
```

### Multi-Objective Optimization
```python
def calculate_optimization_score(results):
    """Calculate multi-objective optimization score"""
    sharpe_ratio = calculate_sharpe_ratio(results)
    profit_factor = calculate_profit_factor(results)
    max_dd_ratio = results.max_drawdown / max(abs(results.total_pnl), 1)
    
    # Weighted score
    score = (
        results.total_pnl * 0.4 +           # 40% weight on P&L
        sharpe_ratio * 100 * 0.3 +          # 30% weight on Sharpe
        profit_factor * 50 * 0.2 +          # 20% weight on profit factor
        (1 - max_dd_ratio) * 100 * 0.1      # 10% weight on drawdown control
    )
    
    return score
```

### Risk-Adjusted Optimization
```python
# Optimize for risk-adjusted returns
def optimize_risk_adjusted():
    daily_limits = [300.0, 500.0, 800.0, 1000.0]
    
    for daily_limit in daily_limits:
        engine = BacktestEngine(
            data_path="5SecData",
            setups=[strategy],
            daily_max_loss=daily_limit
        )
        
        results = engine.run_backtest("QQQ", "2025-08-13", "2025-08-15")
        
        # Calculate risk-adjusted return
        risk_adjusted_return = results.total_pnl / daily_limit
        
        print(f"Daily Limit: ${daily_limit} -> "
              f"Risk-Adjusted Return: {risk_adjusted_return:.3f}")
```

## Advanced Reporting & Analytics

### Comprehensive Report Generation
```python
from backtesting_engine.reporting import BacktestReporter

# Generate full analytics suite
reporter = BacktestReporter(results)

# Generate all reports
report_summary = reporter.generate_full_report(
    symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)

# Reports generated:
# - summary.txt: Overall performance summary
# - trades.csv: Detailed trade log
# - daily.csv: Daily performance breakdown
# - setups.csv: Strategy-specific performance
# - regime_analysis.csv: Market regime performance
# - dynamic_adjustments.csv: Parameter adjustment tracking
# - symbol_performance.csv: Multi-symbol analysis
# - pattern_analysis.csv: Pattern recognition results
# - correlation_analysis.csv: Cross-symbol correlations
# - report.html: Interactive HTML report
```

### Custom Analytics
```python
# Access detailed performance data
for setup_id, setup_perf in results.setup_performance.items():
    print(f"{setup_id}:")
    print(f"  Total P&L: ${setup_perf.total_pnl:.2f}")
    print(f"  Win Rate: {setup_perf.win_rate:.1%}")
    print(f"  Max Drawdown: ${setup_perf.max_drawdown:.2f}")
    
    # Regime-specific performance
    if setup_perf.regime_performance:
        for regime, pnl in setup_perf.regime_performance.items():
            print(f"  {regime}: ${pnl:.2f}")
    
    # Symbol-specific performance
    if setup_perf.symbol_performance:
        for symbol, pnl in setup_perf.symbol_performance.items():
            print(f"  {symbol}: ${pnl:.2f}")
```

### Performance Metrics
```python
# Calculate advanced metrics
def calculate_advanced_metrics(results):
    # Sharpe Ratio
    daily_returns = [day.daily_pnl for day in results.daily_results]
    mean_return = sum(daily_returns) / len(daily_returns)
    std_dev = (sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
    sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0
    
    # Profit Factor
    gross_profit = sum(trade.pnl for trade in results.trade_log if trade.pnl > 0)
    gross_loss = abs(sum(trade.pnl for trade in results.trade_log if trade.pnl < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Maximum Drawdown
    cumulative_pnl = 0
    peak = 0
    max_drawdown = 0
    
    for trade in results.trade_log:
        cumulative_pnl += trade.pnl
        if cumulative_pnl > peak:
            peak = cumulative_pnl
        drawdown = peak - cumulative_pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'sharpe_ratio': sharpe_ratio,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'total_return': results.total_pnl,
        'win_rate': results.win_rate
    }
```

## Best Practices

### 1. Strategy Selection
- Use **straddles and iron condors** in ranging markets
- Use **scalping and momentum strategies** in trending markets
- Use **time decay strategies** near expiration
- Use **volatility skew strategies** when IV differences are significant

### 2. Risk Management
- Set appropriate daily loss limits based on account size
- Use cross-symbol risk limits for multi-symbol trading
- Monitor correlation changes between symbols
- Implement position sizing based on volatility

### 3. Parameter Optimization
- Test parameters across different market conditions
- Use walk-forward analysis for robust optimization
- Consider transaction costs and slippage in optimization
- Optimize for risk-adjusted returns, not just total P&L

### 4. Multi-Symbol Trading
- Account for correlation changes between symbols
- Use symbol-specific parameter sets when appropriate
- Monitor cross-symbol risk exposure
- Consider time zone effects for different symbols

### 5. Pattern Recognition
- Validate patterns across different time periods
- Use multiple confirmation signals
- Account for regime changes in pattern effectiveness
- Monitor pattern degradation over time

This guide provides a comprehensive overview of the advanced features available in the options backtesting engine. For specific implementation examples, refer to the example files provided with the engine.