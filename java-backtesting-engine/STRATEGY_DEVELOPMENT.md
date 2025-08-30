# Strategy Development Guide

## Overview

All concrete strategies have been removed from the engine. You now have a clean slate to build and test your own trading strategies from scratch.

## Available Base Class

### `TradingSetup` (Abstract Base Class)

Located at: `src/main/java/com/backtesting/strategies/TradingSetup.java`

**Required Methods to Implement:**

1. **`checkEntryCondition(int currentTimeindex)`**
   - Define when to enter trades
   - Return `true` when entry conditions are met
   - `currentTimeindex` represents 5-second intervals (e.g., 930 = 9:30 AM)

2. **`selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain)`**
   - Choose which option strikes to trade
   - Return a Map: `{"CE": 580.0, "PE": 575.0}` (option type → strike price)
   - Available option types: "CE" (calls), "PE" (puts)

3. **`createPositions(MarketData marketData)`**
   - Create actual positions when entry is triggered
   - Return a List of Position objects
   - Define position type: "BUY" (long) or "SELL" (short)

## Getting Started

### 1. Use the Template

Copy and modify `TemplateStrategy.java`:

```bash
cp src/main/java/com/backtesting/strategies/TemplateStrategy.java \
   src/main/java/com/backtesting/strategies/MyStrategy.java
```

### 2. Implement Your Strategy

```java
public class MyStrategy extends TradingSetup {
    
    public MyStrategy(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, 4650, "premium", 0.40, 2);
    }

    @Override
    public boolean checkEntryCondition(int currentTimeindex) {
        // Your entry logic here
        return currentTimeindex == entryTimeindex;
    }

    @Override
    public Map<String, Double> selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain) {
        // Your strike selection logic here
        Map<String, Double> strikes = new HashMap<>();
        // ... implement logic ...
        return strikes;
    }

    @Override
    public List<Position> createPositions(MarketData marketData) {
        // Your position creation logic here
        // ... implement logic ...
        return positions;
    }
}
```

### 3. Test Your Strategy

Update `ExampleBacktest.java`:

```java
public static void runMyStrategyBacktest() {
    TradingSetup myStrategy = new MyStrategy("My_Strategy", 50.0, -100.0, 930);
    List<TradingSetup> setups = Arrays.asList(myStrategy);
    
    BacktestEngine engine = new BacktestEngine("../5SecData", setups, 500.0);
    BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-15");
    
    ExampleBacktest.printResults(results);
}
```

## Strategy Examples

### Time-Based Entry
```java
@Override
public boolean checkEntryCondition(int currentTimeindex) {
    // Enter at 9:30 AM
    return currentTimeindex == 930;
    
    // Or enter in a time window
    // return currentTimeindex >= 930 && currentTimeindex <= 1000;
}
```

### Strike Selection Patterns

**ATM (At-The-Money) Strikes:**
```java
Double atmStrike = findClosestStrike(optionChain.get("CE").keySet(), spotPrice);
selectedStrikes.put("CE", atmStrike);
```

**OTM (Out-of-The-Money) Strikes:**
```java
// For calls: strikes above spot price
List<Double> otmCalls = optionChain.get("CE").keySet().stream()
    .filter(s -> s > spotPrice)
    .sorted()
    .collect(Collectors.toList());
```

**Premium-Based Selection:**
```java
for (Map.Entry<Double, Double> entry : optionChain.get("CE").entrySet()) {
    if (entry.getValue() >= 0.40) {  // Premium >= $0.40
        selectedStrikes.put("CE", entry.getKey());
        break;
    }
}
```

### Position Types

**Short Straddle (Sell both calls and puts):**
```java
Position position = new Position(
    setupId, timestamp, entryPrices, selectedStrikes,
    1, 100, targetPct, stopLossPct,
    "SELL",  // Short position
    closeTimeindex, 0.005
);
```

**Long Straddle (Buy both calls and puts):**
```java
Position position = new Position(
    setupId, timestamp, entryPrices, selectedStrikes,
    1, 100, targetPct, stopLossPct,
    "BUY",   // Long position
    closeTimeindex, 0.005
);
```

## Build and Test

```bash
# Compile your strategy
mvn compile

# Run your backtest
mvn exec:java

# Run tests
mvn test
```

## Key Parameters

- **targetPct**: Profit target (e.g., 50.0 = $50 profit)
- **stopLossPct**: Stop loss (e.g., -100.0 = $100 loss)
- **entryTimeindex**: When to enter (930 = 9:30 AM, 1000 = 10:00 AM)
- **closeTimeindex**: Force close time (4650 = market close)
- **Position Type**: "BUY" (long) or "SELL" (short)

## Data Available

- **Spot Price**: Current underlying price
- **Option Chain**: All available strikes and their prices
- **Timestamp**: Current 5-second interval
- **Market Data**: Complete market state at each interval

## Next Steps

1. Copy `TemplateStrategy.java` to create your own strategy
2. Implement the three required methods
3. Test with small date ranges first
4. Iterate and refine your strategy logic
5. Run comprehensive backtests once satisfied

The engine handles all the complex parts (P&L calculation, risk management, reporting) - you just focus on the trading logic!