# Advanced Options Backtesting Engine - Examples & Documentation

## Overview

This repository contains comprehensive examples and documentation for the advanced options backtesting engine. The engine supports sophisticated intraday options trading strategies across multiple symbols (QQQ, SPY, QQQ 1DTE, SPY 1DTE) with advanced features including market regime detection, dynamic parameter adaptation, pattern recognition, and cross-symbol analysis.

## 📁 File Structure

### Example Files
- **`example_backtest.py`** - Basic usage examples and getting started guide
- **`example_advanced_multi_symbol_strategies.py`** - Comprehensive multi-symbol backtesting examples
- **`example_regime_specific_strategies.py`** - Market regime detection and adaptive strategies
- **`example_advanced_pattern_recognition.py`** - Pattern recognition and market condition analysis
- **`example_parameter_optimization.py`** - Systematic parameter optimization techniques

### Documentation Files
- **`ADVANCED_USAGE_GUIDE.md`** - Comprehensive usage guide for all advanced features
- **`STRATEGY_CONFIGURATION_REFERENCE.md`** - Complete strategy configuration reference
- **`CROSS_SYMBOL_ANALYSIS_GUIDE.md`** - Cross-symbol analysis and correlation trading guide
- **`README_ADVANCED_EXAMPLES.md`** - This file - overview and quick start guide

## 🚀 Quick Start

### 1. Basic Multi-Symbol Backtest
```python
from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup

# Create strategy
strategy = StraddleSetup(
    setup_id="multi_symbol_straddle",
    target_pct=0.50,
    stop_loss_pct=2.0,
    entry_timeindex=1000,
    scalping_price=0.40
)

# Configure engine
engine = BacktestEngine(
    data_path="5SecData",
    setups=[strategy],
    enable_multi_symbol=True,
    enable_dynamic_management=True
)

# Run backtest
results = engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)

print(f"Total P&L: ${results.total_pnl:.2f}")
print(f"Win Rate: {results.win_rate:.1%}")
```

### 2. Run Examples
```bash
# Start with basic example
python example_backtest.py

# Multi-symbol strategies
python example_advanced_multi_symbol_strategies.py

# Regime-specific strategies
python example_regime_specific_strategies.py

# Pattern recognition
python example_advanced_pattern_recognition.py

# Parameter optimization
python example_parameter_optimization.py
```

## 📊 Supported Strategies

### Traditional Strategies
- **StraddleSetup** - Basic straddle selling
- **HedgedStraddleSetup** - Straddle with protective hedges
- **CEScalpingSetup** - Call scalping with re-entry
- **PEScalpingSetup** - Put scalping with re-entry

### Advanced Multi-Leg Strategies
- **IronCondorSetup** - Four-leg range-bound strategy
- **ButterflySetup** - Three-strike low volatility strategy
- **VerticalSpreadSetup** - Directional two-leg spreads
- **RatioSpreadSetup** - Unbalanced spreads with configurable ratios
- **GammaScalpingSetup** - Delta-neutral with dynamic rebalancing

### Pattern Recognition Strategies
- **MomentumReversalSetup** - Momentum and mean reversion patterns
- **VolatilitySkewSetup** - Relative IV exploitation
- **TimeDecaySetup** - Theta acceleration strategies

## 🎯 Key Features

### Multi-Symbol Support
- **QQQ**: NASDAQ-100 ETF options
- **SPY**: S&P 500 ETF options
- **QQQ 1DTE**: 1-day-to-expiration QQQ options
- **SPY 1DTE**: 1-day-to-expiration SPY options

### Market Regime Detection
- **TRENDING_UP/DOWN**: Strong directional movement
- **RANGING**: Sideways price action
- **HIGH_VOL/LOW_VOL**: Volatility-based regimes

### Dynamic Adaptation
- Automatic parameter adjustment based on market conditions
- Strategy activation/deactivation based on regime suitability
- Real-time performance tracking and optimization

### Advanced Analytics
- Cross-symbol correlation analysis
- Regime-specific performance breakdown
- Pattern discovery and validation
- Multi-objective parameter optimization

## 📈 Example Use Cases

### 1. Basic Usage
```python
# Run example_backtest.py
python example_backtest.py
```
**Features demonstrated:**
- Basic strategy setup and configuration
- Single symbol backtesting
- Simple reporting and analysis
- Getting started with the engine

### 2. Comprehensive Multi-Symbol Analysis
```python
# Run example_advanced_multi_symbol_strategies.py
python example_advanced_multi_symbol_strategies.py
```
**Features demonstrated:**
- All supported symbols and strategies
- Symbol-specific optimization
- Cross-symbol correlation analysis
- Performance comparison across symbols

### 3. Market Regime Adaptation
```python
# Run example_regime_specific_strategies.py
python example_regime_specific_strategies.py
```
**Features demonstrated:**
- Trending market strategies
- Ranging market strategies
- High/low volatility strategies
- Dynamic regime adaptation

### 4. Pattern Recognition Trading
```python
# Run example_advanced_pattern_recognition.py
python example_advanced_pattern_recognition.py
```
**Features demonstrated:**
- Momentum and mean reversion patterns
- Volatility skew exploitation
- Time decay acceleration patterns
- Cross-pattern confirmation strategies

### 5. Systematic Optimization
```python
# Run example_parameter_optimization.py
python example_parameter_optimization.py
```
**Features demonstrated:**
- Single and multi-parameter optimization
- Risk-adjusted optimization
- Multi-objective scoring
- Optimized portfolio construction

## 🔧 Configuration Examples

### Conservative Setup
```python
conservative_strategy = StraddleSetup(
    setup_id="conservative",
    target_pct=0.30,        # Low target
    stop_loss_pct=1.20,     # Tight stop
    scalping_price=0.50     # High premium requirement
)

conservative_engine = BacktestEngine(
    data_path="5SecData",
    setups=[conservative_strategy],
    daily_max_loss=300.0,   # Low daily limit
    enable_dynamic_management=True
)
```

### Aggressive Setup
```python
aggressive_strategy = StraddleSetup(
    setup_id="aggressive",
    target_pct=0.75,        # High target
    stop_loss_pct=2.50,     # Wide stop
    scalping_price=0.25     # Low premium requirement
)

aggressive_engine = BacktestEngine(
    data_path="5SecData",
    setups=[aggressive_strategy],
    daily_max_loss=1500.0,  # High daily limit
    enable_multi_symbol=True,
    cross_symbol_risk_limit=3000.0
)
```

### Regime-Adaptive Setup
```python
adaptive_strategies = [
    # Trending market strategy
    MomentumReversalSetup(
        setup_id="adaptive_momentum",
        strategy_type="ADAPTIVE",
        momentum_threshold=0.006
    ),
    
    # Ranging market strategy
    IronCondorSetup(
        setup_id="adaptive_condor",
        wing_width=12,
        short_strike_distance=6
    )
]

adaptive_engine = BacktestEngine(
    data_path="5SecData",
    setups=adaptive_strategies,
    enable_dynamic_management=True,  # Enable regime adaptation
    enable_multi_symbol=True
)
```

## 📊 Performance Analysis

### Basic Performance Metrics
```python
from backtesting_engine.reporting import BacktestReporter

reporter = BacktestReporter(results)

# Quick summary
reporter.print_quick_summary()

# Recent trades
reporter.print_recent_trades(10)

# Full report with analytics
report = reporter.generate_full_report(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

### Advanced Analytics
```python
# Symbol performance breakdown
for symbol, perf in results.symbol_performance.items():
    print(f"{symbol}: ${perf.total_pnl:.2f} P&L, {perf.win_rate:.1%} win rate")
    
    # Correlations with other symbols
    for other_symbol, correlation in perf.correlation_with_other_symbols.items():
        print(f"  vs {other_symbol}: {correlation:.3f} correlation")

# Regime performance analysis
for regime, regime_perf in results.regime_performance.items():
    print(f"{regime}: ${regime_perf.total_pnl:.2f} P&L, {regime_perf.win_rate:.1%} win rate")

# Dynamic adjustment impact
if results.dynamic_adjustment_performance:
    dap = results.dynamic_adjustment_performance
    print(f"Dynamic adjustments: {dap.total_adjustments}")
    print(f"Improvement over static: ${dap.static_vs_dynamic_comparison:.2f}")
```

## 🎛️ Parameter Optimization

### Basic Optimization
```python
# Define parameter ranges
parameter_ranges = {
    'target_pct': [0.25, 0.35, 0.50, 0.75],
    'stop_loss_pct': [1.0, 1.5, 2.0, 2.5],
    'scalping_price': [0.30, 0.35, 0.40, 0.45]
}

# Test combinations and find best parameters
best_params = optimize_parameters(parameter_ranges)
print(f"Best parameters: {best_params}")
```

### Multi-Objective Optimization
```python
def calculate_optimization_score(results):
    """Multi-objective optimization score"""
    return (
        results.total_pnl * 0.4 +                    # 40% P&L weight
        calculate_sharpe_ratio(results) * 100 * 0.3 + # 30% Sharpe weight
        results.win_rate * 100 * 0.2 +               # 20% win rate weight
        (1 - results.max_drawdown / max(abs(results.total_pnl), 1)) * 100 * 0.1  # 10% drawdown weight
    )
```

## 🔗 Cross-Symbol Analysis

### Correlation Analysis
```python
# Enable cross-symbol correlation tracking
engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1500.0
)

results = engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)

# Analyze correlations
for symbol, perf in results.symbol_performance.items():
    for other_symbol, correlation in perf.correlation_with_other_symbols.items():
        strength = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.4 else "Weak"
        print(f"{symbol} vs {other_symbol}: {correlation:.3f} ({strength})")
```

### Pairs Trading
```python
# Create complementary strategies for pairs trading
pairs_strategies = [
    CEScalpingSetup(setup_id="pairs_qqq_long", ...),  # Long QQQ bias
    PEScalpingSetup(setup_id="pairs_spy_short", ...)  # Short SPY bias
]

pairs_results = engine.run_multi_symbol_backtest(
    symbols=["QQQ", "SPY"],
    start_date="2025-08-13",
    end_date="2025-08-15"
)
```

## 📚 Documentation Reference

### Complete Guides
1. **[ADVANCED_USAGE_GUIDE.md](ADVANCED_USAGE_GUIDE.md)** - Comprehensive usage guide
   - Multi-symbol backtesting setup
   - Advanced strategy configurations
   - Market regime detection
   - Pattern recognition strategies
   - Cross-symbol analysis
   - Parameter optimization
   - Advanced reporting

2. **[STRATEGY_CONFIGURATION_REFERENCE.md](STRATEGY_CONFIGURATION_REFERENCE.md)** - Strategy reference
   - All strategy types and parameters
   - Configuration examples
   - Best use cases
   - Dynamic management
   - Risk management
   - Optimization guidelines

3. **[CROSS_SYMBOL_ANALYSIS_GUIDE.md](CROSS_SYMBOL_ANALYSIS_GUIDE.md)** - Cross-symbol analysis
   - Correlation analysis
   - Pairs trading strategies
   - Risk management
   - Performance analysis
   - Advanced techniques

### Quick Reference
- **Supported Symbols**: QQQ, SPY, QQQ 1DTE, SPY 1DTE
- **Strategy Types**: 12+ different strategy implementations
- **Market Regimes**: TRENDING_UP/DOWN, RANGING, HIGH_VOL/LOW_VOL
- **Risk Management**: Daily limits, cross-symbol limits, correlation-based adjustments
- **Reporting**: HTML reports, CSV exports, advanced analytics

## 🏃‍♂️ Getting Started

1. **Start with basic example**:
   ```bash
   python example_backtest.py
   ```

2. **Explore advanced features**:
   ```bash
   python example_advanced_multi_symbol_strategies.py
   python example_regime_specific_strategies.py
   ```

3. **Dive into pattern recognition**:
   ```bash
   python example_advanced_pattern_recognition.py
   ```

4. **Optimize your strategies**:
   ```bash
   python example_parameter_optimization.py
   ```

5. **Read the comprehensive guides**:
   - Start with `ADVANCED_USAGE_GUIDE.md` for overview
   - Use `STRATEGY_CONFIGURATION_REFERENCE.md` for specific configurations
   - Explore `CROSS_SYMBOL_ANALYSIS_GUIDE.md` for multi-symbol trading

## 🎯 Best Practices

### Strategy Selection
- Use **straddles and iron condors** in ranging markets
- Use **scalping and momentum strategies** in trending markets
- Use **time decay strategies** near expiration
- Use **volatility skew strategies** when IV differences are significant

### Risk Management
- Set appropriate daily loss limits based on account size
- Use cross-symbol risk limits for multi-symbol trading
- Monitor correlation changes between symbols
- Implement position sizing based on volatility

### Parameter Optimization
- Test parameters across different market conditions
- Use walk-forward analysis for robust optimization
- Consider transaction costs and slippage
- Optimize for risk-adjusted returns, not just total P&L

### Multi-Symbol Trading
- Account for correlation changes between symbols
- Use symbol-specific parameter sets when appropriate
- Monitor cross-symbol risk exposure
- Consider time zone effects for different symbols

## 🔧 Troubleshooting

### Common Issues
1. **Data Loading**: Ensure 5SecData directory structure is correct
2. **Strategy Configuration**: Check parameter ranges and types
3. **Multi-Symbol Setup**: Verify enable_multi_symbol=True
4. **Dynamic Management**: Confirm enable_dynamic_management=True for regime features

### Performance Tips
1. **Start Small**: Begin with single symbol, single strategy
2. **Incremental Complexity**: Add features gradually
3. **Monitor Memory**: Large multi-symbol backtests use more memory
4. **Optimize Parameters**: Use systematic optimization rather than guessing

## 📞 Support

For questions about the advanced examples and documentation:

1. **Check the documentation files** for comprehensive guides
2. **Run the example files** to see working implementations
3. **Review the strategy configuration reference** for parameter details
4. **Examine the cross-symbol analysis guide** for multi-symbol trading

The examples and documentation provide comprehensive coverage of all advanced features in the options backtesting engine. Start with the basic examples and gradually explore the more advanced capabilities as you become familiar with the system.