package com.backtesting.models;

/**
 * Performance results for a specific setup
 */
public class SetupResults {
    private final String setupId;
    private final double totalPnl;
    private final int totalTrades;
    private final double winRate;
    private final double avgWin;
    private final double avgLoss;
    private final double maxDrawdown;

    public SetupResults(String setupId, double totalPnl, int totalTrades,
                       double winRate, double avgWin, double avgLoss, double maxDrawdown) {
        this.setupId = setupId;
        this.totalPnl = totalPnl;
        this.totalTrades = totalTrades;
        this.winRate = winRate;
        this.avgWin = avgWin;
        this.avgLoss = avgLoss;
        this.maxDrawdown = maxDrawdown;
    }

    // Getters
    public String getSetupId() { return setupId; }
    public double getTotalPnl() { return totalPnl; }
    public int getTotalTrades() { return totalTrades; }
    public double getWinRate() { return winRate; }
    public double getAvgWin() { return avgWin; }
    public double getAvgLoss() { return avgLoss; }
    public double getMaxDrawdown() { return maxDrawdown; }
}