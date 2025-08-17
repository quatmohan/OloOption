# Requirements Document

## Introduction

This feature implements a comprehensive options backtesting engine specifically designed for QQQ and SPY options trading strategies. The system loads historical 5-second option chain data, supports multiple sophisticated trading strategies (straddles, hedged positions, scalping with re-entry), and provides advanced analytics and reporting capabilities for strategy evaluation.

## Requirements

### Requirement 1

**User Story:** As a quantitative trader, I want to load and parse the existing 5SecData option chain files for multiple symbols and expiration types, so that I can backtest my options trading strategies against high-resolution historical data across different underlying assets and time frames.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL read CSV files from multiple data directories: 5SecData/QQQ, 5SecData/SPY, 5SecData/QQQ 1DTE, and 5SecData/SPY 1DTE with format: timestamp_index, option_type (CE/PE), strike_price, option_price
2. WHEN loading spot data THEN it SHALL parse underlying prices from Spot/*.csv files (qqq.csv, spy.csv) to determine current spot price at each timestamp for each symbol
3. WHEN loading metadata THEN it SHALL parse .prop files with different naming conventions (2025-08-13.prop, 2025-08-13F.prop, 2025-08-13B.prop, 2025-08-13M.prop) to extract jobEndIdx and other trading session parameters
4. WHEN selecting strikes for new positions THEN it SHALL identify 10-15 strikes closest to the current spot price for strategy evaluation across all supported symbols
5. WHEN calculating P&L for existing positions THEN it SHALL directly lookup the current option price (LTP) for the specific strike prices in the position for the appropriate symbol and expiration type
6. WHEN processing different expiration types THEN it SHALL distinguish between standard expiration (QQQ, SPY) and 1DTE expiration (QQQ 1DTE, SPY 1DTE) data sets
7. WHEN handling file naming conventions THEN it SHALL support different suffixes: no suffix for QQQ, 'F' for QQQ 1DTE, 'B' for SPY, and 'M' for SPY 1DTE

### Requirement 2

**User Story:** As a trader, I want the system to efficiently structure and index the parsed option chain data across multiple symbols and expiration types, so that I can quickly access option prices by time, strike, type, symbol, and expiration during backtesting.

#### Acceptance Criteria

1. WHEN parsing option data THEN the system SHALL distinguish between CE (call) and PE (put) options across all supported symbols (QQQ, SPY, QQQ 1DTE, SPY 1DTE)
2. WHEN organizing data THEN the system SHALL create time-series structures indexed by symbol, expiration type, timestamp, and strike price
3. WHEN accessing data THEN the system SHALL provide fast lookups for option prices at specific time points for any symbol/expiration combination
4. WHEN handling missing data THEN the system SHALL gracefully skip corrupted or incomplete data points with appropriate logging and symbol identification
5. WHEN switching between symbols THEN the system SHALL maintain separate data structures for each symbol and expiration type to prevent cross-contamination
6. WHEN processing concurrent symbols THEN the system SHALL support running backtests on multiple symbols simultaneously or sequentially

### Requirement 3

**User Story:** As a strategy developer, I want to run multiple diverse trading strategies simultaneously, so that I can evaluate different approaches including straddles, hedged positions, and scalping strategies with their own parameters.

#### Acceptance Criteria

1. WHEN the engine starts THEN it SHALL support multiple strategy types: StraddleSetup, HedgedStraddleSetup, CEScalpingSetup, and PEScalpingSetup
2. WHEN processing each 5-second interval THEN it SHALL check all active setups for new position opportunities
3. WHEN a setup triggers THEN it SHALL open new positions based on the specific strategy logic (straddle, hedge, or single-leg)
4. WHEN positions exist THEN it SHALL calculate current P&L using live option prices and check for target/stop-loss hits
5. WHEN target or stop-loss is hit THEN it SHALL close the position and record the trade result with detailed exit reason

### Requirement 4

**User Story:** As a trader, I want sophisticated position management with support for complex positions including hedged straddles and mixed buy/sell legs, so that I can implement advanced trading strategies.

#### Acceptance Criteria

1. WHEN managing positions THEN the system SHALL track P&L for each individual setup separately
2. WHEN calculating P&L THEN the system SHALL apply slippage of 0.005 to both entry and exit prices
3. WHEN handling hedged positions THEN the system SHALL support mixed SELL/BUY legs within the same position
4. WHEN calculating total P&L THEN the system SHALL aggregate P&L across all active setups
5. WHEN total daily P&L hits maximum stop-loss THEN the system SHALL immediately close all open positions

### Requirement 5

**User Story:** As a scalping trader, I want strategies with re-entry capabilities, so that I can implement multiple entries throughout the trading session based on market conditions.

#### Acceptance Criteria

1. WHEN using scalping setups THEN the system SHALL support configurable maximum re-entries (max_reentries parameter)
2. WHEN re-entering positions THEN the system SHALL enforce minimum time gaps between entries (reentry_gap parameter)
3. WHEN checking re-entry conditions THEN the system SHALL prevent entries too close to the session close time
4. WHEN resetting for new trading days THEN the system SHALL reset re-entry counters and tracking variables

### Requirement 6

**User Story:** As a trader, I want comprehensive strike selection algorithms, so that I can choose optimal strikes based on either premium thresholds or distance from spot price.

#### Acceptance Criteria

1. WHEN using premium-based selection THEN the system SHALL iterate from OTM to ITM strikes and select first strike with premium >= scalping_price
2. WHEN using distance-based selection THEN the system SHALL select strikes N positions away from the current spot price
3. WHEN creating hedged positions THEN the system SHALL select hedge strikes further OTM based on hedge_strikes_away parameter
4. WHEN strikes are unavailable THEN the system SHALL handle missing strikes gracefully and skip position creation

### Requirement 7

**User Story:** As an analyst, I want comprehensive reporting and analytics capabilities, so that I can thoroughly evaluate strategy performance and make data-driven decisions.

#### Acceptance Criteria

1. WHEN generating reports THEN the system SHALL create HTML reports with interactive charts and detailed trade analysis
2. WHEN exporting data THEN the system SHALL generate CSV files for trades, daily results, and setup performance
3. WHEN displaying results THEN the system SHALL show win rates, average wins/losses, max drawdown, and exit reason analysis
4. WHEN creating visualizations THEN the system SHALL generate equity curves, daily P&L charts, and setup comparison charts

### Requirement 8

**User Story:** As an intraday trader, I want the system to handle both 0DTE and 1DTE option data across multiple symbols with proper risk management and end-of-day procedures, so that I can backtest intraday strategies without overnight exposure while utilizing different expiration data sets for strategy optimization.

#### Acceptance Criteria

1. WHEN trading with 0DTE data THEN the system SHALL ensure all positions are closed at jobEndIdx from .prop files for standard expiration data (QQQ, SPY)
2. WHEN trading with 1DTE data THEN the system SHALL use QQQ 1DTE and SPY 1DTE data sets but still close all positions at jobEndIdx on the same trading day
3. WHEN using different expiration data THEN the system SHALL allow different setup parameters for 0DTE vs 1DTE strategies while maintaining the same core position management logic
4. WHEN calculating position value THEN the system SHALL use real-time option pricing from the 5-second data for the appropriate symbol and expiration type
5. WHEN managing risk THEN the system SHALL apply intraday position limits and daily maximum loss limits per symbol or across all symbols
6. WHEN reaching job end THEN the system SHALL force close all remaining positions for each symbol/expiration combination and track forced closures in reporting, regardless of whether using 0DTE or 1DTE data

### Requirement 9

**User Story:** As a sophisticated options trader, I want to test iron condor strategies with configurable wing spreads, so that I can evaluate range-bound market strategies with limited risk and reward profiles.

#### Acceptance Criteria

1. WHEN setting up iron condors THEN the system SHALL create four-leg positions: sell call spread + sell put spread
2. WHEN selecting strikes THEN the system SHALL place short strikes equidistant from spot and long strikes at configurable wing distances
3. WHEN calculating P&L THEN the system SHALL handle complex multi-leg positions with mixed buy/sell actions
4. WHEN managing risk THEN the system SHALL support early closure based on percentage of maximum profit or loss thresholds
5. WHEN strikes are unavailable THEN the system SHALL skip iron condor creation and log the missing strikes

### Requirement 10

**User Story:** As a volatility trader, I want to implement butterfly spread strategies (both call and put butterflies), so that I can profit from low volatility scenarios with precise strike targeting.

#### Acceptance Criteria

1. WHEN creating butterfly spreads THEN the system SHALL support both call butterflies (buy-sell-sell-buy) and put butterflies
2. WHEN selecting strikes THEN the system SHALL place the body at a target strike with wings at equal distances above and below
3. WHEN calculating position value THEN the system SHALL handle the 1-2-1 ratio structure (buy 1, sell 2, buy 1)
4. WHEN managing exits THEN the system SHALL support profit-taking at percentage of maximum theoretical profit
5. WHEN the underlying moves significantly THEN the system SHALL implement stop-loss based on position delta or percentage loss

### Requirement 11

**User Story:** As a directional trader, I want to test vertical spread strategies (bull/bear call and put spreads), so that I can evaluate limited-risk directional plays with defined profit targets.

#### Acceptance Criteria

1. WHEN creating vertical spreads THEN the system SHALL support bull call spreads, bear call spreads, bull put spreads, and bear put spreads
2. WHEN selecting strikes THEN the system SHALL allow configurable strike width and direction bias
3. WHEN calculating maximum profit THEN the system SHALL determine theoretical max profit as strike width minus net debit (or net credit)
4. WHEN managing positions THEN the system SHALL support early closure at percentage of maximum profit or time-based exits
5. WHEN calculating P&L THEN the system SHALL handle the two-leg structure with proper buy/sell action tracking

### Requirement 12

**User Story:** As an intraday gamma scalping trader, I want to implement delta-neutral strategies with dynamic rebalancing, so that I can profit from intraday volatility while maintaining market neutrality and closing all positions before market close.

#### Acceptance Criteria

1. WHEN initiating intraday gamma scalping THEN the system SHALL establish delta-neutral positions using options combinations that can be managed within the trading day
2. WHEN delta changes THEN the system SHALL support configurable delta thresholds for intraday rebalancing triggers
3. WHEN rebalancing THEN the system SHALL adjust position ratios or add/remove legs to maintain delta neutrality without requiring overnight positions
4. WHEN calculating P&L THEN the system SHALL track gamma P&L from underlying movement and theta decay separately within the trading session
5. WHEN approaching market close THEN the system SHALL prioritize position closure over maintaining perfect delta neutrality

### Requirement 13

**User Story:** As an intraday volatility trader, I want to test time decay strategies using same-day expiration options, so that I can evaluate strategies that profit from rapid time decay within a single trading session.

#### Acceptance Criteria

1. WHEN creating intraday time decay positions THEN the system SHALL focus on selling high-theta options that expire the same day
2. WHEN managing time decay THEN the system SHALL calculate theta P&L acceleration as options approach expiration within the trading day
3. WHEN options approach expiration THEN the system SHALL handle rapid time decay effects and potential assignment risk
4. WHEN calculating position value THEN the system SHALL account for accelerating time decay in the final hours of trading
5. WHEN underlying moves significantly THEN the system SHALL implement stop-loss based on delta exposure or percentage loss before end-of-day closure

### Requirement 14

**User Story:** As a ratio spread trader, I want to implement unbalanced spread strategies with different ratios, so that I can test strategies that profit from specific price ranges while maintaining favorable risk-reward profiles.

#### Acceptance Criteria

1. WHEN creating ratio spreads THEN the system SHALL support configurable ratios (1:2, 1:3, 2:3, etc.) for call and put spreads
2. WHEN selecting strikes THEN the system SHALL allow different strike selections for long and short legs
3. WHEN calculating breakeven points THEN the system SHALL determine upper and lower breakeven levels for ratio positions
4. WHEN managing unlimited risk THEN the system SHALL implement stop-loss protection for the unlimited risk side
5. WHEN calculating P&L THEN the system SHALL handle the unbalanced leg structure with proper quantity tracking

### Requirement 15

**User Story:** As an intraday volatility arbitrage trader, I want to test strategies that exploit volatility skew within the same expiration cycle, so that I can evaluate intraday volatility-based trading opportunities that close before market close.

#### Acceptance Criteria

1. WHEN analyzing intraday volatility skew THEN the system SHALL support strategies that buy relatively low IV strikes and sell relatively high IV strikes within the same expiration
2. WHEN implementing skew trades THEN the system SHALL focus on put/call skew differences and strike-to-strike IV variations within the trading day
3. WHEN estimating implied volatility THEN the system SHALL calculate relative IV differences between strikes for intraday strategy selection
4. WHEN managing volatility risk THEN the system SHALL support vega-neutral position construction that can be unwound before market close
5. WHEN volatility skew normalizes THEN the system SHALL implement profit-taking based on skew convergence within the trading session

### Requirement 16

**User Story:** As a multi-asset trader, I want to run backtests across different symbols and expiration data types simultaneously, so that I can evaluate strategy performance across QQQ, SPY, and their respective 1DTE data variants for comprehensive intraday market coverage.

#### Acceptance Criteria

1. WHEN configuring backtests THEN the system SHALL support running strategies on QQQ, SPY, QQQ 1DTE, and SPY 1DTE data simultaneously or individually with all positions closed same-day
2. WHEN processing multiple symbols THEN the system SHALL maintain separate position tracking and P&L calculation for each symbol/expiration data combination
3. WHEN using different expiration data THEN the system SHALL allow different setup parameters (target_pct, stop_loss_pct, scalping_price, etc.) for 0DTE vs 1DTE data while using the same strategy logic
4. WHEN applying risk management THEN the system SHALL support both per-symbol risk limits and aggregate risk limits across all symbols and expiration data types
5. WHEN generating reports THEN the system SHALL provide performance breakdowns by symbol and expiration data type
6. WHEN comparing performance THEN the system SHALL enable cross-symbol and cross-expiration data performance analysis for intraday strategies

### Requirement 17

**User Story:** As a data-driven trader, I want to exploit pricing patterns and inefficiencies in the 5-second options price data, so that I can identify and capitalize on short-term pricing anomalies and systematic patterns using only price and time information.

#### Acceptance Criteria

1. WHEN analyzing price momentum THEN the system SHALL identify rapid option price movements over 5-second intervals that may indicate directional opportunities
2. WHEN detecting price reversals THEN the system SHALL identify options that have moved significantly and may revert based on historical price patterns
3. WHEN identifying arbitrage opportunities THEN the system SHALL detect put-call parity violations and cross-strike pricing inconsistencies using available option prices
4. WHEN analyzing price velocity THEN the system SHALL calculate rate of price change across different strikes to identify momentum or mean reversion opportunities
5. WHEN monitoring relative pricing THEN the system SHALL compare option prices across strikes and between calls/puts to identify relative value opportunities
6. WHEN detecting volatility regime changes THEN the system SHALL estimate implied volatility changes from option price movements to identify volatility trading opportunities

### Requirement 18

**User Story:** As a high-frequency options trader, I want to implement mean reversion and momentum strategies based on ultra-short-term option price movements, so that I can profit from temporary price dislocations using only price and time data.

#### Acceptance Criteria

1. WHEN detecting price reversals THEN the system SHALL identify options that have moved significantly in one direction over multiple 5-second intervals and may revert
2. WHEN implementing momentum strategies THEN the system SHALL ride short-term trends in option prices while managing time decay risk
3. WHEN analyzing cross-strike relationships THEN the system SHALL detect when strike price differentials compress or expand beyond historical norms
4. WHEN monitoring underlying-option relationships THEN the system SHALL identify when option price changes lag or lead underlying price movements for delta-based opportunities
5. WHEN calculating price velocity THEN the system SHALL measure option price change rates to identify acceleration or deceleration patterns

### Requirement 19

**User Story:** As a pattern recognition trader, I want to identify recurring intraday patterns and time-based effects in options pricing using available price and time data, so that I can develop systematic strategies based on predictable market behavior.

#### Acceptance Criteria

1. WHEN analyzing time-of-day effects THEN the system SHALL identify consistent patterns in option price movements and implied volatility at specific times using timestamp data
2. WHEN detecting expiration effects THEN the system SHALL identify how option price behavior and time decay acceleration changes as expiration approaches within the trading day
3. WHEN analyzing cross-symbol relationships THEN the system SHALL detect when QQQ and SPY options pricing relationships deviate from historical correlations
4. WHEN identifying volatility clustering THEN the system SHALL detect periods when estimated volatility from price changes tends to persist or revert
5. WHEN analyzing price patterns THEN the system SHALL identify recurring intraday price movement patterns that may indicate systematic opportunities
6. WHEN detecting regime changes THEN the system SHALL identify shifts in price volatility and trending behavior using only price and time data

### Requirement 20

**User Story:** As an adaptive algorithmic trader, I want to dynamically modify setup parameters and strategy selection based on real-time market conditions detected from price movements, so that I can optimize strategy performance as market regimes change throughout the trading day.

#### Acceptance Criteria

1. WHEN detecting high volatility periods THEN the system SHALL automatically adjust target_pct and stop_loss_pct parameters to account for increased price movement
2. WHEN identifying trending markets THEN the system SHALL favor directional strategies (vertical spreads, scalping) and reduce neutral strategies (straddles, iron condors)
3. WHEN detecting ranging markets THEN the system SHALL favor premium selling strategies (straddles, iron condors) and reduce directional strategies
4. WHEN underlying price velocity increases THEN the system SHALL tighten stop-losses and reduce position holding times to manage gamma risk
5. WHEN implied volatility (estimated from option prices) changes rapidly THEN the system SHALL adjust scalping_price thresholds and strike selection criteria
6. WHEN time-to-expiration decreases THEN the system SHALL modify target profits to account for accelerating time decay and increase position monitoring frequency
7. WHEN cross-symbol correlation breaks down THEN the system SHALL adjust risk limits and potentially suspend correlated strategies
8. WHEN recent strategy performance deteriorates THEN the system SHALL temporarily reduce position sizes or pause underperforming setups

### Requirement 21

**User Story:** As a market regime detection trader, I want the system to automatically classify current market conditions and switch between different strategy configurations, so that I can maintain optimal strategy selection as market dynamics evolve.

#### Acceptance Criteria

1. WHEN calculating market regime THEN the system SHALL classify current conditions as: trending up, trending down, high volatility, low volatility, or ranging based on recent price data
2. WHEN regime changes are detected THEN the system SHALL automatically switch to pre-configured strategy sets optimized for the new regime
3. WHEN volatility regime shifts THEN the system SHALL adjust all volatility-sensitive parameters (scalping_price, target_pct, stop_loss_pct) across active setups
4. WHEN trend strength changes THEN the system SHALL modify directional bias in strike selection and strategy weighting
5. WHEN market conditions become uncertain THEN the system SHALL reduce overall position sizes and favor more conservative strategies
6. WHEN regime detection confidence is low THEN the system SHALL maintain current strategy configuration until clearer signals emerge

### Requirement 22

**User Story:** As a strategy researcher, I want comprehensive performance analytics and pattern discovery tools, so that I can continuously identify new opportunities and optimize existing strategies based on evolving market conditions and dynamic setup performance.

#### Acceptance Criteria

1. WHEN analyzing strategy performance THEN the system SHALL calculate strategy-specific metrics (max profit, max loss, breakeven points) for each symbol, expiration type, and market regime
2. WHEN comparing strategies THEN the system SHALL provide risk-adjusted returns, Sharpe ratios, and maximum drawdown analysis across symbols and market conditions
3. WHEN evaluating market conditions THEN the system SHALL segment performance by detected volatility regimes, trending vs ranging markets, and time-of-day effects
4. WHEN generating reports THEN the system SHALL include dynamic setup performance showing how parameter adjustments affected results
5. WHEN optimizing parameters THEN the system SHALL support parameter sensitivity analysis and regime-specific optimization for each strategy type
6. WHEN analyzing adaptive performance THEN the system SHALL track how well dynamic setup changes improved or hurt overall performance compared to static setups

