package com.backtesting.strategies;

import com.backtesting.models.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Straddle selling strategy implementation
 */
public class StraddleSetup extends TradingSetup {

    public StraddleSetup(String setupId, double targetPct, double stopLossPct,
                        int entryTimeindex, int closeTimeindex, String strikeSelection,
                        double scalpingPrice, int strikesAway) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, closeTimeindex,
              strikeSelection, scalpingPrice, strikesAway);
    }

    public StraddleSetup(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
        this(setupId, targetPct, stopLossPct, entryTimeindex, 4650, "premium", 0.40, 2);
    }

    @Override
    public boolean checkEntryCondition(int currentTimeindex) {
        return currentTimeindex == entryTimeindex;
    }

    @Override
    public Map<String, Double> selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selectedStrikes = new HashMap<>();

        if ("premium".equals(strikeSelection)) {
            selectedStrikes = selectPremiumBasedStrikes(spotPrice, optionChain);
        } else if ("distance".equals(strikeSelection)) {
            selectedStrikes = selectDistanceBasedStrikes(spotPrice, optionChain);
        }

        return selectedStrikes;
    }

    /**
     * Select strikes based on premium >= scalping_price
     */
    private Map<String, Double> selectPremiumBasedStrikes(double spotPrice, 
                                                         Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selected = new HashMap<>();

        // For CE options: iterate from OTM to ITM
        if (optionChain.containsKey("CE")) {
            Map<Double, Double> ceOptions = optionChain.get("CE");
            
            // Get OTM strikes (above spot) and sort from highest to lowest
            List<Double> otmStrikes = ceOptions.keySet().stream()
                    .filter(s -> s >= spotPrice)
                    .sorted(Collections.reverseOrder())
                    .collect(Collectors.toList());
            
            // Then get ITM strikes (below spot) and sort from highest to lowest
            List<Double> itmStrikes = ceOptions.keySet().stream()
                    .filter(s -> s < spotPrice)
                    .sorted(Collections.reverseOrder())
                    .collect(Collectors.toList());
            
            // Combine: OTM first, then ITM
            List<Double> allCeStrikes = new ArrayList<>(otmStrikes);
            allCeStrikes.addAll(itmStrikes);
            
            for (Double strike : allCeStrikes) {
                double premium = ceOptions.get(strike);
                if (premium >= scalpingPrice) {
                    selected.put("CE", strike);
                    break;
                }
            }
        }

        // For PE options: iterate from OTM to ITM
        if (optionChain.containsKey("PE")) {
            Map<Double, Double> peOptions = optionChain.get("PE");
            
            // Get OTM strikes (below spot) and sort from lowest to highest
            List<Double> otmStrikes = peOptions.keySet().stream()
                    .filter(s -> s <= spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
            
            // Then get ITM strikes (above spot) and sort from lowest to highest
            List<Double> itmStrikes = peOptions.keySet().stream()
                    .filter(s -> s > spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
            
            // Combine: OTM first, then ITM
            List<Double> allPeStrikes = new ArrayList<>(otmStrikes);
            allPeStrikes.addAll(itmStrikes);
            
            for (Double strike : allPeStrikes) {
                double premium = peOptions.get(strike);
                if (premium >= scalpingPrice) {
                    selected.put("PE", strike);
                    break;
                }
            }
        }

        return selected;
    }

    /**
     * Select strikes N positions away from spot
     */
    private Map<String, Double> selectDistanceBasedStrikes(double spotPrice, 
                                                          Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selected = new HashMap<>();

        // Get available strikes and find closest to spot
        if (optionChain.containsKey("CE")) {
            List<Double> ceStrikes = optionChain.get("CE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(ceStrikes, spotPrice);
            int targetIdx = Math.min(spotIdx + strikesAway, ceStrikes.size() - 1);
            selected.put("CE", ceStrikes.get(targetIdx));
        }

        if (optionChain.containsKey("PE")) {
            List<Double> peStrikes = optionChain.get("PE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(peStrikes, spotPrice);
            int targetIdx = Math.max(spotIdx - strikesAway, 0);
            selected.put("PE", peStrikes.get(targetIdx));
        }

        return selected;
    }

    /**
     * Find index of strike closest to spot price
     */
    private int findClosestStrikeIndex(List<Double> strikes, double spotPrice) {
        int closestIdx = 0;
        double minDistance = Math.abs(strikes.get(0) - spotPrice);
        
        for (int i = 1; i < strikes.size(); i++) {
            double distance = Math.abs(strikes.get(i) - spotPrice);
            if (distance < minDistance) {
                minDistance = distance;
                closestIdx = i;
            }
        }
        
        return closestIdx;
    }

    @Override
    public List<Position> createPositions(MarketData marketData) {
        Map<String, Double> selectedStrikes = selectStrikes(marketData.getSpotPrice(), 
                                                           marketData.getOptionPrices());

        if (selectedStrikes.isEmpty()) {
            return new ArrayList<>();
        }

        List<Position> positions = new ArrayList<>();
        Map<String, Double> entryPrices = new HashMap<>();

        // Create positions for selected strikes
        for (Map.Entry<String, Double> entry : selectedStrikes.entrySet()) {
            String optionType = entry.getKey();
            Double strike = entry.getValue();
            
            if (marketData.getOptionPrices().containsKey(optionType) &&
                marketData.getOptionPrices().get(optionType).containsKey(strike)) {
                // Store original market price (slippage applied in P&L calculation)
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
                1, // quantity
                100, // lot size
                targetPct,
                -Math.abs(stopLossPct),
                "SELL", // Default to selling straddle
                closeTimeindex,
                0.005 // slippage
            );
            positions.add(position);
        }

        return positions;
    }
}