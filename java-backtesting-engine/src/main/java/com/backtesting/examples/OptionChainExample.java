package com.backtesting.examples;

import com.backtesting.data.DataLoader;
import com.backtesting.data.OptionChainManager;
import com.backtesting.models.TradingDayData;
import java.util.*;

/**
 * Example demonstrating advanced Option Chain Manager capabilities
 */
public class OptionChainExample {
    
    public static void main(String[] args) {
        demonstrateOptionChainManager();
    }
    
    public static void demonstrateOptionChainManager() {
        System.out.println("=== Option Chain Manager Demo ===");
        
        // Load data
        DataLoader dataLoader = new DataLoader("../5SecData");
        List<String> availableDates = dataLoader.getAvailableDates("QQQ");
        
        if (availableDates.isEmpty()) {
            System.out.println("No data files found. Please check the data path.");
            return;
        }
        
        String testDate = availableDates.get(0);
        System.out.println("Using test date: " + testDate);
        
        TradingDayData dayData = dataLoader.loadTradingDay("QQQ", testDate);
        if (dayData == null) {
            System.out.println("Could not load data for " + testDate);
            return;
        }
        
        // Create and load Option Chain Manager
        OptionChainManager chainManager = new OptionChainManager();
        chainManager.loadOptionData(dayData.getOptionData());
        
        // Get a sample timestamp and spot price
        Integer sampleTimestamp = dayData.getOptionData().keySet().iterator().next();
        Double sampleSpotPrice = dayData.getSpotData().get(sampleTimestamp);
        
        if (sampleSpotPrice == null) {
            System.out.println("No spot price data available for timestamp " + sampleTimestamp);
            return;
        }
        
        System.out.println("\nAnalyzing timestamp: " + sampleTimestamp + ", Spot Price: $" + sampleSpotPrice);
        
        // Demonstrate various capabilities
        demonstrateStrikeSelection(chainManager, sampleSpotPrice, sampleTimestamp);
        demonstrateOtmItmAnalysis(chainManager, sampleSpotPrice, sampleTimestamp);
        demonstrateDataValidation(chainManager, sampleSpotPrice, sampleTimestamp);
        demonstrateCachePerformance(chainManager, sampleSpotPrice, sampleTimestamp);
        
        System.out.println("\n=== Option Chain Manager Demo Complete ===");
    }
    
    private static void demonstrateStrikeSelection(OptionChainManager manager, double spotPrice, int timestamp) {
        System.out.println("\n--- Strike Selection Demo ---");
        
        // Get strikes near spot
        List<Double> nearStrikes = manager.getStrikesNearSpot(spotPrice, 10);
        System.out.println("10 strikes nearest to spot ($" + spotPrice + "): " + nearStrikes);
        
        // Get ATM strike
        Double atmStrike = manager.getAtmStrike(spotPrice, timestamp);
        System.out.println("ATM Strike: $" + atmStrike);
        
        // Get strikes in range
        List<Double> rangeStrikes = manager.getStrikesInRange(spotPrice, 3.0, timestamp);
        System.out.println("Strikes within 3% of spot: " + rangeStrikes);
        
        // Available strikes at timestamp
        Map<String, List<Double>> availableStrikes = manager.getAvailableStrikesAtTimestamp(timestamp);
        System.out.println("Available CE strikes: " + availableStrikes.get("CE").size());
        System.out.println("Available PE strikes: " + availableStrikes.get("PE").size());
    }
    
    private static void demonstrateOtmItmAnalysis(OptionChainManager manager, double spotPrice, int timestamp) {
        System.out.println("\n--- OTM/ITM Analysis ---");
        
        // CE analysis
        List<Double> ceOtmStrikes = manager.getOtmStrikes(spotPrice, "CE", timestamp);
        List<Double> ceItmStrikes = manager.getItmStrikes(spotPrice, "CE", timestamp);
        
        System.out.println("CE OTM strikes (above $" + spotPrice + "): " + 
                          ceOtmStrikes.subList(0, Math.min(5, ceOtmStrikes.size())));
        System.out.println("CE ITM strikes (below $" + spotPrice + "): " + 
                          ceItmStrikes.subList(Math.max(0, ceItmStrikes.size() - 5), ceItmStrikes.size()));
        
        // PE analysis
        List<Double> peOtmStrikes = manager.getOtmStrikes(spotPrice, "PE", timestamp);
        List<Double> peItmStrikes = manager.getItmStrikes(spotPrice, "PE", timestamp);
        
        System.out.println("PE OTM strikes (below $" + spotPrice + "): " + 
                          peOtmStrikes.subList(Math.max(0, peOtmStrikes.size() - 5), peOtmStrikes.size()));
        System.out.println("PE ITM strikes (above $" + spotPrice + "): " + 
                          peItmStrikes.subList(0, Math.min(5, peItmStrikes.size())));
        
        // Show some option prices
        System.out.println("\nSample Option Prices:");
        if (!ceOtmStrikes.isEmpty()) {
            Double ceStrike = ceOtmStrikes.get(0);
            Double cePrice = manager.getOptionPrice(timestamp, "CE", ceStrike);
            System.out.println("CE $" + ceStrike + " = $" + cePrice);
        }
        
        if (!peOtmStrikes.isEmpty()) {
            Double peStrike = peOtmStrikes.get(peOtmStrikes.size() - 1);
            Double pePrice = manager.getOptionPrice(timestamp, "PE", peStrike);
            System.out.println("PE $" + peStrike + " = $" + pePrice);
        }
    }
    
    private static void demonstrateDataValidation(OptionChainManager manager, double spotPrice, int timestamp) {
        System.out.println("\n--- Data Validation Demo ---");
        
        // Test with strikes that should exist
        List<Double> nearStrikes = manager.getStrikesNearSpot(spotPrice, 5);
        OptionChainManager.ValidationResult validResult = manager.validateDataCompleteness(timestamp, nearStrikes);
        
        System.out.println("Validation for nearby strikes: " + validResult);
        
        // Test with strikes that might not exist
        List<Double> extremeStrikes = Arrays.asList(spotPrice + 100, spotPrice - 100, spotPrice + 200);
        OptionChainManager.ValidationResult extremeResult = manager.validateDataCompleteness(timestamp, extremeStrikes);
        
        System.out.println("Validation for extreme strikes: " + extremeResult);
        
        if (extremeResult.hasErrors()) {
            System.out.println("Missing strikes detected: " + extremeResult.getMissingStrikes());
        }
    }
    
    private static void demonstrateCachePerformance(OptionChainManager manager, double spotPrice, int timestamp) {
        System.out.println("\n--- Cache Performance Demo ---");
        
        // Perform operations to populate cache
        long startTime = System.nanoTime();
        
        // First round - should populate cache
        for (int i = 0; i < 100; i++) {
            manager.getStrikesNearSpot(spotPrice + (i * 0.1), 10);
            manager.getOtmStrikes(spotPrice, "CE", timestamp);
            manager.getItmStrikes(spotPrice, "PE", timestamp);
        }
        
        long firstRoundTime = System.nanoTime() - startTime;
        
        // Second round - should hit cache more often
        startTime = System.nanoTime();
        
        for (int i = 0; i < 100; i++) {
            manager.getStrikesNearSpot(spotPrice + (i * 0.1), 10);
            manager.getOtmStrikes(spotPrice, "CE", timestamp);
            manager.getItmStrikes(spotPrice, "PE", timestamp);
        }
        
        long secondRoundTime = System.nanoTime() - startTime;
        
        // Show cache statistics
        OptionChainManager.CacheStats stats = manager.getCacheStats();
        System.out.println("Cache Statistics: " + stats);
        
        System.out.printf("First round time: %.2f ms%n", firstRoundTime / 1_000_000.0);
        System.out.printf("Second round time: %.2f ms%n", secondRoundTime / 1_000_000.0);
        
        if (secondRoundTime < firstRoundTime) {
            double improvement = ((double) (firstRoundTime - secondRoundTime) / firstRoundTime) * 100;
            System.out.printf("Cache improved performance by %.1f%%%n", improvement);
        }
        
        // Demonstrate cache clearing
        System.out.println("\nClearing caches...");
        manager.clearCaches();
        
        OptionChainManager.CacheStats statsAfterClear = manager.getCacheStats();
        System.out.println("Stats after cache clear: " + statsAfterClear);
    }
}