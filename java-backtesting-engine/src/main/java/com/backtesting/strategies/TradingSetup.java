package com.backtesting.strategies;

import com.backtesting.models.MarketData;
import com.backtesting.models.Position;
import java.util.List;
import java.util.Map;

/**
 * Abstract base class for different trading strategies
 */
public abstract class TradingSetup {
    protected final String setupId;
    protected final double targetPct;
    protected final double stopLossPct;
    protected final int entryTimeindex;
    protected final int closeTimeindex;
    protected final String strikeSelection;
    protected final double scalpingPrice;
    protected final int strikesAway;

    public TradingSetup(String setupId, double targetPct, double stopLossPct,
                       int entryTimeindex, int closeTimeindex, String strikeSelection,
                       double scalpingPrice, int strikesAway) {
        this.setupId = setupId;
        this.targetPct = targetPct;
        this.stopLossPct = stopLossPct;
        this.entryTimeindex = entryTimeindex;
        this.closeTimeindex = closeTimeindex;
        this.strikeSelection = strikeSelection;
        this.scalpingPrice = scalpingPrice;
        this.strikesAway = strikesAway;
    }

    /**
     * Check if entry conditions are met
     */
    public abstract boolean checkEntryCondition(int currentTimeindex);

    /**
     * Select strikes based on strategy logic
     */
    public abstract Map<String, Double> selectStrikes(double spotPrice, 
                                                     Map<String, Map<Double, Double>> optionChain);

    /**
     * Create positions when entry conditions are met
     */
    public abstract List<Position> createPositions(MarketData marketData);

    /**
     * Check if time-based close needed
     */
    public boolean shouldForceClose(int currentTimeindex) {
        return currentTimeindex >= closeTimeindex;
    }

    /**
     * Reset daily state for new trading day - override in subclasses if needed
     */
    public void resetDailyState() {
        // Default implementation - no state to reset
    }

    // Getters
    public String getSetupId() { return setupId; }
    public double getTargetPct() { return targetPct; }
    public double getStopLossPct() { return stopLossPct; }
    public int getEntryTimeindex() { return entryTimeindex; }
    public int getCloseTimeindex() { return closeTimeindex; }
    public String getStrikeSelection() { return strikeSelection; }
    public double getScalpingPrice() { return scalpingPrice; }
    public int getStrikesAway() { return strikesAway; }
}