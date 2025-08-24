package com.backtesting.models;

import java.util.List;
import java.util.Map;

/**
 * Complete backtesting results
 */
public class BacktestResults {
    private final double totalPnl;
    private final List<DailyResults> dailyResults;
    private final List<Trade> tradeLog;
    private final Map<String, SetupResults> setupPerformance;
    private final double winRate;
    private final double maxDrawdown;
    private final int totalTrades;

    public BacktestResults(double totalPnl, List<DailyResults> dailyResults,
                          List<Trade> tradeLog, Map<String, SetupResults> setupPerformance,
                          double winRate, double maxDrawdown, int totalTrades) {
        this.totalPnl = totalPnl;
        this.dailyResults = dailyResults;
        this.tradeLog = tradeLog;
        this.setupPerformance = setupPerformance;
        this.winRate = winRate;
        this.maxDrawdown = maxDrawdown;
        this.totalTrades = totalTrades;
    }

    // Getters
    public double getTotalPnl() { return totalPnl; }
    public List<DailyResults> getDailyResults() { return dailyResults; }
    public List<Trade> getTradeLog() { return tradeLog; }
    public Map<String, SetupResults> getSetupPerformance() { return setupPerformance; }
    public double getWinRate() { return winRate; }
    public double getMaxDrawdown() { return maxDrawdown; }
    public int getTotalTrades() { return totalTrades; }
}

