package com.backtesting.engine;

import com.backtesting.models.*;
import com.backtesting.strategies.StraddleSetup;
import com.backtesting.strategies.TradingSetup;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;

/**
 * Unit tests for BacktestEngine
 */
public class BacktestEngineTest {
    
    private BacktestEngine engine;
    private List<TradingSetup> setups;
    
    @BeforeEach
    public void setUp() {
        // Create a simple straddle setup for testing
        TradingSetup straddleSetup = new StraddleSetup(
            "TestStraddle",
            50.0,   // target
            -100.0, // stop loss
            930     // entry time
        );
        
        setups = Arrays.asList(straddleSetup);
        engine = new BacktestEngine("5SecData", setups, 500.0);
    }
    
    @Test
    public void testEngineInitialization() {
        assertNotNull(engine);
    }
    
    @Test
    public void testProcessTimeInterval() {
        // Create mock market data
        Map<String, Map<Double, Double>> optionPrices = new HashMap<>();
        Map<Double, Double> ceOptions = new HashMap<>();
        ceOptions.put(580.0, 2.45);
        ceOptions.put(585.0, 1.85);
        
        Map<Double, Double> peOptions = new HashMap<>();
        peOptions.put(575.0, 1.95);
        peOptions.put(580.0, 2.15);
        
        optionPrices.put("CE", ceOptions);
        optionPrices.put("PE", peOptions);
        
        MarketData marketData = new MarketData(
            930,        // timestamp
            580.0,      // spot price
            optionPrices,
            Arrays.asList(575.0, 580.0, 585.0)
        );
        
        // Process the interval
        List<Trade> trades = engine.processTimeInterval(marketData, "2025-08-13");
        
        // Should create positions but no trades yet (positions just opened)
        assertNotNull(trades);
    }
    
    @Test
    public void testRiskLimitCheck() {
        // Test that risk limit checking doesn't throw exceptions
        boolean riskLimitHit = engine.checkDailyRiskLimits();
        assertFalse(riskLimitHit); // Should be false initially
    }
    
    @Test
    public void testStraddleSetupCreation() {
        TradingSetup setup = setups.get(0);
        assertEquals("TestStraddle", setup.getSetupId());
        assertEquals(50.0, setup.getTargetPct());
        assertEquals(-100.0, setup.getStopLossPct());
        assertEquals(930, setup.getEntryTimeindex());
    }
    
    @Test
    public void testMarketDataCreation() {
        Map<String, Map<Double, Double>> optionPrices = new HashMap<>();
        MarketData marketData = new MarketData(930, 580.0, optionPrices, new ArrayList<>());
        
        assertEquals(930, marketData.getTimestamp());
        assertEquals(580.0, marketData.getSpotPrice());
        assertNotNull(marketData.getOptionPrices());
        assertNotNull(marketData.getAvailableStrikes());
    }
}