package com.backtesting.strategies;

import com.backtesting.models.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * CE (Call) scalping strategy with re-entry capability
 */
public class CEScalpingSetup extends TradingSetup {
    private final int maxReentries;
    private final int reentryGap;
    private int lastEntryTime = 0;
    private int entryCount = 0;

    public CEScalpingSetup(String setupId, double targetPct, double stopLossPct,
                          int entryTimeindex, int closeTimeindex, String strikeSelection,
                          double scalpingPrice, int strikesAway, int maxReentries, int reentryGap) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, closeTimeindex,
              strikeSelection, scalpingPrice, strikesAway);
        this.maxReentries = maxReentries;
        this.reentryGap = reentryGap;
    }

    public CEScalpingSetup(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
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

        if (!optionChain.containsKey("CE")) {
            return selectedStrikes;
        }

        if ("premium".equals(strikeSelection)) {
            // For CE options: iterate from OTM to ITM
            Map<Double, Double> ceOptions = optionChain.get("CE");
            
            List<Double> otmStrikes = ceOptions.keySet().stream()
                    .filter(s -> s >= spotPrice)
                    .sorted(Collections.reverseOrder())
                    .collect(Collectors.toList());
            
            List<Double> itmStrikes = ceOptions.keySet().stream()
                    .filter(s -> s < spotPrice)
                    .sorted(Collections.reverseOrder())
                    .collect(Collectors.toList());
            
            List<Double> allCeStrikes = new ArrayList<>(otmStrikes);
            allCeStrikes.addAll(itmStrikes);
            
            for (Double strike : allCeStrikes) {
                double premium = ceOptions.get(strike);
                if (premium >= scalpingPrice) {
                    selectedStrikes.put("CE", strike);
                    break;
                }
            }
        } else if ("distance".equals(strikeSelection)) {
            List<Double> ceStrikes = optionChain.get("CE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(ceStrikes, spotPrice);
            int targetIdx = Math.min(spotIdx + strikesAway, ceStrikes.size() - 1);
            selectedStrikes.put("CE", ceStrikes.get(targetIdx));
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

        // Create CE position
        if (selectedStrikes.containsKey("CE") && marketData.getOptionPrices().containsKey("CE")) {
            Double strike = selectedStrikes.get("CE");
            if (marketData.getOptionPrices().get("CE").containsKey(strike)) {
                double marketPrice = marketData.getOptionPrices().get("CE").get(strike);
                entryPrices.put("CE_" + strike, marketPrice); // Store original price
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