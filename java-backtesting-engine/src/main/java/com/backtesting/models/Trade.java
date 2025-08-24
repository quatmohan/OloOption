package com.backtesting.models;

import java.util.Map;

/**
 * Completed trade record
 */
public class Trade {
    private final String setupId;
    private final int entryTimeindex;
    private final int exitTimeindex;
    private final Map<String, Double> entryPrices;
    private final Map<String, Double> exitPrices;
    private final Map<String, Double> strikes;
    private final int quantity;
    private final double pnl;
    private final String exitReason; // "TARGET", "STOP_LOSS", "TIME_BASED", "FORCE_CLOSE", "DAILY_LIMIT"
    private final String date; // Trading date

    public Trade(String setupId, int entryTimeindex, int exitTimeindex,
                Map<String, Double> entryPrices, Map<String, Double> exitPrices,
                Map<String, Double> strikes, int quantity, double pnl,
                String exitReason, String date) {
        this.setupId = setupId;
        this.entryTimeindex = entryTimeindex;
        this.exitTimeindex = exitTimeindex;
        this.entryPrices = entryPrices;
        this.exitPrices = exitPrices;
        this.strikes = strikes;
        this.quantity = quantity;
        this.pnl = pnl;
        this.exitReason = exitReason;
        this.date = date;
    }

    // Getters
    public String getSetupId() { return setupId; }
    public int getEntryTimeindex() { return entryTimeindex; }
    public int getExitTimeindex() { return exitTimeindex; }
    public Map<String, Double> getEntryPrices() { return entryPrices; }
    public Map<String, Double> getExitPrices() { return exitPrices; }
    public Map<String, Double> getStrikes() { return strikes; }
    public int getQuantity() { return quantity; }
    public double getPnl() { return pnl; }
    public String getExitReason() { return exitReason; }
    public String getDate() { return date; }
}