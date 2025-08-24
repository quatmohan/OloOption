package com.backtesting.strategies;

import com.backtesting.models.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Hedged straddle strategy - sell straddle + buy hedge options
 */
public class HedgedStraddleSetup extends TradingSetup {
    private final int hedgeStrikesAway; // How far to place hedge strikes

    public HedgedStraddleSetup(String setupId, double targetPct, double stopLossPct,
                              int entryTimeindex, int closeTimeindex, String strikeSelection,
                              double scalpingPrice, int strikesAway, int hedgeStrikesAway) {
        super(setupId, targetPct, stopLossPct, entryTimeindex, closeTimeindex,
              strikeSelection, scalpingPrice, strikesAway);
        this.hedgeStrikesAway = hedgeStrikesAway;
    }

    public HedgedStraddleSetup(String setupId, double targetPct, double stopLossPct, int entryTimeindex) {
        this(setupId, targetPct, stopLossPct, entryTimeindex, 4650, "premium", 0.40, 2, 5);
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

        // Add hedge strikes
        Map<String, Double> hedgeStrikes = selectHedgeStrikes(spotPrice, optionChain, selectedStrikes);
        selectedStrikes.putAll(hedgeStrikes);

        return selectedStrikes;
    }

    /**
     * Select main straddle strikes based on premium >= scalping_price
     */
    private Map<String, Double> selectPremiumBasedStrikes(double spotPrice, 
                                                         Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selected = new HashMap<>();

        // For CE options: iterate from OTM to ITM
        if (optionChain.containsKey("CE")) {
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
                    selected.put("CE_SELL", strike);
                    break;
                }
            }
        }

        // For PE options: iterate from OTM to ITM
        if (optionChain.containsKey("PE")) {
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
                    selected.put("PE_SELL", strike);
                    break;
                }
            }
        }

        return selected;
    }

    /**
     * Select main straddle strikes N positions away from spot
     */
    private Map<String, Double> selectDistanceBasedStrikes(double spotPrice, 
                                                          Map<String, Map<Double, Double>> optionChain) {
        Map<String, Double> selected = new HashMap<>();

        if (optionChain.containsKey("CE")) {
            List<Double> ceStrikes = optionChain.get("CE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(ceStrikes, spotPrice);
            int targetIdx = Math.min(spotIdx + strikesAway, ceStrikes.size() - 1);
            selected.put("CE_SELL", ceStrikes.get(targetIdx));
        }

        if (optionChain.containsKey("PE")) {
            List<Double> peStrikes = optionChain.get("PE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            int spotIdx = findClosestStrikeIndex(peStrikes, spotPrice);
            int targetIdx = Math.max(spotIdx - strikesAway, 0);
            selected.put("PE_SELL", peStrikes.get(targetIdx));
        }

        return selected;
    }

    /**
     * Select hedge strikes further OTM
     */
    private Map<String, Double> selectHedgeStrikes(double spotPrice, 
                                                  Map<String, Map<Double, Double>> optionChain,
                                                  Map<String, Double> mainStrikes) {
        Map<String, Double> hedgeStrikes = new HashMap<>();

        // CE hedge - further OTM (higher strike)
        if (mainStrikes.containsKey("CE_SELL") && optionChain.containsKey("CE")) {
            List<Double> ceStrikes = optionChain.get("CE").keySet().stream()
                    .sorted()
                    .collect(Collectors.toList());
            
            double mainStrike = mainStrikes.get("CE_SELL");
            
            // Find strikes further OTM than main strike
            List<Double> otmStrikes = ceStrikes.stream()
                    .filter(s -> s > mainStrike)
                    .collect(Collectors.toList());
            
            if (otmStrikes.size() >= hedgeStrikesAway) {
                hedgeStrikes.put("CE_BUY", otmStrikes.get(hedgeStrikesAway - 1));
            } else if (!otmStrikes.isEmpty()) {
                hedgeStrikes.put("CE_BUY", otmStrikes.get(otmStrikes.size() - 1)); // Use furthest available
            }
        }

        // PE hedge - further OTM (lower strike)
        if (mainStrikes.containsKey("PE_SELL") && optionChain.containsKey("PE")) {
            List<Double> peStrikes = optionChain.get("PE").keySet().stream()
                    .sorted(Collections.reverseOrder())
                    .collect(Collectors.toList());
            
            double mainStrike = mainStrikes.get("PE_SELL");
            
            // Find strikes further OTM than main strike
            List<Double> otmStrikes = peStrikes.stream()
                    .filter(s -> s < mainStrike)
                    .collect(Collectors.toList());
            
            if (otmStrikes.size() >= hedgeStrikesAway) {
                hedgeStrikes.put("PE_BUY", otmStrikes.get(hedgeStrikesAway - 1));
            } else if (!otmStrikes.isEmpty()) {
                hedgeStrikes.put("PE_BUY", otmStrikes.get(otmStrikes.size() - 1)); // Use furthest available
            }
        }

        return hedgeStrikes;
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
        Map<String, Double> positionStrikes = new HashMap<>();

        // Create positions for selected strikes
        for (Map.Entry<String, Double> entry : selectedStrikes.entrySet()) {
            String strikeKey = entry.getKey();
            Double strike = entry.getValue();
            
            String[] parts = strikeKey.split("_");
            String optionType = parts[0]; // CE or PE
            String positionType = parts[1]; // SELL or BUY

            if (marketData.getOptionPrices().containsKey(optionType) &&
                marketData.getOptionPrices().get(optionType).containsKey(strike)) {
                double marketPrice = marketData.getOptionPrices().get(optionType).get(strike);

                // Store original market price (slippage applied in P&L calculation)
                entryPrices.put(optionType + "_" + strike + "_" + positionType, marketPrice);
                positionStrikes.put(strikeKey, strike);
            }
        }

        if (!entryPrices.isEmpty()) {
            Position position = new Position(
                setupId,
                marketData.getTimestamp(),
                entryPrices,
                positionStrikes,
                1, // quantity
                100, // lot size
                targetPct,
                -Math.abs(stopLossPct),
                "HEDGED", // Mixed position type
                closeTimeindex,
                0.005 // slippage
            );
            positions.add(position);
        }

        return positions;
    }
}