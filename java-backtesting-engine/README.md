# Java Options Backtesting Engine

A comprehensive Java implementation of an options backtesting engine specifically designed for QQQ and SPY options trading strategies. This is a direct translation of the Python implementation with the same functionality and architecture.

## Features

- **Multi-Strategy Support**: Run multiple trading setups simultaneously
- **5-Second Resolution**: Process high-frequency 5-second option chain data
- **Risk Management**: Daily P&L limits and position-level stop losses
- **Strike Selection**: Premium-based and distance-based strike selection algorithms
- **Position Management**: Real-time P&L tracking with slippage modeling
- **Comprehensive Reporting**: Detailed trade logs, CSV exports, and performance metrics

## Architecture

### Core Components

- **BacktestEngine**: Main orchestrator that processes time intervals
- **DataLoader**: Parses 5SecData CSV files and spot price data
- **OptionChainManager**: Advanced caching and performance optimization for option data
- **PositionManager**: Tracks positions and calculates P&L
- **RiskManager**: Implements daily limits and risk controls
- **TradingSetup**: Abstract base for strategy implementations

### Supported Strategies

- **StraddleSetup**: Straddle selling with premium/distance-based strike selection
- **HedgedStraddleSetup**: Straddle with protective hedge positions
- **CEScalpingSetup**: Call option scalping with re-entry capability  
- **PEScalpingSetup**: Put option scalping with re-entry capability

## Quick Start

### Prerequisites

- Java 11 or higher
- Maven 3.6 or higher
- 5SecData directory with QQQ/SPY option chain files

### Build and Run

```bash
# Clone or extract the project
cd java-backtesting-engine

# Compile the project
mvn compile

# Run the example
mvn exec:java

# Or run tests
mvn test
```

### Basic Usage

```java
import com.backtesting.engine.BacktestEngine;
import com.backtesting.strategies.StraddleSetup;
import com.backtesting.strategies.TradingSetup;
import java.util.Arrays;

// Create a straddle setup
TradingSetup setup = new StraddleSetup(
    "Morning_Straddle",  // setup ID
    50.0,                // target P&L ($50)
    -100.0,              // stop loss P&L (-$100)
    930                  // entry time (9:30 AM)
);

// Create backtest engine
BacktestEngine engine = new BacktestEngine(
    "5SecData",          // data directory
    Arrays.asList(setup), // list of setups
    500.0                // daily max loss ($500)
);

// Run backtest
BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-15");

// Print results
System.out.printf("Total P&L: $%.2f%n", results.getTotalPnl());
System.out.printf("Win Rate: %.1f%%%n", results.getWinRate() * 100);
```

## Data Format

### Option Chain Data
CSV files in `5SecData/{SYMBOL}/{DATE}_BK.csv` format:
```
timestamp_index,option_type,strike_price,option_price
930,CE,580.0,2.45
930,PE,580.0,1.85
```

### Spot Price Data
CSV files in `5SecData/{SYMBOL}/Spot/{symbol}.csv` format:
```
date,timestamp,open,high,low,close,volume
2025-08-13,930,579.50,580.25,579.25,580.00,1000
```

### Metadata Files
Property files in `5SecData/{SYMBOL}/{DATE}.prop` format:
```
jobEndIdx=4660
idxEnd=4680
dte=0
```

## Strategy Configuration

### Strike Selection Methods

**Premium-Based Selection**:
```java
new StraddleSetup("setup1", 50.0, -100.0, 930, 4650, "premium", 0.40, 2)
```
- Iterates from OTM to ITM strikes
- Selects first strike with premium >= scalping_price (0.40)

**Distance-Based Selection**:
```java
new StraddleSetup("setup2", 50.0, -100.0, 930, 4650, "distance", 0.40, 3)
```
- Selects strikes N positions away from spot price
- strikes_away parameter controls distance (3 strikes away)

### Position Types

- **SELL**: Short positions (receive premium, profit when price decreases)
- **BUY**: Long positions (pay premium, profit when price increases)
- **HEDGED**: Mixed positions with both long and short legs

### Risk Management

- **Position-Level**: Individual target/stop-loss per position
- **Daily Limits**: Maximum daily loss across all setups
- **Time-Based**: Force close positions at specified times
- **Job End**: Automatic closure at market close (jobEndIdx)

## Performance Features

- **Slippage Modeling**: 0.005 slippage applied on entry and exit
- **Lot Size**: Standard 100 shares per contract
- **Real-time P&L**: Continuous position valuation
- **Multi-Setup Tracking**: Separate P&L tracking per strategy

## Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=DataLoaderTest

# Run with verbose output
mvn test -Dtest=BacktestEngineTest -X
```

## Project Structure

```
java-backtesting-engine/
├── src/main/java/com/backtesting/
│   ├── data/
│   │   └── DataLoader.java
│   ├── engine/
│   │   ├── BacktestEngine.java
│   │   ├── PositionManager.java
│   │   └── RiskManager.java
│   ├── models/
│   │   ├── TradingDayData.java
│   │   ├── MarketData.java
│   │   ├── Position.java
│   │   ├── Trade.java
│   │   ├── BacktestResults.java
│   │   ├── DailyResults.java
│   │   └── SetupResults.java
│   ├── strategies/
│   │   ├── TradingSetup.java
│   │   ├── StraddleSetup.java
│   │   └── CEScalpingSetup.java
│   └── examples/
│       └── ExampleBacktest.java
├── src/test/java/
├── pom.xml
└── README.md
```

## Comparison with Python Version

This Java implementation maintains 100% functional compatibility with the original Python version:

- **Same Architecture**: Identical component structure and responsibilities
- **Same Algorithms**: Strike selection and P&L calculation logic
- **Same Data Format**: Compatible with existing 5SecData files
- **Same Results**: Produces identical backtest results

### Key Differences

- **Type Safety**: Java's static typing provides compile-time error checking
- **Performance**: Generally faster execution for large datasets
- **Memory Management**: Automatic garbage collection
- **Enterprise Ready**: Better suited for production trading systems

## Contributing

1. Follow Java coding conventions
2. Add unit tests for new features
3. Update documentation for API changes
4. Ensure compatibility with existing data formats

## License

This project is provided as-is for educational and research purposes.