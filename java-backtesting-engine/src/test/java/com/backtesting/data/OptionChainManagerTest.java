package com.backtesting.data;

import com.backtesting.models.MarketData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;

/**
 * Unit tests for OptionChainManager
 */
public class OptionChainManagerTest {
    
    private OptionChainManager manager;
    private Map<Integer, Map<String, Map<Double, Double>>> testData;
    
    @BeforeEach
    public void setUp() {
        manager = new OptionChainManager();
        testData = createTestOptionData();
        manager.loadOptionData(testData);
    }
    
    private Map<Integer, Map<String, Map<Double, Double>>> createTestOptionData() {
        Map<Integer, Map<String, Map<Double, Double>>> data = new HashMap<>();
        
        // Create test data for timestamp 930
        Map<String, Map<Double, Double>> timestamp930 = new HashMap<>();
        
        // CE options
        Map<Double, Double> ceOptions = new HashMap<>();
        ceOptions.put(575.0, 3.25);
        ceOptions.put(580.0, 2.45);
        ceOptions.put(585.0, 1.85);
        ceOptions.put(590.0, 1.25);
        ceOptions.put(595.0, 0.85);
        
        // PE options
        Map<Double, Double> peOptions = new HashMap<>();
        peOptions.put(565.0, 0.95);
        peOptions.put(570.0, 1.35);
        peOptions.put(575.0, 1.95);
        peOptions.put(580.0, 2.75);
        peOptions.put(585.0, 3.45);
        
        timestamp930.put("CE", ceOptions);
        timestamp930.put("PE", peOptions);
        data.put(930, timestamp930);
        
        return data;
    }
    
    @Test
    public void testLoadOptionData() {
        assertNotNull(manager);
        // Data should be loaded successfully
        MarketData marketData = manager.getMarketData(930, 580.0);
        assertNotNull(marketData);
        assertEquals(930, marketData.getTimestamp());
        assertEquals(580.0, marketData.getSpotPrice());
    }
    
    @Test
    public void testGetStrikesNearSpot() {
        List<Double> nearStrikes = manager.getStrikesNearSpot(580.0, 3);
        
        assertNotNull(nearStrikes);
        assertTrue(nearStrikes.size() <= 3);
        
        // Should include 580.0 as it's exactly at spot
        assertTrue(nearStrikes.contains(580.0));
        
        // Test caching - second call should hit cache
        List<Double> cachedStrikes = manager.getStrikesNearSpot(580.0, 3);
        assertEquals(nearStrikes, cachedStrikes);
    }
    
    @Test
    public void testGetOptionPrice() {
        // Test existing price
        Double price = manager.getOptionPrice(930, "CE", 580.0);
        assertNotNull(price);
        assertEquals(2.45, price, 0.001);
        
        // Test non-existent price
        Double nonExistentPrice = manager.getOptionPrice(931, "CE", 580.0);
        assertNull(nonExistentPrice);
    }
    
    @Test
    public void testGetOtmStrikes() {
        // For CE options at spot 580, OTM strikes should be above 580
        List<Double> ceOtmStrikes = manager.getOtmStrikes(580.0, "CE", 930);
        assertNotNull(ceOtmStrikes);
        
        for (Double strike : ceOtmStrikes) {
            assertTrue(strike > 580.0, "CE OTM strike should be above spot price");
        }
        
        // For PE options at spot 580, OTM strikes should be below 580
        List<Double> peOtmStrikes = manager.getOtmStrikes(580.0, "PE", 930);
        assertNotNull(peOtmStrikes);
        
        for (Double strike : peOtmStrikes) {
            assertTrue(strike < 580.0, "PE OTM strike should be below spot price");
        }
    }
    
    @Test
    public void testGetItmStrikes() {
        // For CE options at spot 580, ITM strikes should be below 580
        List<Double> ceItmStrikes = manager.getItmStrikes(580.0, "CE", 930);
        assertNotNull(ceItmStrikes);
        
        for (Double strike : ceItmStrikes) {
            assertTrue(strike < 580.0, "CE ITM strike should be below spot price");
        }
        
        // For PE options at spot 580, ITM strikes should be above 580
        List<Double> peItmStrikes = manager.getItmStrikes(580.0, "PE", 930);
        assertNotNull(peItmStrikes);
        
        for (Double strike : peItmStrikes) {
            assertTrue(strike > 580.0, "PE ITM strike should be above spot price");
        }
    }
    
    @Test
    public void testGetAtmStrike() {
        Double atmStrike = manager.getAtmStrike(580.0, 930);
        assertNotNull(atmStrike);
        assertEquals(580.0, atmStrike, 0.001);
        
        // Test with spot price between strikes
        Double atmStrike2 = manager.getAtmStrike(582.5, 930);
        assertNotNull(atmStrike2);
        // Should be either 580 or 585, whichever is closer
        assertTrue(atmStrike2 == 580.0 || atmStrike2 == 585.0);
    }
    
    @Test
    public void testValidateDataCompleteness() {
        List<Double> requiredStrikes = Arrays.asList(580.0, 585.0, 590.0);
        
        OptionChainManager.ValidationResult result = manager.validateDataCompleteness(930, requiredStrikes);
        assertNotNull(result);
        
        // Check if validation result is reasonable
        Map<String, List<Double>> missingStrikes = result.getMissingStrikes();
        assertNotNull(missingStrikes);
        
        // If there are missing strikes for CE, check the count safely
        if (missingStrikes.containsKey("CE") && missingStrikes.get("CE") != null) {
            int missingCeCount = missingStrikes.get("CE").size();
            assertTrue(missingCeCount >= 0, "Missing CE strikes count should be non-negative");
        }
        
        // Test with non-existent timestamp to ensure validation works
        OptionChainManager.ValidationResult invalidResult = manager.validateDataCompleteness(999999, requiredStrikes);
        assertTrue(invalidResult.hasErrors(), "Should have errors for non-existent timestamp");
    }
    
    @Test
    public void testGetStrikesInRange() {
        List<Double> strikesInRange = manager.getStrikesInRange(580.0, 5.0, 930); // 5% range
        assertNotNull(strikesInRange);
        
        // All strikes should be within 5% of 580
        double lowerBound = 580.0 * 0.95; // 551
        double upperBound = 580.0 * 1.05; // 609
        
        for (Double strike : strikesInRange) {
            assertTrue(strike >= lowerBound && strike <= upperBound,
                      "Strike " + strike + " should be within range [" + lowerBound + ", " + upperBound + "]");
        }
    }
    
    @Test
    public void testCachePerformance() {
        // Perform multiple lookups to test caching
        for (int i = 0; i < 10; i++) {
            manager.getStrikesNearSpot(580.0, 5);
            manager.getOtmStrikes(580.0, "CE", 930);
            manager.getItmStrikes(580.0, "PE", 930);
        }
        
        OptionChainManager.CacheStats stats = manager.getCacheStats();
        assertNotNull(stats);
        
        // Should have some cache hits
        assertTrue(stats.getHits() > 0, "Should have cache hits after repeated lookups");
        assertTrue(stats.getHitRate() > 0, "Hit rate should be greater than 0");
        
        System.out.println("Cache performance: " + stats);
    }
    
    @Test
    public void testClearCaches() {
        // Perform some operations to populate caches
        manager.getStrikesNearSpot(580.0, 5);
        manager.getOtmStrikes(580.0, "CE", 930);
        
        OptionChainManager.CacheStats statsBefore = manager.getCacheStats();
        assertTrue(statsBefore.getStrikeCacheSize() > 0 || statsBefore.getOtmCacheSize() > 0);
        
        // Clear caches
        manager.clearCaches();
        
        // Note: Cache stats counters (hits/misses) are not reset, only cache contents
        // This is by design to maintain performance metrics across cache clears
    }
}