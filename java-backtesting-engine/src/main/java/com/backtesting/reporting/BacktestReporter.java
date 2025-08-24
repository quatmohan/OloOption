package com.backtesting.reporting;

import com.backtesting.models.*;
import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Advanced reporting and analytics for backtest results
 */
public class BacktestReporter {
    private final BacktestResults results;
    private final String reportDir;

    public BacktestReporter(BacktestResults results) {
        this.results = results;
        this.reportDir = "backtest_reports";
        ensureReportDir();
    }

    private void ensureReportDir() {
        try {
            Files.createDirectories(Paths.get(reportDir));
        } catch (IOException e) {
            System.err.println("Error creating report directory: " + e.getMessage());
        }
    }

    /**
     * Generate comprehensive report and save to files
     */
    public String generateFullReport(String symbol, String startDate, String endDate) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String reportPrefix = String.format("%s_%s_to_%s_%s", symbol, startDate, endDate, timestamp);

        // Generate console summary
        String summary = generateSummaryReport(symbol, startDate, endDate);

        // Export detailed data to CSV files
        exportTradesCsv(reportPrefix + "_trades.csv");
        exportDailyResultsCsv(reportPrefix + "_daily.csv");
        exportSetupPerformanceCsv(reportPrefix + "_setups.csv");

        // Save summary to text file
        String summaryFile = Paths.get(reportDir, reportPrefix + "_summary.txt").toString();
        try (PrintWriter writer = new PrintWriter(summaryFile)) {
            writer.print(summary);
        } catch (IOException e) {
            System.err.println("Error writing summary file: " + e.getMessage());
        }

        System.out.println("\n📊 Reports saved to " + reportDir + "/ directory:");
        System.out.println("   - " + reportPrefix + "_summary.txt");
        System.out.println("   - " + reportPrefix + "_trades.csv");
        System.out.println("   - " + reportPrefix + "_daily.csv");
        System.out.println("   - " + reportPrefix + "_setups.csv");

        return summary;
    }

    /**
     * Generate formatted summary report
     */
    private String generateSummaryReport(String symbol, String startDate, String endDate) {
        StringBuilder sb = new StringBuilder();
        
        sb.append("=".repeat(80)).append("\n");
        sb.append(String.format("OPTIONS BACKTESTING REPORT - %s%n", symbol));
        sb.append(String.format("Period: %s to %s%n", startDate, endDate));
        sb.append(String.format("Generated: %s%n", LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))));
        sb.append("=".repeat(80)).append("\n");

        // Overall Performance
        sb.append("\n📈 OVERALL PERFORMANCE\n");
        sb.append("-".repeat(40)).append("\n");
        sb.append(String.format("Total P&L:           $%,10.2f%n", results.getTotalPnl()));
        sb.append(String.format("Total Trades:        %,10d%n", results.getTotalTrades()));
        sb.append(String.format("Win Rate:            %10.1f%%%n", results.getWinRate() * 100));
        sb.append(String.format("Max Drawdown:        $%,10.2f%n", results.getMaxDrawdown()));

        if (results.getTotalTrades() > 0) {
            double avgTrade = results.getTotalPnl() / results.getTotalTrades();
            sb.append(String.format("Average Trade:       $%,10.2f%n", avgTrade));
        }

        // Daily Performance
        sb.append("\n📅 DAILY PERFORMANCE\n");
        sb.append("-".repeat(40)).append("\n");
        sb.append(String.format("%-12s %-10s %-8s %-14s%n", "Date", "P&L", "Trades", "Forced Closes"));
        sb.append("-".repeat(44)).append("\n");

        for (DailyResults daily : results.getDailyResults()) {
            sb.append(String.format("%-12s $%8.2f %6d %12d%n", 
                daily.getDate(), daily.getDailyPnl(), daily.getTradesCount(), 
                daily.getPositionsForcedClosedAtJobEnd()));
        }

        // Setup Performance
        sb.append("\n🎯 SETUP PERFORMANCE\n");
        sb.append("-".repeat(40)).append("\n");
        sb.append(String.format("%-15s %-10s %-8s %-10s %-10s %-10s%n", 
            "Setup ID", "P&L", "Trades", "Win Rate", "Avg Win", "Avg Loss"));
        sb.append("-".repeat(73)).append("\n");

        for (Map.Entry<String, SetupResults> entry : results.getSetupPerformance().entrySet()) {
            SetupResults perf = entry.getValue();
            String avgWinStr = perf.getAvgWin() > 0 ? String.format("$%.2f", perf.getAvgWin()) : "N/A";
            String avgLossStr = perf.getAvgLoss() < 0 ? String.format("$%.2f", perf.getAvgLoss()) : "N/A";
            
            sb.append(String.format("%-15s $%8.2f %6d %8.1f%% %9s %9s%n",
                perf.getSetupId(), perf.getTotalPnl(), perf.getTotalTrades(), 
                perf.getWinRate() * 100, avgWinStr, avgLossStr));
        }

        // Trade Statistics
        sb.append("\n📊 TRADE STATISTICS\n");
        sb.append("-".repeat(40)).append("\n");

        List<Trade> winningTrades = results.getTradeLog().stream()
                .filter(t -> t.getPnl() > 0)
                .collect(Collectors.toList());
        List<Trade> losingTrades = results.getTradeLog().stream()
                .filter(t -> t.getPnl() < 0)
                .collect(Collectors.toList());

        sb.append(String.format("Winning Trades:      %10d%n", winningTrades.size()));
        sb.append(String.format("Losing Trades:       %10d%n", losingTrades.size()));

        if (!winningTrades.isEmpty()) {
            double avgWin = winningTrades.stream().mapToDouble(Trade::getPnl).average().orElse(0.0);
            double maxWin = winningTrades.stream().mapToDouble(Trade::getPnl).max().orElse(0.0);
            sb.append(String.format("Average Win:         $%10.2f%n", avgWin));
            sb.append(String.format("Largest Win:         $%10.2f%n", maxWin));
        }

        if (!losingTrades.isEmpty()) {
            double avgLoss = losingTrades.stream().mapToDouble(Trade::getPnl).average().orElse(0.0);
            double maxLoss = losingTrades.stream().mapToDouble(Trade::getPnl).min().orElse(0.0);
            sb.append(String.format("Average Loss:        $%10.2f%n", avgLoss));
            sb.append(String.format("Largest Loss:        $%10.2f%n", maxLoss));
        }

        // Exit Reason Analysis
        sb.append("\n🚪 EXIT REASON ANALYSIS\n");
        sb.append("-".repeat(40)).append("\n");

        Map<String, Long> exitReasons = results.getTradeLog().stream()
                .collect(Collectors.groupingBy(Trade::getExitReason, Collectors.counting()));

        for (Map.Entry<String, Long> entry : exitReasons.entrySet()) {
            long count = entry.getValue();
            double pct = results.getTotalTrades() > 0 ? (double) count / results.getTotalTrades() * 100 : 0;
            sb.append(String.format("%-15s %6d (%5.1f%%)%n", entry.getKey(), count, pct));
        }

        return sb.toString();
    }

    /**
     * Export detailed trade log to CSV
     */
    private void exportTradesCsv(String filename) {
        Path filepath = Paths.get(reportDir, filename);
        
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(filepath))) {
            // Write header
            writer.println("trade_id,setup_id,date,entry_time,exit_time,duration,exit_reason," +
                          "ce_strike,pe_strike,ce_entry,pe_entry,ce_exit,pe_exit,total_pnl,quantity");

            // Write trade data
            int tradeId = 1;
            for (Trade trade : results.getTradeLog()) {
                String ceStrike = "N/A", peStrike = "N/A";
                double ceEntry = 0.0, peEntry = 0.0, ceExit = 0.0, peExit = 0.0;

                // Parse strikes and prices
                for (Map.Entry<String, Double> entry : trade.getStrikes().entrySet()) {
                    String key = entry.getKey();
                    if (key.contains("CE")) {
                        ceStrike = entry.getValue().toString();
                    } else if (key.contains("PE")) {
                        peStrike = entry.getValue().toString();
                    }
                }

                // Parse entry and exit prices
                for (Map.Entry<String, Double> entry : trade.getEntryPrices().entrySet()) {
                    String key = entry.getKey();
                    if (key.contains("CE")) {
                        ceEntry = entry.getValue();
                        ceExit = trade.getExitPrices().getOrDefault(key, 0.0);
                    } else if (key.contains("PE")) {
                        peEntry = entry.getValue();
                        peExit = trade.getExitPrices().getOrDefault(key, 0.0);
                    }
                }

                writer.printf("%d,%s,%s,%d,%d,%d,%s,%s,%s,%.3f,%.3f,%.3f,%.3f,%.2f,%d%n",
                    tradeId++, trade.getSetupId(), trade.getDate(),
                    trade.getEntryTimeindex(), trade.getExitTimeindex(),
                    trade.getExitTimeindex() - trade.getEntryTimeindex(),
                    trade.getExitReason(), ceStrike, peStrike,
                    ceEntry, peEntry, ceExit, peExit, trade.getPnl(), trade.getQuantity());
            }
        } catch (IOException e) {
            System.err.println("Error writing trades CSV: " + e.getMessage());
        }
    }

    /**
     * Export daily results to CSV
     */
    private void exportDailyResultsCsv(String filename) {
        Path filepath = Paths.get(reportDir, filename);
        
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(filepath))) {
            writer.println("date,daily_pnl,trades_count,positions_forced_closed");

            for (DailyResults daily : results.getDailyResults()) {
                writer.printf("%s,%.2f,%d,%d%n",
                    daily.getDate(), daily.getDailyPnl(), daily.getTradesCount(),
                    daily.getPositionsForcedClosedAtJobEnd());
            }
        } catch (IOException e) {
            System.err.println("Error writing daily results CSV: " + e.getMessage());
        }
    }

    /**
     * Export setup performance to CSV
     */
    private void exportSetupPerformanceCsv(String filename) {
        Path filepath = Paths.get(reportDir, filename);
        
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(filepath))) {
            writer.println("setup_id,total_pnl,total_trades,win_rate,avg_win,avg_loss,max_drawdown");

            for (Map.Entry<String, SetupResults> entry : results.getSetupPerformance().entrySet()) {
                SetupResults perf = entry.getValue();
                writer.printf("%s,%.2f,%d,%.3f,%.2f,%.2f,%.2f%n",
                    perf.getSetupId(), perf.getTotalPnl(), perf.getTotalTrades(),
                    perf.getWinRate(), perf.getAvgWin(), perf.getAvgLoss(), perf.getMaxDrawdown());
            }
        } catch (IOException e) {
            System.err.println("Error writing setup performance CSV: " + e.getMessage());
        }
    }

    /**
     * Print a quick summary to console
     */
    public void printQuickSummary() {
        System.out.printf("%n🎯 Quick Summary:%n");
        System.out.printf("   Total P&L: $%.2f%n", results.getTotalPnl());
        System.out.printf("   Trades: %d%n", results.getTotalTrades());
        System.out.printf("   Win Rate: %.1f%%%n", results.getWinRate() * 100);
        System.out.printf("   Max DD: $%.2f%n", results.getMaxDrawdown());
    }
}