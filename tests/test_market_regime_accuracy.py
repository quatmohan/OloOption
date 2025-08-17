#!/usr/bin/env python3
"""
Tests for market regime detection accuracy with historical data patterns
"""

import sys
import os
import unittest
import math
from typing import List, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.market_regime_detector import MarketRegimeDetector
from backtesting_engine.models import MarketData


class TestMarketRegimeAccuracy(unittest.TestCase):
    """Test market regime detection accuracy with various market scenarios"""
    
    def setUp(self):
        """Set up regime detector"""
        self.detector = MarketRegimeDetector(lookback_periods=60)
    
    def create_synthetic_market_data(self, pattern_type: str, length: int = 100) -> List[MarketData]:
        """Create synthetic market data with known patterns"""
        data = []
        base_price = 580.0
        base_timestamp = 1000
        
        if pattern_type == "strong_uptrend":
            # Consistent upward movement with minor pullbacks
            for i in range(length):
                # Main trend up with occasional small pullbacks
                trend_component = i * 0.08
                noise_component = (i % 7 - 3) * 0.02  # Small noise
                price = base_price + trend_component + noise_component
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "strong_downtrend":
            # Consistent downward movement
            for i in range(length):
                trend_component = -i * 0.06
                noise_component = (i % 5 - 2) * 0.015
                price = base_price + trend_component + noise_component
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "tight_range":
            # Sideways movement within narrow range
            for i in range(length):
                range_component = 1.0 * math.sin(i * 0.3)  # Oscillation
                noise_component = (i % 3 - 1) * 0.1
                price = base_price + range_component + noise_component
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "high_volatility":
            # Large, erratic price movements
            for i in range(length):
                # Large random-like movements
                volatility_component = (i % 11 - 5) * 0.8
                secondary_move = (i % 7 - 3) * 0.4
                price = base_price + volatility_component + secondary_move
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "low_volatility":
            # Very small price movements
            for i in range(length):
                small_drift = i * 0.005  # Minimal drift
                tiny_noise = (i % 4 - 1.5) * 0.02  # Very small noise
                price = base_price + small_drift + tiny_noise
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "trend_reversal":
            # Uptrend followed by downtrend
            for i in range(length):
                if i < length // 2:
                    # Uptrend phase
                    trend_component = i * 0.06
                else:
                    # Downtrend phase
                    peak = (length // 2) * 0.06
                    trend_component = peak - (i - length // 2) * 0.08
                
                noise = (i % 6 - 2.5) * 0.02
                price = base_price + trend_component + noise
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        elif pattern_type == "breakout":
            # Range-bound followed by strong breakout
            for i in range(length):
                if i < length * 0.7:
                    # Range-bound phase
                    range_component = 0.8 * math.sin(i * 0.4)
                else:
                    # Breakout phase
                    breakout_start = length * 0.7
                    breakout_component = (i - breakout_start) * 0.15
                    range_component = 0.8 + breakout_component
                
                noise = (i % 5 - 2) * 0.03
                price = base_price + range_component + noise
                
                data.append(self._create_market_data_point(
                    base_timestamp + i * 5, price, i
                ))
        
        return data
    
    def _create_market_data_point(self, timestamp: int, spot_price: float, index: int) -> MarketData:
        """Create a market data point with realistic option prices"""
        # Create option prices based on spot price
        strikes = [spot_price - 10, spot_price - 5, spot_price, spot_price + 5, spot_price + 10]
        
        option_prices = {"CE": {}, "PE": {}}
        
        for strike in strikes:
            # Simple option pricing model
            ce_intrinsic = max(0, spot_price - strike)
            pe_intrinsic = max(0, strike - spot_price)
            
            # Add time value (decreases with time)
            time_value = 2.0 * (1 - index / 200.0) if index < 200 else 0.1
            
            option_prices["CE"][strike] = ce_intrinsic + time_value
            option_prices["PE"][strike] = pe_intrinsic + time_value
        
        return MarketData(
            timestamp=timestamp,
            symbol="QQQ",
            spot_price=spot_price,
            option_prices=option_prices,
            available_strikes=strikes
        )
    
    def test_strong_uptrend_detection(self):
        """Test detection of strong upward trends"""
        uptrend_data = self.create_synthetic_market_data("strong_uptrend", 80)
        
        # Feed data to detector
        for data_point in uptrend_data:
            self.detector.update_market_data(data_point)
        
        # Check final regime
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        trend_strength = self.detector.get_trend_strength()
        velocity = self.detector.get_price_velocity()
        
        self.assertEqual(regime, "TRENDING_UP")
        self.assertGreater(confidence, 0.7, "Confidence should be high for clear uptrend")
        self.assertGreater(trend_strength, 0.5, "Trend strength should be positive and strong")
        self.assertGreater(velocity, 0.0, "Price velocity should be positive")
        
        print(f"Uptrend - Regime: {regime}, Confidence: {confidence:.3f}, "
              f"Trend: {trend_strength:.3f}, Velocity: {velocity:.4f}")
    
    def test_strong_downtrend_detection(self):
        """Test detection of strong downward trends"""
        downtrend_data = self.create_synthetic_market_data("strong_downtrend", 80)
        
        for data_point in downtrend_data:
            self.detector.update_market_data(data_point)
        
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        trend_strength = self.detector.get_trend_strength()
        velocity = self.detector.get_price_velocity()
        
        self.assertEqual(regime, "TRENDING_DOWN")
        self.assertGreater(confidence, 0.7)
        self.assertLess(trend_strength, -0.5, "Trend strength should be negative and strong")
        self.assertLess(velocity, 0.0, "Price velocity should be negative")
        
        print(f"Downtrend - Regime: {regime}, Confidence: {confidence:.3f}, "
              f"Trend: {trend_strength:.3f}, Velocity: {velocity:.4f}")
    
    def test_ranging_market_detection(self):
        """Test detection of ranging/sideways markets"""
        ranging_data = self.create_synthetic_market_data("tight_range", 80)
        
        for data_point in ranging_data:
            self.detector.update_market_data(data_point)
        
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        trend_strength = self.detector.get_trend_strength()
        
        self.assertEqual(regime, "RANGING")
        self.assertGreater(confidence, 0.6)
        self.assertLess(abs(trend_strength), 0.3, "Trend strength should be weak in ranging market")
        
        print(f"Ranging - Regime: {regime}, Confidence: {confidence:.3f}, "
              f"Trend: {trend_strength:.3f}")
    
    def test_high_volatility_detection(self):
        """Test detection of high volatility periods"""
        high_vol_data = self.create_synthetic_market_data("high_volatility", 80)
        
        for data_point in high_vol_data:
            self.detector.update_market_data(data_point)
        
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        volatility = self.detector.get_volatility_estimate()
        
        self.assertEqual(regime, "HIGH_VOL")
        self.assertGreater(confidence, 0.6)
        self.assertGreater(volatility, 0.03, "Volatility should be high")
        
        print(f"High Vol - Regime: {regime}, Confidence: {confidence:.3f}, "
              f"Volatility: {volatility:.4f}")
    
    def test_low_volatility_detection(self):
        """Test detection of low volatility periods"""
        low_vol_data = self.create_synthetic_market_data("low_volatility", 80)
        
        for data_point in low_vol_data:
            self.detector.update_market_data(data_point)
        
        regime = self.detector.get_current_regime()
        confidence = self.detector.get_regime_confidence()
        volatility = self.detector.get_volatility_estimate()
        
        self.assertEqual(regime, "LOW_VOL")
        self.assertGreater(confidence, 0.6)
        self.assertLess(volatility, 0.01, "Volatility should be low")
        
        print(f"Low Vol - Regime: {regime}, Confidence: {confidence:.3f}, "
              f"Volatility: {volatility:.4f}")
    
    def test_regime_change_detection_accuracy(self):
        """Test accuracy of regime change detection"""
        # Start with uptrend
        uptrend_data = self.create_synthetic_market_data("strong_uptrend", 50)
        for data_point in uptrend_data:
            self.detector.update_market_data(data_point)
        
        initial_regime = self.detector.get_current_regime()
        self.assertEqual(initial_regime, "TRENDING_UP")
        
        # Switch to downtrend
        downtrend_data = self.create_synthetic_market_data("strong_downtrend", 50)
        # Adjust starting price to continue from uptrend end
        last_price = uptrend_data[-1].spot_price
        for i, data_point in enumerate(downtrend_data):
            data_point.spot_price = last_price - i * 0.06  # Continue downward
            self.detector.update_market_data(data_point)
        
        final_regime = self.detector.get_current_regime()
        regime_changed = self.detector.detect_regime_change()
        
        self.assertEqual(final_regime, "TRENDING_DOWN")
        self.assertTrue(regime_changed, "Should detect regime change")
        
        print(f"Regime change: {initial_regime} -> {final_regime}, Detected: {regime_changed}")
    
    def test_trend_reversal_pattern(self):
        """Test detection of trend reversal patterns"""
        reversal_data = self.create_synthetic_market_data("trend_reversal", 100)
        
        regimes_detected = []
        
        for i, data_point in enumerate(reversal_data):
            self.detector.update_market_data(data_point)
            
            # Record regime at key points
            if i in [30, 50, 80]:  # Early uptrend, peak, late downtrend
                regime = self.detector.get_current_regime()
                confidence = self.detector.get_regime_confidence()
                regimes_detected.append((i, regime, confidence))
        
        # Should detect uptrend early, then downtrend later
        early_regime = regimes_detected[0][1]  # At point 30
        late_regime = regimes_detected[2][1]   # At point 80
        
        self.assertIn(early_regime, ["TRENDING_UP", "HIGH_VOL"])
        self.assertIn(late_regime, ["TRENDING_DOWN", "HIGH_VOL"])
        
        print(f"Reversal pattern - Early: {early_regime}, Late: {late_regime}")
    
    def test_breakout_pattern_detection(self):
        """Test detection of breakout patterns"""
        breakout_data = self.create_synthetic_market_data("breakout", 100)
        
        regimes_detected = []
        
        for i, data_point in enumerate(breakout_data):
            self.detector.update_market_data(data_point)
            
            # Record regime before and after breakout
            if i in [40, 60, 90]:  # Range phase, early breakout, late breakout
                regime = self.detector.get_current_regime()
                confidence = self.detector.get_regime_confidence()
                regimes_detected.append((i, regime, confidence))
        
        # Should detect ranging early, then trending later
        range_regime = regimes_detected[0][1]   # At point 40
        breakout_regime = regimes_detected[2][1] # At point 90
        
        self.assertIn(range_regime, ["RANGING", "LOW_VOL"])
        self.assertIn(breakout_regime, ["TRENDING_UP", "HIGH_VOL"])
        
        print(f"Breakout pattern - Range: {range_regime}, Breakout: {breakout_regime}")
    
    def test_regime_confidence_accuracy(self):
        """Test that confidence levels are appropriate for different scenarios"""
        test_scenarios = [
            ("strong_uptrend", 0.7),
            ("strong_downtrend", 0.7),
            ("tight_range", 0.6),
            ("high_volatility", 0.6),
            ("low_volatility", 0.6)
        ]
        
        for pattern, min_confidence in test_scenarios:
            with self.subTest(pattern=pattern):
                # Reset detector
                detector = MarketRegimeDetector(lookback_periods=60)
                
                # Feed pattern data
                pattern_data = self.create_synthetic_market_data(pattern, 80)
                for data_point in pattern_data:
                    detector.update_market_data(data_point)
                
                confidence = detector.get_regime_confidence()
                regime = detector.get_current_regime()
                
                self.assertGreater(confidence, min_confidence, 
                                 f"Confidence {confidence:.3f} too low for {pattern} (regime: {regime})")
    
    def test_time_of_day_effects(self):
        """Test time-of-day effect analysis"""
        # Create data with different characteristics at different times
        morning_data = self.create_synthetic_market_data("high_volatility", 30)
        afternoon_data = self.create_synthetic_market_data("low_volatility", 30)
        
        # Update timestamps to reflect different times of day
        for i, data_point in enumerate(morning_data):
            data_point.timestamp = 1000 + i * 5  # Morning
            self.detector.update_market_data(data_point)
        
        morning_effects = self.detector.analyze_time_effects(1100)
        
        for i, data_point in enumerate(afternoon_data):
            data_point.timestamp = 3000 + i * 5  # Afternoon
            self.detector.update_market_data(data_point)
        
        afternoon_effects = self.detector.analyze_time_effects(3100)
        
        # Check that time effects are tracked
        self.assertIsInstance(morning_effects, dict)
        self.assertIsInstance(afternoon_effects, dict)
        self.assertIn("volatility", morning_effects)
        self.assertIn("price_velocity", morning_effects)
        
        print(f"Morning effects: {morning_effects}")
        print(f"Afternoon effects: {afternoon_effects}")
    
    def test_cross_validation_with_known_patterns(self):
        """Cross-validate regime detection with multiple known patterns"""
        test_cases = [
            ("strong_uptrend", "TRENDING_UP", 80),
            ("strong_downtrend", "TRENDING_DOWN", 80),
            ("tight_range", "RANGING", 80),
            ("high_volatility", "HIGH_VOL", 80),
            ("low_volatility", "LOW_VOL", 80)
        ]
        
        results = []
        
        for pattern, expected_regime, length in test_cases:
            # Reset detector for each test
            detector = MarketRegimeDetector(lookback_periods=60)
            
            # Generate and feed data
            pattern_data = self.create_synthetic_market_data(pattern, length)
            for data_point in pattern_data:
                detector.update_market_data(data_point)
            
            # Get results
            detected_regime = detector.get_current_regime()
            confidence = detector.get_regime_confidence()
            
            # Record result
            correct = detected_regime == expected_regime
            results.append((pattern, expected_regime, detected_regime, confidence, correct))
            
            print(f"{pattern}: Expected {expected_regime}, Got {detected_regime}, "
                  f"Confidence: {confidence:.3f}, Correct: {correct}")
        
        # Calculate accuracy
        correct_detections = sum(1 for _, _, _, _, correct in results if correct)
        accuracy = correct_detections / len(results)
        
        self.assertGreater(accuracy, 0.8, f"Accuracy {accuracy:.2f} too low")
        print(f"\nOverall accuracy: {accuracy:.2f} ({correct_detections}/{len(results)})")


def run_regime_accuracy_tests():
    """Run market regime detection accuracy tests"""
    print("Running Market Regime Detection Accuracy Tests")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMarketRegimeAccuracy)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nRegime Detection Tests: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    run_regime_accuracy_tests()