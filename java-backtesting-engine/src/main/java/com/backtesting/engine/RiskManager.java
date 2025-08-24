package com.backtesting.engine;

/**
 * Implements risk controls and daily limits
 */
public class RiskManager {
    private final double dailyMaxLoss;
    private double dailyPnl = 0.0;

    public RiskManager(double dailyMaxLoss) {
        this.dailyMaxLoss = Math.abs(dailyMaxLoss); // Ensure positive value
    }

    /**
     * Check if daily limit is breached
     */
    public boolean checkDailyLimit(double currentPnl) {
        return currentPnl <= -dailyMaxLoss;
    }

    /**
     * Check if all positions should be closed due to daily limit
     */
    public boolean shouldCloseAllPositions(double totalPnl) {
        return checkDailyLimit(totalPnl);
    }

    /**
     * Update daily P&L tracking
     */
    public void updateDailyPnl(double pnl) {
        this.dailyPnl = pnl;
    }

    /**
     * Reset daily tracking for new trading day
     */
    public void resetDailyTracking() {
        this.dailyPnl = 0.0;
    }

    /**
     * Get remaining risk capacity for the day
     */
    public double getRemainingRiskCapacity() {
        return Math.max(0, dailyMaxLoss + dailyPnl);
    }

    // Getters
    public double getDailyMaxLoss() { return dailyMaxLoss; }
    public double getDailyPnl() { return dailyPnl; }
}