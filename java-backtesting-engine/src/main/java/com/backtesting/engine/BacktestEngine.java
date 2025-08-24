package com.backtesting.engine;

import com.backtesting.data.DataLoader;
import com.backtesting.models.*;
import com.backtesting.strategies.TradingSetup;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Main orchestrator that iterates through time intervals
 */
public class BacktestEngine {
    private final DataLoader dataLoader;
    private final List<TradingSetup> setups;
    private final PositionManager positionManager;
    private final RiskManager riskManager;
    
    // Results tracking
    private final List<Trade> allTrades = new ArrayList<>();
    private final List<DailyResults> dailyResults = new ArrayList<>();
    private double cumulativePnl = 0.0;

    public BacktestEngine(String dataPath, List<TradingSetup> setups, double dailyMaxLoss) {
        this.dataLoader = new DataLoader(dataPath);
        this.setups = setups;
        this.positionManager = new PositionManager();
        this.riskManager = new RiskManager(dailyMaxLoss);
    }

    public BacktestEngine(String dataPath, List<TradingSetup> setups) {
        this(dataPath, setups, 1000.0);
    }

    /**
     * Run backtest across multiple dates
     */
    public BacktestResults runBacktest(String symbol, String startDate, String endDate) {
        List<String> availableDates = dataLoader.getAvailableDates(symbol);
        
        // Filter dates within range
        List<String> testDates = availableDates.stream()
                .filter(date -> date.compareTo(startDate) >= 0 && date.compareTo(endDate) <= 0)
                .collect(Collectors.toList());

        System.out.println("Running backtest for " + symbol + " from " + startDate + " to " + endDate);
        System.out.println("Found " + testDates.size() + " trading days: " + testDates);

        for (String date : testDates) {
            System.out.println("\nProcessing " + date + "...");
            DailyResults dailyResult = processTradingDay(symbol, date);
            if (dailyResult != null) {
                dailyResults.add(dailyResult);
                cumulativePnl += dailyResult.getDailyPnl();
            }
        }

        return generateFinalResults();
    }

    /**
     * Process a single trading day
     */
    public DailyResults processTradingDay(String symbol, String date) {
        // Load data for the day
        TradingDayData tradingDayData = dataLoader.loadTradingDay(symbol, date);
        if (tradingDayData == null) {
            System.err.println("Could not load data for " + date);
            return null;
        }

        // Reset for new day
        positionManager.resetPositions();
        riskManager.resetDailyTracking();

        // Reset daily state for all setups
        for (TradingSetup setup : setups) {
            setup.resetDailyState();
        }

        List<Trade> dailyTrades = new ArrayList<>();
        int positionsForcedClosed = 0;

        // Get all timestamps and sort them
        Set<Integer> allTimestamps = new HashSet<>(tradingDayData.getOptionData().keySet());
        allTimestamps.addAll(tradingDayData.getSpotData().keySet());
        List<Integer> sortedTimestamps = allTimestamps.stream().sorted().collect(Collectors.toList());

        System.out.println("Processing " + sortedTimestamps.size() + " time intervals...");

        for (Integer timestamp : sortedTimestamps) {
            // Skip if we don't have both option and spot data
            if (!tradingDayData.getOptionData().containsKey(timestamp) ||
                !tradingDayData.getSpotData().containsKey(timestamp)) {
                continue;
            }

            // Create market data
            Map<String, Map<Double, Double>> optionPrices = tradingDayData.getOptionData().get(timestamp);
            Set<Double> allStrikes = new HashSet<>();
            for (Map<Double, Double> strikes : optionPrices.values()) {
                allStrikes.addAll(strikes.keySet());
            }

            MarketData marketData = new MarketData(
                timestamp,
                tradingDayData.getSpotData().get(timestamp),
                optionPrices,
                new ArrayList<>(allStrikes)
            );

            // Process this time interval
            List<Trade> intervalTrades = processTimeInterval(marketData, date);
            dailyTrades.addAll(intervalTrades);

            // Check daily risk limits
            if (checkDailyRiskLimits()) {
                System.out.println("Daily risk limit hit at timestamp " + timestamp + ". Closing all positions.");
                List<Trade> emergencyTrades = positionManager.closeAllPositions(marketData, "DAILY_LIMIT", date);
                dailyTrades.addAll(emergencyTrades);
                break;
            }

            // Check if we've reached job end
            if (timestamp >= tradingDayData.getJobEndIdx()) {
                System.out.println("Reached job end index " + tradingDayData.getJobEndIdx() + ". Force closing positions.");
                List<Trade> jobEndTrades = positionManager.forceCloseAtJobEnd(
                    tradingDayData.getJobEndIdx(), marketData, date);
                dailyTrades.addAll(jobEndTrades);
                positionsForcedClosed = jobEndTrades.size();
                break;
            }
        }

        // Calculate daily results
        double dailyPnl = dailyTrades.stream().mapToDouble(Trade::getPnl).sum();
        Map<String, Double> setupPnls = new HashMap<>();
        for (TradingSetup setup : setups) {
            double setupPnl = dailyTrades.stream()
                    .filter(trade -> trade.getSetupId().equals(setup.getSetupId()))
                    .mapToDouble(Trade::getPnl)
                    .sum();
            setupPnls.put(setup.getSetupId(), setupPnl);
        }

        // Add to all trades
        allTrades.addAll(dailyTrades);

        System.out.println("Day " + date + " completed: " + dailyTrades.size() + 
                          " trades, P&L: " + String.format("%.2f", dailyPnl));

        return new DailyResults(date, dailyPnl, dailyTrades.size(), positionsForcedClosed, setupPnls);
    }

    /**
     * Process a single 5-second interval
     */
    public List<Trade> processTimeInterval(MarketData marketData, String date) {
        List<Trade> intervalTrades = new ArrayList<>();

        // 1. Check entry conditions for all setups
        for (TradingSetup setup : setups) {
            if (setup.checkEntryCondition(marketData.getTimestamp())) {
                // 2. Create new positions if entry triggered
                List<Position> newPositions = setup.createPositions(marketData);
                for (Position position : newPositions) {
                    String positionId = positionManager.addPosition(position);
                    System.out.println("📈 " + setup.getSetupId() + ": Opened at " + 
                                     marketData.getTimestamp() + ", Spot=" + 
                                     String.format("%.2f", marketData.getSpotPrice()) + 
                                     ", Strikes=" + position.getStrikes());
                }
            }
        }

        // 3. Update P&L for existing positions and check exit conditions
        List<Trade> closedTrades = positionManager.updatePositions(marketData, date);
        intervalTrades.addAll(closedTrades);

        // 4. Check time-based closures
        List<Trade> timeBasedTrades = positionManager.checkTimeBasedClosures(
            marketData.getTimestamp(), setups);
        intervalTrades.addAll(timeBasedTrades);

        return intervalTrades;
    }

    /**
     * Check if daily risk limits are breached
     */
    public boolean checkDailyRiskLimits() {
        double totalPnl = positionManager.getTotalPnl();
        return riskManager.shouldCloseAllPositions(totalPnl);
    }

    /**
     * Generate final backtest results
     */
    private BacktestResults generateFinalResults() {
        double totalPnl = allTrades.stream().mapToDouble(Trade::getPnl).sum();
        int totalTrades = allTrades.size();

        // Calculate win rate
        long winningTrades = allTrades.stream().filter(trade -> trade.getPnl() > 0).count();
        double winRate = totalTrades > 0 ? (double) winningTrades / totalTrades : 0.0;

        // Calculate max drawdown
        double maxDrawdown = calculateMaxDrawdown();

        // Calculate setup performance
        Map<String, SetupResults> setupPerformance = new HashMap<>();
        for (TradingSetup setup : setups) {
            List<Trade> setupTrades = allTrades.stream()
                    .filter(trade -> trade.getSetupId().equals(setup.getSetupId()))
                    .collect(Collectors.toList());
            
            double setupPnl = setupTrades.stream().mapToDouble(Trade::getPnl).sum();
            List<Trade> setupWins = setupTrades.stream()
                    .filter(trade -> trade.getPnl() > 0)
                    .collect(Collectors.toList());
            List<Trade> setupLosses = setupTrades.stream()
                    .filter(trade -> trade.getPnl() < 0)
                    .collect(Collectors.toList());

            setupPerformance.put(setup.getSetupId(), new SetupResults(
                setup.getSetupId(),
                setupPnl,
                setupTrades.size(),
                setupTrades.size() > 0 ? (double) setupWins.size() / setupTrades.size() : 0.0,
                setupWins.size() > 0 ? setupWins.stream().mapToDouble(Trade::getPnl).average().orElse(0.0) : 0.0,
                setupLosses.size() > 0 ? setupLosses.stream().mapToDouble(Trade::getPnl).average().orElse(0.0) : 0.0,
                0.0 // TODO: Calculate setup-specific drawdown
            ));
        }

        return new BacktestResults(
            totalPnl,
            dailyResults,
            allTrades,
            setupPerformance,
            winRate,
            maxDrawdown,
            totalTrades
        );
    }

    /**
     * Calculate maximum drawdown
     */
    private double calculateMaxDrawdown() {
        if (allTrades.isEmpty()) {
            return 0.0;
        }

        double cumulativePnl = 0.0;
        double peak = 0.0;
        double maxDrawdown = 0.0;

        for (Trade trade : allTrades) {
            cumulativePnl += trade.getPnl();
            if (cumulativePnl > peak) {
                peak = cumulativePnl;
            }

            double drawdown = peak - cumulativePnl;
            if (drawdown > maxDrawdown) {
                maxDrawdown = drawdown;
            }
        }

        return maxDrawdown;
    }
}