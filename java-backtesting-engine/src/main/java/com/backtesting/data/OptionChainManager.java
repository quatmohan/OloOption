package com.backtesting.data;

import com.backtesting.models.MarketData;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Manages option chain data with efficient lookups and strike selection
 * Provides advanced caching and performance optimizations
 */
public class OptionChainManager {
    private Map<Integer, Map<String, Map<Double, Double>>> optionData = new HashMap<>();
    private final Map<Double, List<Double>> strikeCache = new ConcurrentHashMap<>(); // Thread-safe cache
    private List<Double> allStrikes = new ArrayList<>();
    private final Map<String, List<Double>> otmStrikeCache = new ConcurrentHashMap<>();
    private final Map<String, List<Double>> itmStrikeCache = new ConcurrentHashMap<>();
    
    // Performance tracking
    private long cacheHits = 0;
    private long cacheMisses = 0;

    /**
     * Load option data and build indexes for fast access
     */
    public void loadOptionData(Map<Integer, Map<String, Map<Double, Double>>> optionData) {
        this.optionData = optionData;
        buildStrikeIndexes();
        System.out.println("OptionChainManager: Loaded " + optionData.size() + " timestamps with " + 
                          allStrikes.size() + " unique strikes");
    }

    /**
     * Build comprehensive strike indexes for performance
     */
    private void buildStrikeIndexes() {
        // Get all unique strikes across all timestamps
        Set<Double> strikeSet = new HashSet<>();
        for (Map<String, Map<Double, Double>> timestampData : optionData.values()) {
            for (Map<Double, Double> optionTypeData : timestampData.values()) {
                strikeSet.addAll(optionTypeData.keySet());
            }
        }
        
        allStrikes = strikeSet.stream().sorted().collect(Collectors.toList());
        
        // Clear caches when rebuilding indexes
        strikeCache.clear();
        otmStrikeCache.clear();
        itmStrikeCache.clear();
        
        System.out.println("OptionChainManager: Built indexes for " + allStrikes.size() + " strikes");
    }

    /**
     * Get strikes closest to spot price with intelligent caching
     */
    public List<Double> getStrikesNearSpot(double spotPrice, int numStrikes) {
        // Use rounded spot price as cache key to improve hit rate
        double cacheKey = Math.round(spotPrice * 4) / 4.0; // Round to nearest 0.25
        
        if (strikeCache.containsKey(cacheKey)) {
            cacheHits++;
            return strikeCache.get(cacheKey);
        }
        
        cacheMisses++;
        
        // Calculate strikes closest to spot price
        List<StrikeDistance> strikesWithDistance = allStrikes.stream()
                .map(strike -> new StrikeDistance(strike, Math.abs(strike - spotPrice)))
                .sorted(Comparator.comparing(StrikeDistance::getDistance))
                .limit(numStrikes)
                .collect(Collectors.toList());
        
        List<Double> nearbyStrikes = strikesWithDistance.stream()
                .map(StrikeDistance::getStrike)
                .collect(Collectors.toList());
        
        // Cache the result
        strikeCache.put(cacheKey, nearbyStrikes);
        
        return nearbyStrikes;
    }

    /**
     * Get option price with efficient lookup
     */
    public Double getOptionPrice(int timestamp, String optionType, double strike) {
        if (optionData.containsKey(timestamp) &&
            optionData.get(timestamp).containsKey(optionType) &&
            optionData.get(timestamp).get(optionType).containsKey(strike)) {
            return optionData.get(timestamp).get(optionType).get(strike);
        }
        return null;
    }

    /**
     * Get all available strikes at a specific timestamp
     */
    public Map<String, List<Double>> getAvailableStrikesAtTimestamp(int timestamp) {
        if (!optionData.containsKey(timestamp)) {
            return new HashMap<>();
        }

        Map<String, List<Double>> availableStrikes = new HashMap<>();
        for (Map.Entry<String, Map<Double, Double>> entry : optionData.get(timestamp).entrySet()) {
            String optionType = entry.getKey();
            List<Double> strikes = new ArrayList<>(entry.getValue().keySet());
            Collections.sort(strikes);
            availableStrikes.put(optionType, strikes);
        }

        return availableStrikes;
    }

    /**
     * Validate that required strikes have data at timestamp
     */
    public ValidationResult validateDataCompleteness(int timestamp, List<Double> requiredStrikes) {
        ValidationResult result = new ValidationResult();
        
        if (!optionData.containsKey(timestamp)) {
            result.addMissingStrikes("CE", requiredStrikes);
            result.addMissingStrikes("PE", requiredStrikes);
            return result;
        }

        for (String optionType : Arrays.asList("CE", "PE")) {
            if (!optionData.get(timestamp).containsKey(optionType)) {
                result.addMissingStrikes(optionType, requiredStrikes);
            } else {
                Map<Double, Double> availableData = optionData.get(timestamp).get(optionType);
                for (Double strike : requiredStrikes) {
                    if (!availableData.containsKey(strike)) {
                        result.addMissingStrike(optionType, strike);
                    }
                }
            }
        }

        return result;
    }

    /**
     * Create MarketData object for a specific timestamp with validation
     */
    public MarketData getMarketData(int timestamp, double spotPrice) {
        if (!optionData.containsKey(timestamp)) {
            return null;
        }

        // Get all available strikes at this timestamp
        Set<Double> allTimestampStrikes = new HashSet<>();
        for (Map<Double, Double> optionTypeData : optionData.get(timestamp).values()) {
            allTimestampStrikes.addAll(optionTypeData.keySet());
        }

        return new MarketData(
            timestamp,
            spotPrice,
            deepCopyOptionPrices(optionData.get(timestamp)), // Defensive copy
            allTimestampStrikes.stream().sorted().collect(Collectors.toList())
        );
    }

    /**
     * Get out-of-the-money strikes with caching
     */
    public List<Double> getOtmStrikes(double spotPrice, String optionType, int timestamp) {
        String cacheKey = String.format("%s_%.2f_%d", optionType, spotPrice, timestamp);
        
        if (otmStrikeCache.containsKey(cacheKey)) {
            return otmStrikeCache.get(cacheKey);
        }

        if (!optionData.containsKey(timestamp) || !optionData.get(timestamp).containsKey(optionType)) {
            return new ArrayList<>();
        }

        List<Double> availableStrikes = new ArrayList<>(optionData.get(timestamp).get(optionType).keySet());
        List<Double> otmStrikes;

        if ("CE".equals(optionType)) {
            // For calls, OTM strikes are above spot price
            otmStrikes = availableStrikes.stream()
                    .filter(strike -> strike > spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
        } else { // PE
            // For puts, OTM strikes are below spot price
            otmStrikes = availableStrikes.stream()
                    .filter(strike -> strike < spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
        }

        otmStrikeCache.put(cacheKey, otmStrikes);
        return otmStrikes;
    }

    /**
     * Get in-the-money strikes with caching
     */
    public List<Double> getItmStrikes(double spotPrice, String optionType, int timestamp) {
        String cacheKey = String.format("%s_%.2f_%d_ITM", optionType, spotPrice, timestamp);
        
        if (itmStrikeCache.containsKey(cacheKey)) {
            return itmStrikeCache.get(cacheKey);
        }

        if (!optionData.containsKey(timestamp) || !optionData.get(timestamp).containsKey(optionType)) {
            return new ArrayList<>();
        }

        List<Double> availableStrikes = new ArrayList<>(optionData.get(timestamp).get(optionType).keySet());
        List<Double> itmStrikes;

        if ("CE".equals(optionType)) {
            // For calls, ITM strikes are below spot price
            itmStrikes = availableStrikes.stream()
                    .filter(strike -> strike < spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
        } else { // PE
            // For puts, ITM strikes are above spot price
            itmStrikes = availableStrikes.stream()
                    .filter(strike -> strike > spotPrice)
                    .sorted()
                    .collect(Collectors.toList());
        }

        itmStrikeCache.put(cacheKey, itmStrikes);
        return itmStrikes;
    }

    /**
     * Get the at-the-money strike closest to spot price
     */
    public Double getAtmStrike(double spotPrice, int timestamp) {
        if (!optionData.containsKey(timestamp)) {
            return null;
        }

        // Get all available strikes at this timestamp
        Set<Double> allTimestampStrikes = new HashSet<>();
        for (Map<Double, Double> optionTypeData : optionData.get(timestamp).values()) {
            allTimestampStrikes.addAll(optionTypeData.keySet());
        }

        if (allTimestampStrikes.isEmpty()) {
            return null;
        }

        // Find strike closest to spot price
        return allTimestampStrikes.stream()
                .min(Comparator.comparing(strike -> Math.abs(strike - spotPrice)))
                .orElse(null);
    }

    /**
     * Get strikes within a specific range of spot price
     */
    public List<Double> getStrikesInRange(double spotPrice, double rangePct, int timestamp) {
        if (!optionData.containsKey(timestamp)) {
            return new ArrayList<>();
        }

        double lowerBound = spotPrice * (1 - rangePct / 100);
        double upperBound = spotPrice * (1 + rangePct / 100);

        Set<Double> allTimestampStrikes = new HashSet<>();
        for (Map<Double, Double> optionTypeData : optionData.get(timestamp).values()) {
            allTimestampStrikes.addAll(optionTypeData.keySet());
        }

        return allTimestampStrikes.stream()
                .filter(strike -> strike >= lowerBound && strike <= upperBound)
                .sorted()
                .collect(Collectors.toList());
    }

    /**
     * Clear all caches (useful for memory management)
     */
    public void clearCaches() {
        strikeCache.clear();
        otmStrikeCache.clear();
        itmStrikeCache.clear();
        System.out.println("OptionChainManager: Cleared all caches");
    }

    /**
     * Get cache performance statistics
     */
    public CacheStats getCacheStats() {
        return new CacheStats(cacheHits, cacheMisses, strikeCache.size(), 
                             otmStrikeCache.size(), itmStrikeCache.size());
    }

    /**
     * Create a defensive copy of option prices to prevent external modification
     */
    private Map<String, Map<Double, Double>> deepCopyOptionPrices(Map<String, Map<Double, Double>> original) {
        Map<String, Map<Double, Double>> copy = new HashMap<>();
        for (Map.Entry<String, Map<Double, Double>> entry : original.entrySet()) {
            copy.put(entry.getKey(), new HashMap<>(entry.getValue()));
        }
        return copy;
    }

    // Helper classes
    private static class StrikeDistance {
        private final double strike;
        private final double distance;

        public StrikeDistance(double strike, double distance) {
            this.strike = strike;
            this.distance = distance;
        }

        public double getStrike() { return strike; }
        public double getDistance() { return distance; }
    }

    /**
     * Data validation result container
     */
    public static class ValidationResult {
        private final Map<String, List<Double>> missingStrikes = new HashMap<>();

        public void addMissingStrike(String optionType, double strike) {
            missingStrikes.computeIfAbsent(optionType, k -> new ArrayList<>()).add(strike);
        }

        public void addMissingStrikes(String optionType, List<Double> strikes) {
            missingStrikes.computeIfAbsent(optionType, k -> new ArrayList<>()).addAll(strikes);
        }

        public boolean hasErrors() {
            return !missingStrikes.isEmpty();
        }

        public Map<String, List<Double>> getMissingStrikes() {
            return new HashMap<>(missingStrikes);
        }

        @Override
        public String toString() {
            if (!hasErrors()) {
                return "ValidationResult: No missing data";
            }
            
            StringBuilder sb = new StringBuilder("ValidationResult: Missing data - ");
            for (Map.Entry<String, List<Double>> entry : missingStrikes.entrySet()) {
                sb.append(entry.getKey()).append(": ").append(entry.getValue().size()).append(" strikes, ");
            }
            return sb.toString();
        }
    }

    /**
     * Cache performance statistics
     */
    public static class CacheStats {
        private final long hits;
        private final long misses;
        private final int strikeCacheSize;
        private final int otmCacheSize;
        private final int itmCacheSize;

        public CacheStats(long hits, long misses, int strikeCacheSize, int otmCacheSize, int itmCacheSize) {
            this.hits = hits;
            this.misses = misses;
            this.strikeCacheSize = strikeCacheSize;
            this.otmCacheSize = otmCacheSize;
            this.itmCacheSize = itmCacheSize;
        }

        public double getHitRate() {
            long total = hits + misses;
            return total > 0 ? (double) hits / total : 0.0;
        }

        @Override
        public String toString() {
            return String.format("CacheStats: Hits=%d, Misses=%d, Hit Rate=%.2f%%, " +
                               "Strike Cache=%d, OTM Cache=%d, ITM Cache=%d",
                               hits, misses, getHitRate() * 100, 
                               strikeCacheSize, otmCacheSize, itmCacheSize);
        }

        // Getters
        public long getHits() { return hits; }
        public long getMisses() { return misses; }
        public int getStrikeCacheSize() { return strikeCacheSize; }
        public int getOtmCacheSize() { return otmCacheSize; }
        public int getItmCacheSize() { return itmCacheSize; }
    }
}