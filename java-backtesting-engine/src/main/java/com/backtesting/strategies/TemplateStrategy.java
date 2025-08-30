package com.backtesting.strategies;

import com.backtesting.models.*;
import java.util.*;

/**
 * Template strategy showing how to implement a custom trading strategy
 * 
 * This is a basic template - modify the logic to implement your own strategy.
 * You can copy this file and rename it to create new strategies.
 */
public class TemplateStrategy extends TradingSetup {

    public TemplateStrategy(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
        // Call parent constructor with default values
        super(setupId, targetPct, stopLossPct, entryTimeindex, 4650, "premium", 0.40, 2);
    }

    public TemplateStrategy(String setupId, double targetPct, double stopLossPct,
                           int entryTimeindex, int closeTimeindex, String strikeSelection,
                           double scalpingPrice, int strikesAway) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, closeTimeindex,
              strikeSelection, scalpingPrice, strikesAway);
    }

    /**
     * Define when to enter trades
     * 
     * Examples:
     * - return currentTimeindex == entryTimeindex;  // Enter at specific time
     * - return currentTimeindex >= 930 && currentTimeindex <= 1000;  // Enter in time window
     * - Add your own logic based on market conditions
     */
    @Override
    public boolean checkEntryCondition(int currentTimeindex) {
        // TODO: Implement your entry logic
        return currentTimeindex == entryTimeindex;
    }

    /**
     * Select which option strikes to trade
     * 
     * Available option types in optionChain:
     * - "CE" for Call options
     * - "PE" for Put options
     * 
     * Return a Map with option type as key and strike price as value
     * Example: {"CE": 580.0, "PE": 575.0}
     */
    @Override
    public Map<String, Double> selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selectedStrikes = new HashMap<>();
        
        // TODO: Implement your strike selection logic
        
        // Example 1: Select ATM strikes
        if (optionChain.containsKey("CE")) {
            Double atmStrike = findClosestStrike(optionChain.get("CE").keySet(), spotPrice);
            if (atmStrike != null) {
                selectedStrikes.put("CE", atmStrike);
            }
        }
        
        if (optionChain.containsKey("PE")) {
            Double atmStrike = findClosestStrike(optionChain.get("PE").keySet(), spotPrice);
            if (atmStrike != null) {
                selectedStrikes.put("PE", atmStrike);
            }
        }
        
        return selectedStrikes;
    }

    /**
     * Create positions when entry conditions are met
     * 
     * Position types:
     * - "SELL" = Short position (receive premium, profit when price decreases)
     * - "BUY" = Long position (pay premium, profit when price increases)
     */
    @Override
    public List<Position> createPositions(MarketData marketData) {
        Map<String, Double> selectedStrikes = selectStrikes(marketData.getSpotPrice(), 
                                                           marketData.getOptionPrices());

        if (selectedStrikes.isEmpty()) {
            return new ArrayList<>();
        }

        List<Position> positions = new ArrayList<>();
        Map<String, Double> entryPrices = new HashMap<>();

        // Get market prices for selected strikes
        for (Map.Entry<String, Double> entry : selectedStrikes.entrySet()) {
            String optionType = entry.getKey();
            Double strike = entry.getValue();
            
            if (marketData.getOptionPrices().containsKey(optionType) &&
                marketData.getOptionPrices().get(optionType).containsKey(strike)) {
                
                double marketPrice = marketData.getOptionPrices().get(optionType).get(strike);
                entryPrices.put(optionType + "_" + strike, marketPrice);
            }
        }

        if (!entryPrices.isEmpty()) {
            Position position = new Position(
                setupId,
                marketData.getTimestamp(),
                entryPrices,
                selectedStrikes,
                1,                          // quantity
                100,                        // lot size (standard options contract)
                targetPct,                  // target profit
                -Math.abs(stopLossPct),     // stop loss (negative)
                "SELL",                     // TODO: Change to "BUY" or "SELL" based on your strategy
                closeTimeindex,             // force close time
                0.005                       // slippage
            );
            positions.add(position);
        }

        return positions;
    }

    /**
     * Helper method to find the strike closest to spot price
     */
    private Double findClosestStrike(Set<Double> strikes, double spotPrice) {
        return strikes.stream()
                .min((s1, s2) -> Double.compare(
                    Math.abs(s1 - spotPrice), 
                    Math.abs(s2 - spotPrice)))
                .orElse(null);
    }
}