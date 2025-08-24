package com.backtesting.models;

import java.util.Map;

/**
 * Container for all data related to a single trading day
 */
public class TradingDayData {
    private final String date;
    private final Map<Integer, Double> spotData; // timestamp -> spot_price
    private final Map<Integer, Map<String, Map<Double, Double>>> optionData; // timestamp -> {CE/PE -> {strike -> price}}
    private final int jobEndIdx; // from .prop file - last valid timeindex for the day
    private final Map<String, Object> metadata; // other data from .prop file

    public TradingDayData(String date, Map<Integer, Double> spotData, 
                         Map<Integer, Map<String, Map<Double, Double>>> optionData,
                         int jobEndIdx, Map<String, Object> metadata) {
        this.date = date;
        this.spotData = spotData;
        this.optionData = optionData;
        this.jobEndIdx = jobEndIdx;
        this.metadata = metadata;
    }

    // Getters
    public String getDate() { return date; }
    public Map<Integer, Double> getSpotData() { return spotData; }
    public Map<Integer, Map<String, Map<Double, Double>>> getOptionData() { return optionData; }
    public int getJobEndIdx() { return jobEndIdx; }
    public Map<String, Object> getMetadata() { return metadata; }
}