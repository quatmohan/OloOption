# Implementation Plan

- [x] 1. Set up project structure and core data models
  - Create directory structure for the backtesting engine
  - Implement core data classes: TradingDayData, MarketData, Position, BacktestResults
  - Define abstract TradingSetup base class with strike selection methods
  - _Requirements: 1.1, 2.1_

- [x] 2. Implement DataLoader for parsing 5SecData files
  - Create DataLoader class to read CSV files from 5SecData directory
  - Parse option data format: timestamp_index, option_type (CE/PE), strike_price, option_price
  - Parse spot data from Spot/*.csv files with OHLC format
  - Load metadata from .prop files (jobEndIdx, idxEnd, dte)
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement efficient option chain data structures
  - Create indexed data structures for fast option price lookups
  - Implement strike selection near spot price (10-15 strikes)
  - Build time-series option chain access for P&L calculations
  - Add data validation and missing price handling
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Create PositionManager for P&L tracking
  - Implement position creation and tracking
  - Calculate P&L with lot size (100) and slippage (0.005)
  - Handle selling P&L: (entry_price - current_price) * quantity * lot_size
  - Handle buying P&L: (current_price - entry_price) * quantity * lot_size
  - Implement target and stop-loss checking
  - _Requirements: 4.1, 4.2_

- [x] 5. Implement strike selection algorithms
  - Create premium-based strike selection (iterate OTM to ITM, select if premium >= scalping_price)
  - Create distance-based strike selection (N strikes away from spot)
  - For CE options: iterate from OTM (e.g., 590) to spot (580) for premium-based
  - For PE options: iterate from OTM (e.g., 570) to spot (580) for premium-based
  - _Requirements: 3.1, 3.2_

- [x] 6. Create concrete TradingSetup implementations
  - Implement StraddleSetup with premium-based and distance-based strike selection
  - Add entry condition checking based on timeindex
  - Implement position creation with selected strikes
  - Add time-based force close logic
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 7. Implement RiskManager for daily limits
  - Create daily P&L monitoring across all setups
  - Implement daily maximum loss limit checking
  - Add emergency position closure when daily max SL hit
  - Coordinate with PositionManager for mass position closure
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 8. Build BacktestEngine main orchestrator
  - Implement multi-date file processing (iterate through available dates)
  - Create 5-second interval processing loop
  - Coordinate entry condition checking across all setups
  - Handle position creation when entry conditions met
  - Update P&L for all existing positions each interval
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 9. Implement end-of-day processing
  - Add jobEndIdx detection and force position closure
  - Calculate daily P&L and trade statistics
  - Reset positions between trading days
  - Update cumulative statistics (total P&L, win rate, max drawdown)
  - _Requirements: 4.3, 4.4_

- [x] 10. Create results tracking and reporting
  - Implement trade logging with entry/exit details
  - Calculate performance metrics per setup
  - Generate daily and overall backtest results
  - Track positions forced closed at jobEndIdx
  - _Requirements: 4.4_

- [x] 11. Implement advanced strategy types with re-entry capabilities
  - Create CEScalpingSetup with re-entry logic and state tracking
  - Create PEScalpingSetup with configurable re-entry parameters
  - Implement HedgedStraddleSetup with hedge strike placement
  - Add daily state reset functionality for all strategies
  - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3_

- [x] 12. Build comprehensive reporting and analytics system
  - Implement BacktestReporter with multiple output formats
  - Create HTMLReporter with interactive charts and visualizations
  - Add CSV export functionality for trades, daily results, and setup performance
  - Generate equity curves, daily P&L charts, and setup comparison visualizations
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 13. Add comprehensive testing
  - Create unit tests for DataLoader with sample 5SecData files
  - Test strike selection algorithms with various market conditions
  - Test P&L calculations with different position types and slippage
  - Test multi-day backtesting with risk management
  - Test re-entry logic for scalping strategies
  - _Requirements: All_

- [x] 14. Create example usage and documentation
  - Write example scripts showing how to set up and run backtests
  - Document strike selection strategies and their use cases
  - Create sample trading setups (straddle, hedged, scalping examples)
  - Add configuration examples for different testing scenarios
  - _Requirements: All_