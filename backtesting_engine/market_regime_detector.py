"""
Market regime detection system for real-time market analysis
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
from .models import MarketData


class MarketRegimeDetector:
    """
    Real-time market condition analysis and regime classification using only price and time data.
    
    Detects market regimes including:
    - TRENDING_UP: Strong upward price movement
    - TRENDING_DOWN: Strong downward price movement  
    - RANGING: Sideways/choppy price action
    - HIGH_VOL: High volatility periods
    - LOW_VOL: Low volatility periods
    """
    
    def __init__(self, lookback_periods: int = 60):
        """
        Initialize market regime detector
        
        Args:
            lookback_periods: Number of 5-second periods to look back (default 60 = 5 minutes)
        """
        self.lookback_periods = lookback_periods
        
        # Price history for calculations
        self.price_history: deque = deque(maxlen=lookback_periods)
        self.timestamp_history: deque = deque(maxlen=lookback_periods)
        
        # Option price history for volatility estimation
        self.option_price_history: deque = deque(maxlen=lookback_periods)
        
        # Calculated indicators
        self.current_regime = "UNKNOWN"
        self.regime_confidence = 0.0
        self.price_velocity = 0.0
        self.trend_strength = 0.0
        self.estimated_volatility = 0.0
        
        # Time-of-day effects tracking
        self.time_effects: Dict[int, Dict[str, float]] = {}  # timeindex -> {metric -> value}
        
        # Regime change detection
        self.previous_regime = "UNKNOWN"
        self.regime_change_count = 0
        
        # Cross-symbol correlation (will be updated externally)
        self.cross_symbol_correlation = 0.0
    
    def update_market_data(self, market_data: MarketData) -> None:
        """
        Update market data and recalculate regime indicators
        
        Args:
            market_data: Current market data snapshot
        """
        # Store price and timestamp
        self.price_history.append(market_data.spot_price)
        self.timestamp_history.append(market_data.timestamp)
        
        # Store option prices for volatility estimation
        if market_data.option_prices:
            # Calculate average option price change for volatility estimation
            avg_option_price = self._calculate_average_option_price(market_data.option_prices)
            self.option_price_history.append(avg_option_price)
        
        # Need at least 2 data points for calculations
        if len(self.price_history) < 2:
            return
        
        # Calculate all indicators
        self.price_velocity = self._calculate_price_velocity()
        self.trend_strength = self._calculate_trend_strength()
        self.estimated_volatility = self._calculate_volatility_estimate()
        
        # Classify current regime
        self.previous_regime = self.current_regime
        self.current_regime, self.regime_confidence = self._classify_market_regime()
        
        # Track regime changes
        if self.current_regime != self.previous_regime and self.previous_regime != "UNKNOWN":
            self.regime_change_count += 1
        
        # Update time-of-day effects
        self._update_time_effects(market_data.timestamp)
        
        # Update market data with calculated indicators
        market_data.price_velocity = self.price_velocity
        market_data.estimated_volatility = self.estimated_volatility
        market_data.trend_strength = self.trend_strength
        market_data.regime_classification = self.current_regime
    
    def get_current_regime(self) -> str:
        """Get current market regime classification"""
        return self.current_regime
    
    def get_volatility_estimate(self) -> float:
        """Get current volatility estimate"""
        return self.estimated_volatility
    
    def get_trend_strength(self) -> float:
        """Get current trend strength (-1 to 1, negative = down trend)"""
        return self.trend_strength
    
    def get_price_velocity(self) -> float:
        """Get current price velocity (rate of change)"""
        return self.price_velocity
    
    def detect_regime_change(self) -> bool:
        """Check if regime has changed from previous update"""
        return self.current_regime != self.previous_regime and self.previous_regime != "UNKNOWN"
    
    def get_regime_confidence(self) -> float:
        """Get confidence level in current regime classification (0-1)"""
        return self.regime_confidence
    
    def analyze_time_effects(self, current_time: int) -> Dict[str, float]:
        """
        Analyze time-of-day effects for current time
        
        Args:
            current_time: Current timestamp
            
        Returns:
            Dictionary of time-based metrics
        """
        # Round to nearest 5-minute bucket for time effects
        time_bucket = (current_time // 300) * 300
        
        if time_bucket in self.time_effects:
            return self.time_effects[time_bucket].copy()
        
        return {
            'avg_volatility': self.estimated_volatility,
            'avg_trend_strength': abs(self.trend_strength),
            'regime_stability': 1.0 - (self.regime_change_count / max(len(self.price_history), 1))
        }
    
    def detect_cross_symbol_divergence(self, other_detector: 'MarketRegimeDetector') -> float:
        """
        Detect divergence between this detector and another symbol's detector
        
        Args:
            other_detector: Another MarketRegimeDetector instance
            
        Returns:
            Divergence score (0-1, higher = more divergent)
        """
        if not other_detector or len(other_detector.price_history) < 2:
            return 0.0
        
        # Compare regime classifications
        regime_divergence = 0.0 if self.current_regime == other_detector.current_regime else 1.0
        
        # Compare trend directions
        trend_divergence = abs(self.trend_strength - other_detector.trend_strength) / 2.0
        
        # Compare volatility levels
        vol_divergence = abs(self.estimated_volatility - other_detector.estimated_volatility) / max(
            self.estimated_volatility + other_detector.estimated_volatility, 0.01)
        
        # Weighted average
        total_divergence = (regime_divergence * 0.5 + trend_divergence * 0.3 + vol_divergence * 0.2)
        
        return min(total_divergence, 1.0)
    
    def _calculate_price_velocity(self) -> float:
        """Calculate price velocity (rate of change per period)"""
        if len(self.price_history) < 2:
            return 0.0
        
        # Calculate velocity over multiple periods for smoothing
        periods_to_check = min(5, len(self.price_history) - 1)
        
        total_change = 0.0
        for i in range(periods_to_check):
            current_price = self.price_history[-(i+1)]
            previous_price = self.price_history[-(i+2)]
            total_change += (current_price - previous_price) / previous_price
        
        return total_change / periods_to_check
    
    def _calculate_trend_strength(self) -> float:
        """Calculate trend strength (-1 to 1, negative = downtrend)"""
        if len(self.price_history) < 10:
            return 0.0
        
        # Use linear regression slope over lookback period
        prices = list(self.price_history)
        n = len(prices)
        
        # Calculate slope using least squares
        x_sum = sum(range(n))
        y_sum = sum(prices)
        xy_sum = sum(i * prices[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        # Normalize slope relative to price level
        avg_price = y_sum / n
        normalized_slope = slope / avg_price if avg_price > 0 else 0.0
        
        # Scale to -1 to 1 range
        return max(-1.0, min(1.0, normalized_slope * 1000))
    
    def _calculate_volatility_estimate(self) -> float:
        """Estimate volatility from price movements and option price changes"""
        if len(self.price_history) < 5:
            return 0.0
        
        # Calculate realized volatility from price changes
        price_returns = []
        for i in range(1, len(self.price_history)):
            if self.price_history[i-1] > 0:
                ret = math.log(self.price_history[i] / self.price_history[i-1])
                price_returns.append(ret)
        
        if not price_returns:
            return 0.0
        
        # Calculate standard deviation of returns
        mean_return = sum(price_returns) / len(price_returns)
        variance = sum((ret - mean_return) ** 2 for ret in price_returns) / len(price_returns)
        volatility = math.sqrt(variance)
        
        # Annualize (assuming 252 trading days, 78 5-second periods per day)
        annualized_vol = volatility * math.sqrt(252 * 78)
        
        # If we have option price data, incorporate that as well
        if len(self.option_price_history) >= 5:
            option_vol = self._estimate_implied_volatility_from_prices()
            # Blend realized and implied volatility estimates
            annualized_vol = 0.7 * annualized_vol + 0.3 * option_vol
        
        return annualized_vol
    
    def _estimate_implied_volatility_from_prices(self) -> float:
        """Estimate implied volatility from option price movements"""
        if len(self.option_price_history) < 5:
            return 0.0
        
        # Calculate volatility of option price changes as proxy for IV
        option_returns = []
        for i in range(1, len(self.option_price_history)):
            if self.option_price_history[i-1] > 0:
                ret = math.log(self.option_price_history[i] / self.option_price_history[i-1])
                option_returns.append(ret)
        
        if not option_returns:
            return 0.0
        
        mean_return = sum(option_returns) / len(option_returns)
        variance = sum((ret - mean_return) ** 2 for ret in option_returns) / len(option_returns)
        option_vol = math.sqrt(variance)
        
        # Convert to annualized estimate (rough approximation)
        # Option prices are more sensitive to volatility, so scale down
        return option_vol * math.sqrt(252 * 78) * 0.5
    
    def _calculate_average_option_price(self, option_prices: Dict[str, Dict[float, float]]) -> float:
        """Calculate average option price across all strikes and types"""
        all_prices = []
        
        for option_type in option_prices:
            for strike, price in option_prices[option_type].items():
                if price > 0:
                    all_prices.append(price)
        
        return sum(all_prices) / len(all_prices) if all_prices else 0.0
    
    def _classify_market_regime(self) -> Tuple[str, float]:
        """
        Classify current market regime based on calculated indicators
        
        Returns:
            Tuple of (regime_name, confidence_score)
        """
        if len(self.price_history) < 10:
            return "UNKNOWN", 0.0
        
        # Thresholds for classification
        HIGH_VOL_THRESHOLD = 0.25  # 25% annualized volatility
        LOW_VOL_THRESHOLD = 0.10   # 10% annualized volatility
        STRONG_TREND_THRESHOLD = 0.3
        WEAK_TREND_THRESHOLD = 0.1
        HIGH_VELOCITY_THRESHOLD = 0.002  # 0.2% per period
        
        confidence = 0.0
        regime = "RANGING"  # Default
        
        # Check trend strength first, then volatility
        if abs(self.trend_strength) > STRONG_TREND_THRESHOLD:
            regime = "TRENDING_UP" if self.trend_strength > 0 else "TRENDING_DOWN"
            confidence = min(0.9, abs(self.trend_strength) + 0.2)
        
        elif self.estimated_volatility > HIGH_VOL_THRESHOLD:
            regime = "HIGH_VOL"
            confidence = min(0.8, self.estimated_volatility / HIGH_VOL_THRESHOLD * 0.5 + 0.3)
        
        elif self.estimated_volatility < LOW_VOL_THRESHOLD:
            # Even in low vol, check for moderate trends
            if abs(self.trend_strength) > WEAK_TREND_THRESHOLD * 2:  # Lower threshold for low vol
                regime = "TRENDING_UP" if self.trend_strength > 0 else "TRENDING_DOWN"
                confidence = min(0.7, abs(self.trend_strength) + 0.2)
            else:
                regime = "LOW_VOL"
                confidence = min(0.8, (LOW_VOL_THRESHOLD - self.estimated_volatility) / LOW_VOL_THRESHOLD * 0.5 + 0.3)
        
        else:
            # Medium volatility - check trend and velocity
            if abs(self.trend_strength) > WEAK_TREND_THRESHOLD * 1.5:
                regime = "TRENDING_UP" if self.trend_strength > 0 else "TRENDING_DOWN"
                confidence = min(0.8, abs(self.trend_strength))
            elif abs(self.trend_strength) < WEAK_TREND_THRESHOLD and abs(self.price_velocity) < HIGH_VELOCITY_THRESHOLD:
                regime = "RANGING"
                confidence = min(0.7, (WEAK_TREND_THRESHOLD - abs(self.trend_strength)) / WEAK_TREND_THRESHOLD * 0.4 + 0.3)
            else:
                # Unclear regime
                regime = "RANGING"
                confidence = 0.3
        
        # Boost confidence if regime is stable
        if regime == self.previous_regime:
            confidence = min(1.0, confidence + 0.1)
        
        return regime, confidence
    
    def _update_time_effects(self, timestamp: int) -> None:
        """Update time-of-day effects tracking"""
        # Round to nearest 5-minute bucket
        time_bucket = (timestamp // 300) * 300
        
        if time_bucket not in self.time_effects:
            self.time_effects[time_bucket] = {
                'avg_volatility': 0.0,
                'avg_trend_strength': 0.0,
                'regime_stability': 0.0,
                'sample_count': 0
            }
        
        effects = self.time_effects[time_bucket]
        count = effects['sample_count']
        
        # Update running averages
        effects['avg_volatility'] = (effects['avg_volatility'] * count + self.estimated_volatility) / (count + 1)
        effects['avg_trend_strength'] = (effects['avg_trend_strength'] * count + abs(self.trend_strength)) / (count + 1)
        
        # Calculate regime stability (lower regime change rate = higher stability)
        stability = 1.0 - (self.regime_change_count / max(len(self.price_history), 1))
        effects['regime_stability'] = (effects['regime_stability'] * count + stability) / (count + 1)
        
        effects['sample_count'] = count + 1
    
    def get_regime_statistics(self) -> Dict[str, float]:
        """Get comprehensive regime statistics"""
        return {
            'current_regime': self.current_regime,
            'regime_confidence': self.regime_confidence,
            'price_velocity': self.price_velocity,
            'trend_strength': self.trend_strength,
            'estimated_volatility': self.estimated_volatility,
            'regime_changes': self.regime_change_count,
            'data_points': len(self.price_history)
        }