package com.backtesting.engine;

import com.backtesting.models.*;
import com.backtesting.strategies.TradingSetup;
import java.util.*;

/**
 * Tracks all open positions and calculates real-time P&L
 */
public class PositionManager {
    private final Map<String, Position> positions = new HashMap<>();
    private int positionCounter = 0;

    /**
     * Add a new position and return position ID
     */
    public String addPosition(Position position) {
        String positionId = position.getSetupId() + "_" + positionCounter++;
        positions.put(positionId, position);
        return positionId;
    }

    /**
     * Update all positions and return closed positions as trades
     */
    public List<Trade> updatePositions(MarketData marketData, String date) {
        List<Trade> closedTrades = new ArrayList<>();
        List<String> positionsToRemove = new ArrayList<>();

        for (Map.Entry<String, Position> entry : positions.entrySet()) {
            String positionId = entry.getKey();
            Position position = entry.getValue();

            // Calculate current P&L
            double currentPnl = calculatePositionPnl(position, marketData);
            position.setCurrentPnl(currentPnl);

            // Check exit conditions
            String exitReason = checkExitConditions(position, marketData.getTimestamp());

            if (exitReason != null) {
                Trade trade = closePosition(position, marketData, exitReason, date);
                closedTrades.add(trade);
                positionsToRemove.add(positionId);
            }
        }

        // Remove closed positions
        for (String positionId : positionsToRemove) {
            positions.remove(positionId);
        }

        return closedTrades;
    }

    /**
     * Check for time-based position closures
     */
    public List<Trade> checkTimeBasedClosures(int currentTimeindex, List<TradingSetup> setups) {
        List<Trade> closedTrades = new ArrayList<>();
        List<String> positionsToRemove = new ArrayList<>();

        // Create setup lookup for force close times
        Map<String, Integer> setupCloseTimes = new HashMap<>();
        for (TradingSetup setup : setups) {
            setupCloseTimes.put(setup.getSetupId(), setup.getCloseTimeindex());
        }

        for (Map.Entry<String, Position> entry : positions.entrySet()) {
            String positionId = entry.getKey();
            Position position = entry.getValue();

            int setupCloseTime = setupCloseTimes.getOrDefault(position.getSetupId(), 
                                                            position.getForceCloseTimeindex());

            if (currentTimeindex >= setupCloseTime) {
                // Create dummy market data for closure
                MarketData marketData = new MarketData(currentTimeindex, 0.0, 
                                                     new HashMap<>(), new ArrayList<>());

                Trade trade = closePosition(position, marketData, "TIME_BASED", "");
                closedTrades.add(trade);
                positionsToRemove.add(positionId);
            }
        }

        // Remove closed positions
        for (String positionId : positionsToRemove) {
            positions.remove(positionId);
        }

        return closedTrades;
    }

    /**
     * Get total P&L across all positions
     */
    public double getTotalPnl() {
        return positions.values().stream()
                .mapToDouble(Position::getCurrentPnl)
                .sum();
    }

    /**
     * Get P&L for a specific setup
     */
    public double getSetupPnl(String setupId) {
        return positions.values().stream()
                .filter(p -> p.getSetupId().equals(setupId))
                .mapToDouble(Position::getCurrentPnl)
                .sum();
    }

    /**
     * Close all open positions
     */
    public List<Trade> closeAllPositions(MarketData marketData, String reason, String date) {
        List<Trade> closedTrades = new ArrayList<>();

        for (Position position : positions.values()) {
            Trade trade = closePosition(position, marketData, reason, date);
            closedTrades.add(trade);
        }

        positions.clear();
        return closedTrades;
    }

    /**
     * Force close all positions at job end index
     */
    public List<Trade> forceCloseAtJobEnd(int jobEndIdx, MarketData marketData, String date) {
        return closeAllPositions(marketData, "JOB_END", date);
    }

    /**
     * Clear all positions for new trading day
     */
    public void resetPositions() {
        positions.clear();
        positionCounter = 0;
    }

    /**
     * Calculate current P&L for a position with slippage applied
     */
    private double calculatePositionPnl(Position position, MarketData marketData) {
        double totalPnl = 0.0;

        for (Map.Entry<String, Double> entry : position.getEntryPrices().entrySet()) {
            String optionKey = entry.getKey();
            double entryPrice = entry.getValue();

            // Parse option key - handle both formats
            String[] parts = optionKey.split("_");
            String optionType = parts[0]; // CE or PE
            double strike = Double.parseDouble(parts[1]);

            // Determine if this is a SELL or BUY position
            String legType = parts.length >= 3 ? parts[2] : position.getPositionType();

            // Get current market price
            double currentPrice = 0.0;
            if (marketData.getOptionPrices().containsKey(optionType) &&
                marketData.getOptionPrices().get(optionType).containsKey(strike)) {
                currentPrice = marketData.getOptionPrices().get(optionType).get(strike);
            }

            // Apply slippage to prices for P&L calculation
            double optionPnl;
            if ("SELL".equals(legType)) {
                // When selling: receive less on entry, pay more on exit
                double effectiveEntry = entryPrice - position.getSlippage();
                double effectiveExit = currentPrice + position.getSlippage();
                optionPnl = (effectiveEntry - effectiveExit) * position.getQuantity() * position.getLotSize();
            } else { // BUY
                // When buying: pay more on entry, receive less on exit
                double effectiveEntry = entryPrice + position.getSlippage();
                double effectiveExit = currentPrice - position.getSlippage();
                optionPnl = (effectiveExit - effectiveEntry) * position.getQuantity() * position.getLotSize();
            }

            totalPnl += optionPnl;
        }

        return totalPnl;
    }

    /**
     * Check if position should be closed
     */
    private String checkExitConditions(Position position, int currentTimeindex) {
        // Check target
        if (position.getTargetPnl() > 0 && position.getCurrentPnl() >= position.getTargetPnl()) {
            return "TARGET";
        }

        // Check stop loss
        if (position.getStopLossPnl() < 0 && position.getCurrentPnl() <= position.getStopLossPnl()) {
            return "STOP_LOSS";
        }

        // Check time-based close
        if (currentTimeindex >= position.getForceCloseTimeindex()) {
            return "TIME_BASED";
        }

        return null;
    }

    /**
     * Close a position and create trade record
     */
    private Trade closePosition(Position position, MarketData marketData, String exitReason, String date) {
        Map<String, Double> exitPrices = new HashMap<>();

        // Get exit prices (original market prices, slippage applied in P&L calculation)
        for (Map.Entry<String, Double> entry : position.getEntryPrices().entrySet()) {
            String optionKey = entry.getKey();
            String[] parts = optionKey.split("_");
            String optionType = parts[0]; // CE or PE
            double strike = Double.parseDouble(parts[1]);

            // Get current market price
            double marketPrice = 0.0;
            if (marketData.getOptionPrices().containsKey(optionType) &&
                marketData.getOptionPrices().get(optionType).containsKey(strike)) {
                marketPrice = marketData.getOptionPrices().get(optionType).get(strike);
            }

            // Store original market price (slippage applied in P&L calculation)
            exitPrices.put(optionKey, marketPrice);
        }

        // Calculate final P&L with slippage applied
        double finalPnl = 0.0;
        for (Map.Entry<String, Double> entry : position.getEntryPrices().entrySet()) {
            String optionKey = entry.getKey();
            double entryPrice = entry.getValue();
            double exitPrice = exitPrices.get(optionKey);

            // Parse leg type for P&L calculation
            String[] parts = optionKey.split("_");
            String legType = parts.length >= 3 ? parts[2] : position.getPositionType();

            // Apply slippage to P&L calculation
            double optionPnl;
            if ("SELL".equals(legType)) {
                // When selling: receive less on entry, pay more on exit
                double effectiveEntry = entryPrice - position.getSlippage();
                double effectiveExit = exitPrice + position.getSlippage();
                optionPnl = (effectiveEntry - effectiveExit) * position.getQuantity() * position.getLotSize();
            } else { // BUY
                // When buying: pay more on entry, receive less on exit
                double effectiveEntry = entryPrice + position.getSlippage();
                double effectiveExit = exitPrice - position.getSlippage();
                optionPnl = (effectiveExit - effectiveEntry) * position.getQuantity() * position.getLotSize();
            }

            finalPnl += optionPnl;
        }

        return new Trade(
            position.getSetupId(),
            position.getEntryTimeindex(),
            marketData.getTimestamp(),
            position.getEntryPrices(),
            exitPrices,
            position.getStrikes(),
            position.getQuantity(),
            finalPnl,
            exitReason,
            date
        );
    }
}