package com.backtesting.examples;

import com.backtesting.engine.BacktestEngine;
import com.backtesting.models.*;
import com.backtesting.strategies.*;
import com.backtesting.reporting.BacktestReporter;
import java.util.*;

/**
 * Example usage of the Java backtesting engine
 * 
 * NOTE: All concrete strategies have been removed. 
 * You'll need to implement your own strategies extending TradingSetup.
 */
public class ExampleBacktest {
    
    public static void main(String[] args) {
        System.out.println("=== Java Backtesting Engine ===");
        System.out.println("All concrete strategies have been removed.");
        System.out.println("Please implement your own strategies extending TradingSetup.");
        System.out.println();
        System.out.println("Available base class: TradingSetup");
        System.out.println("Required methods to implement:");
        System.out.println("- checkEntryCondition(int currentTimeindex)");
        System.out.println("- selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain)");
        System.out.println("- createPositions(MarketData marketData)");
        
        // Option Chain Manager demo still works
        System.out.println("\n" + "=".repeat(50));
        OptionChainExample.demonstrateOptionChainManager();
    }
    
    /**
     * Example method showing how to create and run a custom strategy
     * Uncomment and modify when you have implemented your own strategies
     */
    /*
    public static void runCustomStrategyBacktest() {
        System.out.println("=== Custom Strategy Backtest ===");
        
        // Create your custom strategy
        TradingSetup customSetup = new YourCustomStrategy(
            "Custom_Strategy",  // setup ID
            50.0,              // target P&L
            -100.0,            // stop loss P&L
            930                // entry time index (9:30 AM)
        );
        
        List<TradingSetup> setups = Arrays.asList(customSetup);
        
        // Create backtest engine
        BacktestEngine engine = new BacktestEngine("../5SecData", setups, 500.0);
        
        // Run backtest
        BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-15");
        
        // Print results
        printResults(results);
        
        // Generate detailed reports
        BacktestReporter reporter = new BacktestReporter(results);
        reporter.generateFullReport("QQQ", "2025-08-13", "2025-08-15");
    }
    */
    
    /**
     * Print overall backtest results
     */
    public static void printResults(BacktestResults results) {
        System.out.println("\n--- Overall Results ---");
        System.out.printf("Total P&L: $%.2f%n", results.getTotalPnl());
        System.out.printf("Total Trades: %d%n", results.getTotalTrades());
        System.out.printf("Win Rate: %.1f%%%n", results.getWinRate() * 100);
        System.out.printf("Max Drawdown: $%.2f%n", results.getMaxDrawdown());
        
        System.out.println("\n--- Daily Results ---");
        for (DailyResults daily : results.getDailyResults()) {
            System.out.printf("%s: P&L=$%.2f, Trades=%d, Forced Closed=%d%n",
                daily.getDate(), daily.getDailyPnl(), daily.getTradesCount(),
                daily.getPositionsForcedClosedAtJobEnd());
        }
    }
    
    /**
     * Print setup-specific performance breakdown
     */
    public static void printSetupBreakdown(BacktestResults results) {
        System.out.println("\n--- Setup Performance ---");
        for (Map.Entry<String, SetupResults> entry : results.getSetupPerformance().entrySet()) {
            SetupResults setup = entry.getValue();
            System.out.printf("%s:%n", setup.getSetupId());
            System.out.printf("  P&L: $%.2f%n", setup.getTotalPnl());
            System.out.printf("  Trades: %d%n", setup.getTotalTrades());
            System.out.printf("  Win Rate: %.1f%%%n", setup.getWinRate() * 100);
            System.out.printf("  Avg Win: $%.2f%n", setup.getAvgWin());
            System.out.printf("  Avg Loss: $%.2f%n", setup.getAvgLoss());
        }
    }
}