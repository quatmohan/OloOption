package com.backtesting.models;

import java.util.Map;

/**
 * Represents a single options position (e.g., short straddle)
 */
public class Position {
    private final String setupId;
    private final int entryTimeindex;
    private final Map<String, Double> entryPrices; // {option_key -> entry_price_with_slippage}
    private final Map<String, Double> strikes; // {option_type -> strike}
    private final int quantity;
    private final int lotSize;
    private final double targetPnl;
    private final double stopLossPnl;
    private double currentPnl;
    private final String positionType; // "SELL" or "BUY"
    private final int forceCloseTimeindex;
    private final double slippage;

    public Position(String setupId, int entryTimeindex, Map<String, Double> entryPrices,
                   Map<String, Double> strikes, int quantity, int lotSize,
                   double targetPnl, double stopLossPnl, String positionType,
                   int forceCloseTimeindex, double slippage) {
        this.setupId = setupId;
        this.entryTimeindex = entryTimeindex;
        this.entryPrices = entryPrices;
        this.strikes = strikes;
        this.quantity = quantity;
        this.lotSize = lotSize;
        this.targetPnl = targetPnl;
        this.stopLossPnl = stopLossPnl;
        this.currentPnl = 0.0;
        this.positionType = positionType;
        this.forceCloseTimeindex = forceCloseTimeindex;
        this.slippage = slippage;
    }

    // Getters and setters
    public String getSetupId() { return setupId; }
    public int getEntryTimeindex() { return entryTimeindex; }
    public Map<String, Double> getEntryPrices() { return entryPrices; }
    public Map<String, Double> getStrikes() { return strikes; }
    public int getQuantity() { return quantity; }
    public int getLotSize() { return lotSize; }
    public double getTargetPnl() { return targetPnl; }
    public double getStopLossPnl() { return stopLossPnl; }
    public double getCurrentPnl() { return currentPnl; }
    public void setCurrentPnl(double currentPnl) { this.currentPnl = currentPnl; }
    public String getPositionType() { return positionType; }
    public int getForceCloseTimeindex() { return forceCloseTimeindex; }
    public double getSlippage() { return slippage; }
}