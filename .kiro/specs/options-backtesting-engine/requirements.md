# Requirements Document

## Introduction

This feature implements a comprehensive options backtesting engine specifically designed for QQQ and SPY options trading strategies. The system loads historical 5-second option chain data, supports multiple sophisticated trading strategies (straddles, hedged positions, scalping with re-entry), and provides advanced analytics and reporting capabilities for strategy evaluation.

## Requirements

### Requirement 1

**User Story:** As a quantitative trader, I want to load and parse the existing 5SecData option chain files for QQQ and SPY, so that I can backtest my options trading strategies against high-resolution historical data.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL read CSV files from the 5SecData/QQQ and 5SecData/SPY directories with format: timestamp_index, option_type (CE/PE), strike_price, option_price
2. WHEN loading spot data THEN it SHALL parse underlying prices from Spot/*.csv files to determine current spot price at each timestamp
3. WHEN loading metadata THEN it SHALL parse .prop files to extract jobEndIdx and other trading session parameters
4. WHEN selecting strikes for new positions THEN it SHALL identify 10-15 strikes closest to the current spot price for strategy evaluation
5. WHEN calculating P&L for existing positions THEN it SHALL directly lookup the current option price (LTP) for the specific strike prices in the position

### Requirement 2

**User Story:** As a trader, I want the system to efficiently structure and index the parsed option chain data, so that I can quickly access option prices by time, strike, and type during backtesting.

#### Acceptance Criteria

1. WHEN parsing option data THEN the system SHALL distinguish between CE (call) and PE (put) options
2. WHEN organizing data THEN the system SHALL create time-series structures indexed by timestamp and strike price
3. WHEN accessing data THEN the system SHALL provide fast lookups for option prices at specific time points
4. WHEN handling missing data THEN the system SHALL gracefully skip corrupted or incomplete data points with appropriate logging

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

**User Story:** As an intraday trader, I want the system to handle 0DTE option positions with proper risk management and end-of-day procedures, so that I can backtest intraday strategies without overnight exposure.

#### Acceptance Criteria

1. WHEN trading 0DTE options THEN the system SHALL ensure all positions are closed at jobEndIdx from .prop files
2. WHEN calculating position value THEN the system SHALL use real-time option pricing from the 5-second data
3. WHEN managing risk THEN the system SHALL apply intraday position limits and daily maximum loss limits
4. WHEN reaching job end THEN the system SHALL force close all remaining positions and track forced closures in reporting

