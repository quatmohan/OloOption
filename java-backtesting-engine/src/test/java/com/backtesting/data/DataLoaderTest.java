package com.backtesting.data;

import com.backtesting.models.TradingDayData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;

/**
 * Unit tests for DataLoader
 */
public class DataLoaderTest {
    
    private DataLoader dataLoader;
    
    @BeforeEach
    public void setUp() {
        dataLoader = new DataLoader("5SecData");
    }
    
    @Test
    public void testDataLoaderInitialization() {
        assertNotNull(dataLoader);
    }
    
    @Test
    public void testGetAvailableDates() {
        List<String> dates = dataLoader.getAvailableDates("QQQ");
        assertNotNull(dates);
        // Note: This test will pass even if no files exist (returns empty list)
    }
    
    @Test
    public void testGetStrikesNearSpot() {
        // Create mock option chain
        Map<String, Map<Double, Double>> optionChain = new HashMap<>();
        Map<Double, Double> ceOptions = new HashMap<>();
        ceOptions.put(575.0, 3.25);
        ceOptions.put(580.0, 2.45);
        ceOptions.put(585.0, 1.85);
        ceOptions.put(590.0, 1.25);
        
        optionChain.put("CE", ceOptions);
        
        List<Double> nearStrikes = dataLoader.getStrikesNearSpot(580.0, optionChain, 3);
        
        assertNotNull(nearStrikes);
        assertTrue(nearStrikes.size() <= 3);
        
        if (!nearStrikes.isEmpty()) {
            // The closest strike should be 580.0
            assertTrue(nearStrikes.contains(580.0));
        }
    }
    
    @Test
    public void testGetOptionPrice() {
        // Create mock option data
        Map<Integer, Map<String, Map<Double, Double>>> optionData = new HashMap<>();
        Map<String, Map<Double, Double>> timestampData = new HashMap<>();
        Map<Double, Double> ceOptions = new HashMap<>();
        ceOptions.put(580.0, 2.45);
        
        timestampData.put("CE", ceOptions);
        optionData.put(930, timestampData);
        
        Double price = dataLoader.getOptionPrice(optionData, 930, "CE", 580.0);
        assertNotNull(price);
        assertEquals(2.45, price, 0.001);
        
        // Test non-existent price
        Double nonExistentPrice = dataLoader.getOptionPrice(optionData, 931, "CE", 580.0);
        assertNull(nonExistentPrice);
    }
    
    @Test
    public void testLoadTradingDayWithNonExistentFile() {
        // Test loading a non-existent date
        TradingDayData data = dataLoader.loadTradingDay("QQQ", "2099-12-31");
        assertNull(data); // Should return null for non-existent files
    }
}