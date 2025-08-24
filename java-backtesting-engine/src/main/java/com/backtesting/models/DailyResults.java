package com.backtesting.models;

import java.util.Map;

/**
 * Results for a single trading day
 */
public class DailyResults {
    private final String date;
    private final double dailyPnl;
    private final int tradesCount;
    private final int positionsForcedClosedAtJobEnd;
    private final Map<String, Double> setupPnls;

    public DailyResults(String date, double dailyPnl, int tradesCount,
                       int positionsForcedClosedAtJobEnd, Map<String, Double> setupPnls) {
        this.date = date;
        this.dailyPnl = dailyPnl;
        this.tradesCount = tradesCount;
        this.positionsForcedClosedAtJobEnd = positionsForcedClosedAtJobEnd;
        this.setupPnls = setupPnls;
    }

    // Getters
    public String getDate() { return date; }
    public double getDailyPnl() { return dailyPnl; }
    public int getTradesCount() { return tradesCount; }
    public int getPositionsForcedClosedAtJobEnd() { return positionsForcedClosedAtJobEnd; }
    public Map<String, Double> getSetupPnls() { return setupPnls; }
}