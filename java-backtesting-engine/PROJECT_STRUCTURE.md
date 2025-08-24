# Java Options Backtesting Engine - Project Structure

## Directory Layout

```
java-backtesting-engine/
├── src/
│   ├── main/
│   │   └── java/
│   │       └── com/
│   │           └── backtesting/
│   │               ├── data/
│   │               │   └── DataLoader.java              # CSV file parsing and data loading
│   │               ├── engine/
│   │               │   ├── BacktestEngine.java          # Main orchestrator
│   │               │   ├── PositionManager.java         # Position tracking and P&L
│   │               │   └── RiskManager.java             # Risk controls and limits
│   │               ├── models/
│   │               │   ├── BacktestResults.java         # Final results container
│   │               │   ├── DailyResults.java            # Single day results
│   │               │   ├── MarketData.java              # Market data at timestamp
│   │               │   ├── Position.java                # Individual position
│   │               │   ├── SetupResults.java            # Setup performance metrics
│   │               │   ├── Trade.java                   # Completed trade record
│   │               │   └── TradingDayData.java          # Full day data container
│   │               ├── strategies/
│   │               │   ├── TradingSetup.java            # Abstract strategy base
│   │               │   ├── StraddleSetup.java           # Straddle selling strategy
│   │               │   └── CEScalpingSetup.java         # Call scalping strategy
│   │               └── examples/
│   │                   └── ExampleBacktest.java         # Usage examples
│   └── test/
│       └── java/
│           └── com/
│               └── backtesting/
│                   ├── data/
│                   │   └── DataLoaderTest.java          # DataLoader unit tests
│                   └── engine/
│                       └── BacktestEngineTest.java      # BacktestEngine unit tests
├── pom.xml                                              # Maven build configuration
├── build.sh                                             # Build script
├── README.md                                            # Main documentation
└── PROJECT_STRUCTURE.md                                 # This file
```

## Component Relationships

### Data Flow
```
5SecData Files → DataLoader → TradingDayData → BacktestEngine → MarketData → TradingSetup → Position → PositionManager → Trade → BacktestResults
```

### Core Components

#### 1. Data Layer (`com.backtesting.data`)
- **DataLoader**: Parses CSV files, loads spot prices, handles metadata
- Converts raw data into structured Java objects
- Provides efficient data access methods

#### 2. Engine Layer (`com.backtesting.engine`)
- **BacktestEngine**: Main orchestrator, processes time intervals
- **PositionManager**: Tracks positions, calculates P&L, handles closures
- **RiskManager**: Implements daily limits and risk controls

#### 3. Models Layer (`com.backtesting.models`)
- **Data Containers**: TradingDayData, MarketData, Position, Trade
- **Results**: BacktestResults, DailyResults, SetupResults
- Immutable data structures with clear interfaces

#### 4. Strategies Layer (`com.backtesting.strategies`)
- **TradingSetup**: Abstract base class for all strategies
- **Concrete Strategies**: StraddleSetup, CEScalpingSetup, etc.
- Strategy-specific logic for entry/exit conditions and strike selection

#### 5. Examples Layer (`com.backtesting.examples`)
- **ExampleBacktest**: Demonstrates usage patterns
- Shows how to configure and run different strategies

## Key Design Patterns

### 1. Strategy Pattern
- `TradingSetup` abstract base class
- Concrete implementations for different trading strategies
- Allows easy addition of new strategies without modifying core engine

### 2. Builder Pattern (Implicit)
- Complex objects like `Position` and `MarketData` use constructor parameters
- Clear parameter ordering and validation

### 3. Observer Pattern (Implicit)
- `PositionManager` tracks position state changes
- `RiskManager` monitors P&L levels

### 4. Template Method Pattern
- `BacktestEngine.processTimeInterval()` defines the algorithm structure
- Strategy-specific behavior implemented in `TradingSetup` subclasses

## Data Models Hierarchy

```
BacktestResults
├── List<DailyResults>
├── List<Trade>
└── Map<String, SetupResults>

TradingDayData
├── Map<Integer, Double> spotData
├── Map<Integer, Map<String, Map<Double, Double>>> optionData
└── Map<String, Object> metadata

Position
├── Map<String, Double> entryPrices
├── Map<String, Double> strikes
└── P&L tracking fields
```

## Threading and Concurrency

- **Single-threaded design**: Current implementation processes sequentially
- **Thread-safe potential**: Models are immutable, engine state is contained
- **Future enhancement**: Could be parallelized by trading day or setup

## Memory Management

- **Efficient data structures**: Uses HashMap and ArrayList for O(1) access
- **Garbage collection friendly**: Immutable objects, clear lifecycle
- **Memory considerations**: Large datasets may require streaming for very long backtests

## Extension Points

### Adding New Strategies
1. Extend `TradingSetup` abstract class
2. Implement required methods: `checkEntryCondition()`, `selectStrikes()`, `createPositions()`
3. Add to setup list in backtest configuration

### Adding New Data Sources
1. Extend or modify `DataLoader` class
2. Implement new parsing methods for different file formats
3. Ensure compatibility with existing `TradingDayData` structure

### Adding New Risk Controls
1. Extend `RiskManager` class
2. Add new limit checking methods
3. Integrate with `BacktestEngine` processing loop

## Testing Strategy

### Unit Tests
- **DataLoaderTest**: Tests file parsing and data access
- **BacktestEngineTest**: Tests core engine functionality
- **Strategy Tests**: Individual strategy logic validation

### Integration Tests
- End-to-end backtesting with sample data
- Multi-setup coordination testing
- Risk management trigger validation

### Performance Tests
- Large dataset processing benchmarks
- Memory usage profiling
- Execution time optimization

## Build and Deployment

### Maven Configuration
- **Java 11**: Minimum required version
- **JUnit 5**: Testing framework
- **Maven plugins**: Compiler, Surefire, Exec

### Build Process
1. `mvn clean` - Clean previous builds
2. `mvn compile` - Compile source code
3. `mvn test` - Run unit tests
4. `mvn package` - Create JAR file
5. `mvn exec:java` - Run examples

### Deployment Options
- **Standalone JAR**: Self-contained executable
- **Library JAR**: For integration into larger systems
- **Docker container**: For containerized deployment