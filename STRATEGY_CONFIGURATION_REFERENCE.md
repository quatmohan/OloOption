# Strategy Configuration Reference

## Table of Contents
1. [Traditional Strategies](#traditional-strategies)
2. [Advanced Multi-Leg Strategies](#advanced-multi-leg-strategies)
3. [Pattern Recognition Strategies](#pattern-recognition-strategies)
4. [Dynamic Strategy Management](#dynamic-strategy-management)
5. [Parameter Optimization Guidelines](#parameter-optimization-guidelines)
6. [Risk Management Configuration](#risk-management-configuration)

## Traditional Strategies

### StraddleSetup
Sells both call and put options at the same strike price.

#### Parameters
```python
StraddleSetup(
    setup_id: str,                    # Unique identifier
    target_pct: float,                # Target profit in dollars
    stop_loss_pct: float,             # Stop loss in dollars
    entry_timeindex: int,             # Entry time (5-second intervals)
    close_timeindex: int = 4650,      # Force close time
    strike_selection: str = "premium", # "premium" or "distance"
    scalping_price: float = 0.40,     # Minimum premium for "premium" selection
    strikes_away: int = 2             # Strikes away for "distance" selection
)
```

#### Configuration Examples
```python
# Conservative straddle
conservative_straddle = StraddleSetup(
    setup_id="conservative_straddle",
    target_pct=0.30,        # $30 target
    stop_loss_pct=1.20,     # $120 stop loss
    entry_timeindex=1000,
    strike_selection="premium",
    scalping_price=0.50     # Higher premium requirement
)

# Aggressive straddle
aggressive_straddle = StraddleSetup(
    setup_id="aggressive_straddle",
    target_pct=0.75,        # $75 target
    stop_loss_pct=2.50,     # $250 stop loss
    entry_timeindex=800,    # Earlier entry
    strike_selection="distance",
    strikes_away=1          # Closer to ATM
)

# Late-day straddle
late_day_straddle = StraddleSetup(
    setup_id="late_day_straddle",
    target_pct=0.25,        # Lower target for time decay
    stop_loss_pct=0.75,     # Tighter stop
    entry_timeindex=4000,   # Late entry for theta acceleration
    close_timeindex=4600,   # Close before EOD
    scalping_price=0.25     # Lower premium for late day
)
```

#### Best Use Cases
- **Ranging markets**: When underlying is expected to stay within a range
- **Low volatility periods**: When IV is relatively low
- **Pre-earnings**: When high IV is expected to crush post-announcement
- **Time decay acceleration**: Near expiration for rapid theta decay

### HedgedStraddleSetup
Sells straddle and buys protective options further OTM.

#### Parameters
```python
HedgedStraddleSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "premium",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    hedge_strikes_away: int = 5       # Distance of hedge strikes from main strikes
)
```

#### Configuration Examples
```python
# Conservative hedged straddle
conservative_hedged = HedgedStraddleSetup(
    setup_id="conservative_hedged",
    target_pct=0.25,        # Lower target due to hedge cost
    stop_loss_pct=1.00,     # Lower stop due to hedge protection
    entry_timeindex=1000,
    scalping_price=0.40,
    hedge_strikes_away=6    # Wider hedge for more protection
)

# Aggressive hedged straddle
aggressive_hedged = HedgedStraddleSetup(
    setup_id="aggressive_hedged",
    target_pct=0.50,        # Higher target
    stop_loss_pct=1.80,     # Wider stop
    entry_timeindex=1200,
    scalping_price=0.35,
    hedge_strikes_away=4    # Closer hedge for lower cost
)

# Tight hedged straddle
tight_hedged = HedgedStraddleSetup(
    setup_id="tight_hedged",
    target_pct=0.20,        # Very low target
    stop_loss_pct=0.60,     # Very tight stop
    entry_timeindex=1500,
    scalping_price=0.30,
    hedge_strikes_away=3    # Very close hedge
)
```

#### Best Use Cases
- **Uncertain market direction**: When direction is unclear but movement expected
- **High volatility periods**: When large moves are possible
- **Risk management**: When maximum loss needs to be limited
- **Overnight positions**: When positions might be held longer (though engine closes intraday)

### CEScalpingSetup / PEScalpingSetup
Single-leg call or put selling with re-entry capabilities.

#### Parameters
```python
CEScalpingSetup(  # or PEScalpingSetup
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "premium",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    max_reentries: int = 3,           # Maximum re-entries allowed
    reentry_gap: int = 300            # Minimum gap between entries (timeindex)
)
```

#### Configuration Examples
```python
# Conservative CE scalping
conservative_ce = CEScalpingSetup(
    setup_id="conservative_ce",
    target_pct=0.20,        # Low target for quick profits
    stop_loss_pct=0.60,     # Tight stop
    entry_timeindex=1000,
    max_reentries=1,        # Limited re-entries
    reentry_gap=600,        # Long gap between entries
    scalping_price=0.40
)

# Aggressive PE scalping
aggressive_pe = PEScalpingSetup(
    setup_id="aggressive_pe",
    target_pct=0.40,        # Higher target
    stop_loss_pct=1.00,     # Wider stop
    entry_timeindex=1500,
    max_reentries=4,        # More re-entries
    reentry_gap=180,        # Shorter gap
    scalping_price=0.25     # Lower premium threshold
)

# Trend-following scalping
trend_ce = CEScalpingSetup(
    setup_id="trend_ce",
    target_pct=0.35,
    stop_loss_pct=0.70,
    entry_timeindex=800,    # Early entry to catch trends
    max_reentries=5,        # Many re-entries for trending
    reentry_gap=120,        # Very short gap
    scalping_price=0.20     # Very low premium for more entries
)
```

#### Best Use Cases
- **Trending markets**: CE for uptrends, PE for downtrends
- **High volatility**: When frequent re-entries are profitable
- **Momentum trading**: Following strong directional moves
- **Scalping strategies**: Quick in-and-out trades

## Advanced Multi-Leg Strategies

### IronCondorSetup
Four-leg strategy: sell call spread + sell put spread.

#### Parameters
```python
IronCondorSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "distance",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    wing_width: int = 10,             # Distance between short and long strikes
    short_strike_distance: int = 5    # Distance of short strikes from spot
)
```

#### Configuration Examples
```python
# Wide iron condor (ranging market)
wide_condor = IronCondorSetup(
    setup_id="wide_condor",
    target_pct=0.40,        # Higher target for wider spread
    stop_loss_pct=1.60,     # Wider stop
    entry_timeindex=1000,
    wing_width=15,          # Wide wings
    short_strike_distance=8  # Far from spot
)

# Tight iron condor (low volatility)
tight_condor = IronCondorSetup(
    setup_id="tight_condor",
    target_pct=0.25,        # Lower target for tighter spread
    stop_loss_pct=1.00,     # Tighter stop
    entry_timeindex=1200,
    wing_width=8,           # Narrow wings
    short_strike_distance=4  # Close to spot
)

# Balanced iron condor
balanced_condor = IronCondorSetup(
    setup_id="balanced_condor",
    target_pct=0.35,
    stop_loss_pct=1.40,
    entry_timeindex=1500,
    wing_width=12,
    short_strike_distance=6
)
```

#### Best Use Cases
- **Range-bound markets**: When underlying expected to stay within range
- **Low to moderate volatility**: When large moves are unlikely
- **Time decay strategies**: Benefiting from theta decay on short options
- **Defined risk trading**: When maximum loss is predetermined

### ButterflySetup
Three-strike strategy with 1-2-1 ratio (buy-sell-sell-buy).

#### Parameters
```python
ButterflySetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "distance",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    wing_distance: int = 5,           # Distance between body and wings
    butterfly_type: str = "CALL"      # "CALL" or "PUT"
)
```

#### Configuration Examples
```python
# Wide call butterfly
wide_call_butterfly = ButterflySetup(
    setup_id="wide_call_butterfly",
    target_pct=0.50,        # Higher target for wider spread
    stop_loss_pct=1.50,
    entry_timeindex=1000,
    wing_distance=8,        # Wide wings
    butterfly_type="CALL"
)

# Tight put butterfly
tight_put_butterfly = ButterflySetup(
    setup_id="tight_put_butterfly",
    target_pct=0.30,        # Lower target for tighter spread
    stop_loss_pct=0.90,
    entry_timeindex=1500,
    wing_distance=4,        # Tight wings
    butterfly_type="PUT"
)

# ATM butterfly
atm_butterfly = ButterflySetup(
    setup_id="atm_butterfly",
    target_pct=0.40,
    stop_loss_pct=1.20,
    entry_timeindex=1200,
    wing_distance=6,
    butterfly_type="CALL",
    strikes_away=0          # At-the-money body
)
```

#### Best Use Cases
- **Low volatility**: When underlying expected to stay near specific price
- **Earnings plays**: When expecting minimal movement post-announcement
- **Time decay**: Benefiting from theta decay on short options
- **Precise targeting**: When specific price target is expected

### VerticalSpreadSetup
Two-leg directional strategies (bull/bear call/put spreads).

#### Parameters
```python
VerticalSpreadSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "distance",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    spread_width: int = 5,            # Width between strikes
    direction: str = "BULL_CALL"      # Direction and type
)
```

#### Direction Options
- `"BULL_CALL"`: Bullish using calls (buy lower, sell higher)
- `"BEAR_CALL"`: Bearish using calls (sell lower, buy higher)
- `"BULL_PUT"`: Bullish using puts (sell higher, buy lower)
- `"BEAR_PUT"`: Bearish using puts (buy higher, sell lower)

#### Configuration Examples
```python
# Aggressive bull call spread
aggressive_bull_call = VerticalSpreadSetup(
    setup_id="aggressive_bull_call",
    target_pct=0.60,        # High target for directional play
    stop_loss_pct=1.80,     # Wide stop for trend following
    entry_timeindex=800,    # Early entry
    spread_width=8,         # Wide spread for more profit potential
    direction="BULL_CALL"
)

# Conservative bear put spread
conservative_bear_put = VerticalSpreadSetup(
    setup_id="conservative_bear_put",
    target_pct=0.25,        # Conservative target
    stop_loss_pct=0.75,     # Tight stop
    entry_timeindex=1500,
    spread_width=4,         # Narrow spread
    direction="BEAR_PUT"
)

# Balanced bull put spread
balanced_bull_put = VerticalSpreadSetup(
    setup_id="balanced_bull_put",
    target_pct=0.40,
    stop_loss_pct=1.20,
    entry_timeindex=1200,
    spread_width=6,
    direction="BULL_PUT"
)
```

#### Best Use Cases
- **Directional bias**: When clear directional view exists
- **Limited risk**: When maximum loss needs to be defined
- **Moderate volatility**: When some movement expected but not extreme
- **Cost reduction**: When outright option purchase is too expensive

### RatioSpreadSetup
Unbalanced spreads with configurable ratios.

#### Parameters
```python
RatioSpreadSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "distance",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    ratio: str = "1:2",               # Ratio of long to short
    spread_type: str = "CALL",        # "CALL" or "PUT"
    unlimited_risk_protection: bool = True  # Enable stop-loss protection
)
```

#### Ratio Options
- `"1:2"`: 1 long, 2 short (most common)
- `"1:3"`: 1 long, 3 short (more aggressive)
- `"2:3"`: 2 long, 3 short (less aggressive)

#### Configuration Examples
```python
# Conservative 1:2 call ratio
conservative_ratio = RatioSpreadSetup(
    setup_id="conservative_ratio",
    target_pct=0.35,
    stop_loss_pct=1.20,     # Important for unlimited risk
    entry_timeindex=1000,
    ratio="1:2",
    spread_type="CALL",
    unlimited_risk_protection=True
)

# Aggressive 1:3 put ratio
aggressive_ratio = RatioSpreadSetup(
    setup_id="aggressive_ratio",
    target_pct=0.60,
    stop_loss_pct=2.00,
    entry_timeindex=1200,
    ratio="1:3",
    spread_type="PUT",
    unlimited_risk_protection=True
)

# Balanced 2:3 call ratio
balanced_ratio = RatioSpreadSetup(
    setup_id="balanced_ratio",
    target_pct=0.45,
    stop_loss_pct=1.50,
    entry_timeindex=1500,
    ratio="2:3",
    spread_type="CALL",
    unlimited_risk_protection=True
)
```

#### Best Use Cases
- **Volatility trading**: When expecting specific volatility levels
- **Income generation**: When seeking premium income with some risk
- **Range trading**: When expecting underlying to stay within range
- **Advanced strategies**: When sophisticated risk/reward profile needed

### GammaScalpingSetup
Delta-neutral positions with dynamic rebalancing.

#### Parameters
```python
GammaScalpingSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "distance",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    delta_threshold: float = 0.15,    # Delta threshold for rebalancing
    rebalance_frequency: int = 60     # Rebalance frequency (timeindex)
)
```

#### Configuration Examples
```python
# Conservative gamma scalping
conservative_gamma = GammaScalpingSetup(
    setup_id="conservative_gamma",
    target_pct=0.20,        # Lower target for delta-neutral
    stop_loss_pct=0.60,     # Tight stop
    entry_timeindex=1000,
    delta_threshold=0.10,   # Tight delta management
    rebalance_frequency=30  # Frequent rebalancing
)

# Aggressive gamma scalping
aggressive_gamma = GammaScalpingSetup(
    setup_id="aggressive_gamma",
    target_pct=0.40,        # Higher target
    stop_loss_pct=1.00,     # Wider stop
    entry_timeindex=1200,
    delta_threshold=0.20,   # Wider delta bands
    rebalance_frequency=120 # Less frequent rebalancing
)

# High-frequency gamma scalping
hf_gamma = GammaScalpingSetup(
    setup_id="hf_gamma",
    target_pct=0.15,        # Very low target
    stop_loss_pct=0.45,     # Very tight stop
    entry_timeindex=800,
    delta_threshold=0.05,   # Very tight delta
    rebalance_frequency=15  # Very frequent rebalancing
)
```

#### Best Use Cases
- **High volatility**: When underlying is moving significantly
- **Market neutral**: When no directional bias exists
- **Intraday trading**: When positions will be closed same day
- **Volatility harvesting**: When seeking to profit from movement regardless of direction

## Pattern Recognition Strategies

### MomentumReversalSetup
Strategies based on price velocity and momentum detection.

#### Parameters
```python
MomentumReversalSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "premium",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    strategy_type: str = "MOMENTUM",  # "MOMENTUM", "REVERSION", "ADAPTIVE"
    momentum_threshold: float = 0.007, # Momentum detection threshold
    lookback_periods: int = 12,       # Periods for momentum calculation
    velocity_smoothing: int = 5       # Smoothing for velocity calculation
)
```

#### Strategy Types
- `"MOMENTUM"`: Follow momentum direction
- `"REVERSION"`: Trade against momentum (mean reversion)
- `"ADAPTIVE"`: Switch between momentum and reversion based on conditions

#### Configuration Examples
```python
# Pure momentum following
momentum_follow = MomentumReversalSetup(
    setup_id="momentum_follow",
    target_pct=0.40,
    stop_loss_pct=1.00,
    entry_timeindex=1000,
    strategy_type="MOMENTUM",
    momentum_threshold=0.008,   # Strong momentum required
    lookback_periods=8,         # Short lookback for responsiveness
    velocity_smoothing=3        # Light smoothing
)

# Mean reversion after exhaustion
momentum_reversion = MomentumReversalSetup(
    setup_id="momentum_reversion",
    target_pct=0.35,
    stop_loss_pct=0.85,
    entry_timeindex=1500,
    strategy_type="REVERSION",
    momentum_threshold=0.012,   # High threshold for exhaustion
    lookback_periods=20,        # Longer lookback for reversion
    velocity_smoothing=8        # More smoothing for reversion
)

# Adaptive momentum/reversion
adaptive_momentum = MomentumReversalSetup(
    setup_id="adaptive_momentum",
    target_pct=0.38,
    stop_loss_pct=0.95,
    entry_timeindex=1200,
    strategy_type="ADAPTIVE",
    momentum_threshold=0.006,   # Lower threshold for adaptive
    lookback_periods=15,        # Medium lookback
    velocity_smoothing=5        # Medium smoothing
)
```

#### Best Use Cases
- **Trending markets**: Momentum following in strong trends
- **Reversal points**: Mean reversion at exhaustion points
- **Volatile markets**: Adaptive switching based on conditions
- **Intraday patterns**: Capturing short-term momentum shifts

### VolatilitySkewSetup
Strategies to exploit relative implied volatility differences.

#### Parameters
```python
VolatilitySkewSetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "premium",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    skew_threshold: float = 0.020,    # Minimum skew for entry
    min_iv_difference: float = 0.025, # Minimum IV difference required
    skew_persistence_periods: int = 8  # How long skew must persist
)
```

#### Configuration Examples
```python
# Conservative skew trading
conservative_skew = VolatilitySkewSetup(
    setup_id="conservative_skew",
    target_pct=0.25,
    stop_loss_pct=0.75,
    entry_timeindex=1000,
    skew_threshold=0.030,       # High threshold for conservative
    min_iv_difference=0.035,    # Large IV difference required
    skew_persistence_periods=12 # Long persistence required
)

# Aggressive skew trading
aggressive_skew = VolatilitySkewSetup(
    setup_id="aggressive_skew",
    target_pct=0.45,
    stop_loss_pct=1.20,
    entry_timeindex=1200,
    skew_threshold=0.015,       # Low threshold for aggressive
    min_iv_difference=0.020,    # Smaller IV difference
    skew_persistence_periods=5  # Short persistence
)

# Opportunistic skew trading
opportunistic_skew = VolatilitySkewSetup(
    setup_id="opportunistic_skew",
    target_pct=0.35,
    stop_loss_pct=0.90,
    entry_timeindex=1500,
    skew_threshold=0.018,
    min_iv_difference=0.025,
    skew_persistence_periods=6
)
```

#### Best Use Cases
- **IV distortions**: When relative IV between strikes is abnormal
- **Event trading**: Around earnings or other events affecting skew
- **Arbitrage opportunities**: When skew creates pricing inefficiencies
- **Volatility trading**: When trading volatility rather than direction

### TimeDecaySetup
Strategies optimized for accelerating theta decay.

#### Parameters
```python
TimeDecaySetup(
    setup_id: str,
    target_pct: float,
    stop_loss_pct: float,
    entry_timeindex: int,
    close_timeindex: int = 4650,
    strike_selection: str = "premium",
    scalping_price: float = 0.40,
    strikes_away: int = 2,
    theta_acceleration_time: int = 4400,  # When theta accelerates
    high_theta_threshold: float = 0.35,   # High theta threshold
    theta_acceleration_multiplier: float = 2.0  # Theta acceleration factor
)
```

#### Configuration Examples
```python
# Early theta acceleration
early_theta = TimeDecaySetup(
    setup_id="early_theta",
    target_pct=0.40,
    stop_loss_pct=1.20,
    entry_timeindex=1000,
    theta_acceleration_time=4200,  # Earlier acceleration
    high_theta_threshold=0.30,
    theta_acceleration_multiplier=2.5
)

# Late theta acceleration
late_theta = TimeDecaySetup(
    setup_id="late_theta",
    target_pct=0.25,        # Lower target for late entry
    stop_loss_pct=0.75,     # Tighter stop
    entry_timeindex=4000,   # Very late entry
    theta_acceleration_time=4500,  # Very late acceleration
    high_theta_threshold=0.40,     # High threshold for late
    theta_acceleration_multiplier=3.0  # High acceleration
)

# Balanced theta strategy
balanced_theta = TimeDecaySetup(
    setup_id="balanced_theta",
    target_pct=0.35,
    stop_loss_pct=1.00,
    entry_timeindex=1500,
    theta_acceleration_time=4300,
    high_theta_threshold=0.35,
    theta_acceleration_multiplier=2.2
)
```

#### Best Use Cases
- **Expiration day**: When theta decay is accelerating rapidly
- **Time premium harvesting**: When seeking to capture time decay
- **Low volatility**: When movement is minimal and theta dominates
- **End-of-day trading**: When theta acceleration is most pronounced

## Dynamic Strategy Management

### Enabling Dynamic Management
```python
engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=1000.0,
    enable_dynamic_management=True,  # Enable regime detection and adaptation
    enable_multi_symbol=True
)
```

### Regime-Specific Parameter Adjustments

The dynamic management system automatically adjusts strategy parameters based on detected market regimes:

#### Trending Markets
- **Increase** target_pct for directional strategies
- **Decrease** stop_loss_pct for tighter risk management
- **Reduce** scalping_price for more entries
- **Favor** momentum and scalping strategies
- **Reduce** premium selling strategies

#### Ranging Markets
- **Increase** target_pct for premium selling
- **Increase** stop_loss_pct for wider stops
- **Increase** scalping_price for higher premium
- **Favor** straddles, iron condors, butterflies
- **Reduce** directional strategies

#### High Volatility
- **Adjust** all parameters for increased movement
- **Increase** stop_loss_pct for wider stops
- **Favor** volatility skew and ratio strategies
- **Increase** rebalancing frequency for gamma strategies

#### Low Volatility
- **Decrease** target_pct for realistic expectations
- **Decrease** stop_loss_pct for tighter management
- **Favor** time decay and butterfly strategies
- **Reduce** momentum strategies

### Custom Dynamic Rules
```python
# Example of custom dynamic adjustment logic
def custom_regime_adjustment(strategy, regime, confidence):
    """Custom logic for regime-based parameter adjustment"""
    
    if regime == "TRENDING_UP" and confidence > 0.7:
        if isinstance(strategy, CEScalpingSetup):
            strategy.target_pct *= 1.3      # Increase target in uptrend
            strategy.max_reentries += 1     # Allow more re-entries
            strategy.reentry_gap *= 0.8     # Shorter gaps
    
    elif regime == "HIGH_VOL" and confidence > 0.8:
        if isinstance(strategy, StraddleSetup):
            strategy.stop_loss_pct *= 1.4   # Wider stops in high vol
            strategy.scalping_price *= 1.2  # Higher premium requirement
    
    elif regime == "LOW_VOL" and confidence > 0.6:
        if isinstance(strategy, ButterflySetup):
            strategy.target_pct *= 0.8      # Lower target in low vol
            strategy.wing_distance *= 0.9   # Tighter wings
    
    return strategy
```

## Parameter Optimization Guidelines

### Single Parameter Optimization
```python
# Example: Optimizing target_pct for straddle
target_values = [0.25, 0.35, 0.50, 0.75, 1.00]
best_target = None
best_performance = float('-inf')

for target in target_values:
    strategy = StraddleSetup(
        setup_id=f"straddle_target_{target}",
        target_pct=target,
        stop_loss_pct=2.0,  # Keep other params constant
        entry_timeindex=1000,
        scalping_price=0.40
    )
    
    # Run backtest and evaluate
    results = run_backtest(strategy)
    performance_score = calculate_performance_score(results)
    
    if performance_score > best_performance:
        best_performance = performance_score
        best_target = target
```

### Multi-Parameter Optimization
```python
# Example: Grid search optimization
parameter_grid = {
    'target_pct': [0.25, 0.50, 0.75],
    'stop_loss_pct': [1.0, 2.0, 3.0],
    'scalping_price': [0.30, 0.40, 0.50]
}

best_params = None
best_score = float('-inf')

for target in parameter_grid['target_pct']:
    for stop_loss in parameter_grid['stop_loss_pct']:
        for scalping_price in parameter_grid['scalping_price']:
            
            strategy = StraddleSetup(
                setup_id=f"opt_{target}_{stop_loss}_{scalping_price}",
                target_pct=target,
                stop_loss_pct=stop_loss,
                entry_timeindex=1000,
                scalping_price=scalping_price
            )
            
            results = run_backtest(strategy)
            score = calculate_multi_objective_score(results)
            
            if score > best_score:
                best_score = score
                best_params = {
                    'target_pct': target,
                    'stop_loss_pct': stop_loss,
                    'scalping_price': scalping_price
                }
```

### Performance Scoring Functions
```python
def calculate_performance_score(results):
    """Simple performance score based on total P&L"""
    return results.total_pnl

def calculate_risk_adjusted_score(results):
    """Risk-adjusted performance score"""
    if results.max_drawdown == 0:
        return results.total_pnl
    return results.total_pnl / results.max_drawdown

def calculate_multi_objective_score(results):
    """Multi-objective optimization score"""
    pnl_score = results.total_pnl * 0.4
    win_rate_score = results.win_rate * 100 * 0.3
    drawdown_score = (1 - results.max_drawdown / max(abs(results.total_pnl), 1)) * 100 * 0.2
    trade_count_score = min(results.total_trades / 10, 10) * 0.1
    
    return pnl_score + win_rate_score + drawdown_score + trade_count_score

def calculate_sharpe_ratio(results):
    """Calculate Sharpe ratio for optimization"""
    if not results.daily_results or len(results.daily_results) < 2:
        return 0.0
    
    daily_returns = [day.daily_pnl for day in results.daily_results]
    mean_return = sum(daily_returns) / len(daily_returns)
    
    if len(daily_returns) < 2:
        return 0.0
    
    variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std_dev = variance ** 0.5
    
    return mean_return / std_dev if std_dev > 0 else 0.0
```

## Risk Management Configuration

### Daily Risk Limits
```python
# Conservative risk management
conservative_engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=300.0,       # Low daily limit
    enable_dynamic_management=True
)

# Moderate risk management
moderate_engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=800.0,       # Moderate daily limit
    enable_dynamic_management=True
)

# Aggressive risk management
aggressive_engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=1500.0,      # High daily limit
    enable_dynamic_management=True
)
```

### Cross-Symbol Risk Management
```python
# Multi-symbol risk configuration
multi_symbol_engine = BacktestEngine(
    data_path="5SecData",
    setups=strategies,
    daily_max_loss=500.0,           # Per-symbol daily limit
    enable_multi_symbol=True,
    cross_symbol_risk_limit=1200.0  # Total cross-symbol limit
)
```

### Position-Level Risk Management
```python
# Strategy with tight risk controls
tight_risk_strategy = StraddleSetup(
    setup_id="tight_risk_straddle",
    target_pct=0.25,        # Low target
    stop_loss_pct=0.75,     # Tight stop (3:1 risk/reward)
    entry_timeindex=1000,
    scalping_price=0.40
)

# Strategy with loose risk controls
loose_risk_strategy = StraddleSetup(
    setup_id="loose_risk_straddle",
    target_pct=1.00,        # High target
    stop_loss_pct=2.00,     # Loose stop (2:1 risk/reward)
    entry_timeindex=1000,
    scalping_price=0.30
)

# Balanced risk strategy
balanced_risk_strategy = StraddleSetup(
    setup_id="balanced_risk_straddle",
    target_pct=0.50,        # Medium target
    stop_loss_pct=1.50,     # Medium stop (3:1 risk/reward)
    entry_timeindex=1000,
    scalping_price=0.35
)
```

### Risk-Reward Ratios
Common risk-reward ratios and their applications:

- **1:1 Ratio**: `target_pct = 0.50, stop_loss_pct = 0.50`
  - High win rate required (>50%)
  - Good for high-probability strategies
  
- **1:2 Ratio**: `target_pct = 0.50, stop_loss_pct = 1.00`
  - Moderate win rate required (>33%)
  - Balanced approach
  
- **1:3 Ratio**: `target_pct = 0.50, stop_loss_pct = 1.50`
  - Lower win rate acceptable (>25%)
  - Good for trend-following strategies
  
- **2:1 Ratio**: `target_pct = 1.00, stop_loss_pct = 0.50`
  - Very high win rate required (>67%)
  - Good for mean reversion strategies

This reference provides comprehensive guidance for configuring all available strategies in the options backtesting engine. Use these configurations as starting points and optimize based on your specific market conditions and risk tolerance.