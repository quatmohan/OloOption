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

- [x] 13. Extend DataLoader for multi-symbol support
  - Add support for QQQ, SPY, QQQ 1DTE, and SPY 1DTE data loading
  - Implement file suffix handling (no suffix, F, B, M) for different symbols
  - Add symbol-specific spot data parsing (qqq.csv, spy.csv)
  - Create concurrent and sequential multi-symbol data loading capabilities
  - _Requirements: 1.1, 1.6, 1.7, 2.5, 2.6_

- [x] 14. Implement market regime detection system
  - Create MarketRegimeDetector class for real-time market analysis
  - Implement price velocity and momentum calculation from 5-second data
  - Add volatility estimation from option price movements
  - Create trend detection and market classification algorithms
  - Add time-of-day effect analysis and cross-symbol correlation tracking
  - _Requirements: 19.1, 19.2, 19.3, 19.6, 20.1_

- [x] 15. Build dynamic setup management system
  - Create DynamicSetupManager for adaptive parameter adjustment
  - Implement regime-based parameter modification (target_pct, stop_loss_pct, scalping_price)
  - Add strategy activation/deactivation based on market conditions
  - Create performance tracking for dynamic vs static parameters
  - _Requirements: 20.2, 20.3, 20.4, 20.5, 21.1, 21.2_

- [x] 16. Implement advanced multi-leg option strategies
  - Create IronCondorSetup with four-leg position management
  - Implement ButterflySetup with 1-2-1 ratio structure
  - Add VerticalSpreadSetup for directional strategies (bull/bear call/put spreads)
  - Create RatioSpreadSetup with configurable ratios and unlimited risk protection
  - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 11.1, 11.2, 14.1, 14.2_

- [x] 17. Build pattern recognition strategies
  - Implement MomentumReversalSetup for price velocity-based trading
  - Create VolatilitySkewSetup for relative IV exploitation
  - Add TimeDecaySetup optimized for accelerating theta in final trading hours
  - Implement put-call parity violation detection for arbitrage opportunities
  - _Requirements: 17.1, 17.2, 17.3, 18.1, 18.2, 15.1, 15.3_

- [x] 18. Implement intraday gamma scalping strategy
  - Create GammaScalpingSetup with delta-neutral position construction
  - Add intraday rebalancing logic based on delta thresholds
  - Implement position ratio adjustments to maintain neutrality
  - Add gamma P&L tracking separate from theta decay
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 19. Extend PositionManager for complex multi-leg positions
  - Add support for four-leg positions (iron condors) with mixed buy/sell actions
  - Implement complex P&L calculations for butterfly and ratio spreads
  - Add position-specific risk management for unlimited risk strategies
  - Create coordinated position closure for multi-leg strategies
  - _Requirements: 9.3, 10.3, 11.3, 14.3, 14.5_

- [x] 20. Update BacktestEngine for multi-symbol and dynamic processing
  - Add multi-symbol coordination and processing capabilities
  - Integrate MarketRegimeDetector and DynamicSetupManager
  - Implement regime-based strategy switching and parameter adjustment
  - Add cross-symbol correlation monitoring and risk management
  - _Requirements: 16.1, 16.2, 16.3, 20.6, 21.3, 21.4_

- [x] 21. Enhance reporting system for advanced analytics
  - Extend BacktestReporter with multi-symbol performance breakdowns
  - Add regime-specific performance analysis and visualization
  - Create dynamic adjustment impact tracking and reporting
  - Implement pattern discovery tools and cross-symbol correlation analysis
  - Add strategy-specific visualizations for complex multi-leg positions
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

- [x] 22. Add comprehensive testing for new functionality
  - Create unit tests for multi-symbol data loading and processing
  - Test market regime detection accuracy with historical data
  - Test dynamic parameter adjustment logic and performance impact
  - Test complex multi-leg strategy P&L calculations
  - Test pattern recognition strategy signal generation
  - Validate cross-symbol correlation and risk management
  - _Requirements: All_

- [x] 23. Create advanced example usage and documentation
  - Write examples for multi-symbol backtesting across all data sources
  - Document advanced strategy configurations and parameter optimization
  - Create regime-specific strategy examples and dynamic setup configurations
  - Add pattern recognition strategy examples and market condition analysis
  - Document cross-symbol analysis and correlation trading strategies
  - _Requirements: All_