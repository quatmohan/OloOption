package com.backtesting.examples;

import com.backtesting.engine.BacktestEngine;
import com.backtesting.models.*;
import com.backtesting.strategies.*;
import com.backtesting.reporting.BacktestReporter;
import java.util.*;

/**
 * Example usage of the Java backtesting engine
 */
public class ExampleBacktest {
    
    public static void main(String[] args) {
        // Example 1: Simple straddle setup
        runSimpleStraddleBacktest();
        
        // Example 2: Multiple setups
        runMultipleSetupsBacktest();
        
        // Example 3: All strategies showcase
        runAllStrategiesBacktest();
        
        // Example 4: Option Chain Manager demo
        System.out.println("\n" + "=".repeat(50));
        OptionChainExample.demonstrateOptionChainManager();
    }
    
    /**
     * Example 1: Simple straddle selling strategy
     */
    public static void runSimpleStraddleBacktest() {
        System.out.println("=== Simple Straddle Backtest ===");
        
        // Create a straddle setup
        TradingSetup straddleSetup = new StraddleSetup(
            "Straddle_930",  // setup ID
            50.0,            // target P&L
            -100.0,          // stop loss P&L
            930              // entry time index (9:30 AM)
        );
        
        List<TradingSetup> setups = Arrays.asList(straddleSetup);
        
        // Create backtest engine (path relative to parent directory)
        BacktestEngine engine = new BacktestEngine("../5SecData", setups, 500.0); // $500 daily max loss
        
        // Run backtest
        BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-22");
        
        // Print results
        printResults(results);
        
        // Generate detailed reports
        BacktestReporter reporter = new BacktestReporter(results);
        reporter.generateFullReport("QQQ", "2025-08-13", "2025-08-15");
    }
    
    /**
     * Example 2: Multiple trading setups
     */
    public static void runMultipleSetupsBacktest() {
        System.out.println("\n=== Multiple Setups Backtest ===");
        
        // Create multiple setups
        List<TradingSetup> setups = Arrays.asList(
            // Morning straddle
            new StraddleSetup("Morning_Straddle", 40.0, -80.0, 930, 4150, "premium", 0.40, 2),
            
            // Afternoon straddle  
            new StraddleSetup("Afternoon_Straddle", 30.0, -60.0, 2400, 4150, "distance", 0.30, 3)
        );
        
        // Create backtest engine with higher daily limit for multiple setups (path relative to parent directory)
        BacktestEngine engine = new BacktestEngine("../5SecData", setups, 1000.0);
        
        // Run backtest
        BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-15");
        
        // Print results
        printResults(results);
        printSetupBreakdown(results);
        
        // Generate detailed reports
        BacktestReporter reporter = new BacktestReporter(results);
        reporter.generateFullReport("QQQ", "2025-08-13", "2025-08-15");
    }
    
    /**
     * Print overall backtest results
     */
    private static void printResults(BacktestResults results) {
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
    private static void printSetupBreakdown(BacktestResults results) {
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
    
    /**
     * Example 3: Showcase all available strategies
     */
    public static void runAllStrategiesBacktest() {
        System.out.println("\n=== All Strategies Showcase ===");
        
        // Create all available strategies
        List<TradingSetup> setups = Arrays.asList(
            // // Basic straddle
            // new StraddleSetup("Basic_Straddle", 40.0, -80.0, 930),
            
            // // Hedged straddle
            // new HedgedStraddleSetup("Hedged_Straddle", 60.0, -120.0, 1000),
            
            // CE scalping with re-entry
            new CEScalpingSetup("CE_Scalping", 25.0, -50.0, 100)
            
            // PE scalping with re-entry
            // new PEScalpingSetup("PE_Scalping", 25.0, -50.0, 1400)
        );
        
        // Create backtest engine with higher daily limit for multiple strategies
        BacktestEngine engine = new BacktestEngine("../5SecData", setups, 2000.0);
        
        // Run backtest
        BacktestResults results = engine.runBacktest("QQQ", "2025-08-13", "2025-08-22");
        
        // Print results
        printResults(results);
        printSetupBreakdown(results);
        
        // Generate detailed reports
        BacktestReporter reporter = new BacktestReporter(results);
        reporter.generateFullReport("QQQ", "2025-08-13", "2025-08-22");
        reporter.printQuickSummary();
    }
}