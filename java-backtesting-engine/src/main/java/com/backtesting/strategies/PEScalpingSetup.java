package com.backtesting.strategies;

import com.backtesting.models.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * PE (Put) scalping strategy with re-entry capability
 */
public class PEScalpingSetup extends TradingSetup {
    private final int maxReentries;
    private final int reentryGap;
    private int lastEntryTime = 0;
    private int entryCount = 0;

    public PEScalpingSetup(String setupId, double targetPct, double stopLossPct,
                          int entryTimeindex, int closeTimeindex, String strikeSelection,
                          double scalpingPrice, int strikesAway, int maxReentries, int reentryGap) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, closeTimeindex,
              strikeSelection, scalpingPrice, strikesAway);
        this.maxReentries = maxReentries;
        this.reentryGap = reentryGap;
    }

    public PEScalpingSetup(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
        this(setupId, targetPct, stopLossPct, entryTimeindex, 4650, "premium", 0.40, 2, 3, 300);
    }

    @Override
    public boolean checkEntryCondition(int currentTimeindex) {
        // Initial entry
        if (entryCount == 0 && currentTimeindex == entryTimeindex) {
            return true;
        }

        // Re-entry conditions
        if (entryCount < maxReentries &&
            currentTimeindex >= lastEntryTime + reentryGap &&
            currentTimeindex <= closeTimeindex - 100) { // Don't enter too close to close
            return true;
        }

        return false;
    }

    @Override
    public Map<String, Double> selectStrikes(double spotPrice, Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selectedStrikes = new HashMap<>();

        if (!optionChain.containsKey("PE")) {
            return selectedStrikes;
        }

        if ("premium".equals(strikeSelection)) {
            // For PE options: iterate from OTM to ITM
            Map<Double, Double> peOptions = optionChain.get("PE");
            
            List<Double> otmStrikes = peOptions.keySet().stream()
                    .filter(s -> s <= spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
            
            List<Double> itmStrikes = peOptions.keySet().stream()
                    .filter(s -> s > spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
            
            List<Double> allPeStrikes = new ArrayList<>(otmStrikes);
            allPeStrikes.addAll(itmStrikes);
            
            for (Double strike : allPeStrikes) {
                double premium = peOptions.get(strike);
                if (premium >= scalpingPrice) {
                    selectedStrikes.put("PE", strike);
                    break;
                }
            }
        } else if ("distance".equals(strikeSelection)) {
            List<Double> peStrikes = optionChain.get("PE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(peStrikes, spotPrice);
            int targetIdx = Math.max(spotIdx - strikesAway, 0);
            selectedStrikes.put("PE", peStrikes.get(targetIdx));
        }

        return selectedStrikes;
    }

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

        // Create PE position
        if (selectedStrikes.containsKey("PE") && marketData.getOptionPrices().containsKey("PE")) {
            Double strike = selectedStrikes.get("PE");
            if (marketData.getOptionPrices().get("PE").containsKey(strike)) {
                double marketPrice = marketData.getOptionPrices().get("PE").get(strike);
                entryPrices.put("PE_" + strike, marketPrice); // Store original price
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
                "SELL",
                closeTimeindex,
                0.005 // slippage
            );
            positions.add(position);

            // Update tracking
            lastEntryTime = marketData.getTimestamp();
            entryCount++;
        }

        return positions;
    }

    @Override
    public void resetDailyState() {
        lastEntryTime = 0;
        entryCount = 0;
    }
}