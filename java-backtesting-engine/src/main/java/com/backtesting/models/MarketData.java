package com.backtesting.models;

import java.util.List;
import java.util.Map;

/**
 * Market data at a specific timestamp
 */
public class MarketData {
    private final int timestamp;
    private final double spotPrice;
    private final Map<String, Map<Double, Double>> optionPrices; // {CE/PE -> {strike -> price}}
    private final List<Double> availableStrikes;

    public MarketData(int timestamp, double spotPrice, 
                     Map<String, Map<Double, Double>> optionPrices,
                     List<Double> availableStrikes) {
        this.timestamp = timestamp;
        this.spotPrice = spotPrice;
        this.optionPrices = optionPrices;
        this.availableStrikes = availableStrikes;
    }

    // Getters
    public int getTimestamp() { return timestamp; }
    public double getSpotPrice() { return spotPrice; }
    public Map<String, Map<Double, Double>> getOptionPrices() { return optionPrices; }
    public List<Double> getAvailableStrikes() { return availableStrikes; }
}