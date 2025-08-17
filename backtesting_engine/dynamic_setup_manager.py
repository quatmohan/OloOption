"""
Dynamic setup management system for adaptive parameter adjustment
"""

import copy
from typing import Dict, List, Optional, Tuple
from .models import TradingSetup, MarketData, Trade, ParameterAdjustment


class DynamicSetupManager:
    """
    Adaptive parameter management that modifies setup configurations based on market regime changes.
    
    Monitors market regime changes from MarketRegimeDetector and dynamically adjusts setup parameters
    (target_pct, stop_loss_pct, scalping_price) to optimize performance for current market conditions.
    """
    
    def __init__(self, base_setups: List[TradingSetup]):
        """
        Initialize dynamic setup manager
        
        Args:
            base_setups: List of base trading setups to manage
        """
        self.base_setups = base_setups
        self.adjusted_setups = [copy.deepcopy(setup) for setup in base_setups]
        
        # Current market regime tracking
        self.current_regime = "UNKNOWN"
        self.regime_confidence = 0.0
        self.last_regime_change_time = 0
        
        # Performance tracking
        self.adjustment_performance: Dict[str, float] = {}  # adjustment_type -> avg_pnl_impact
        self.static_performance: Dict[str, List[float]] = {}  # setup_id -> [pnl_values]
        self.dynamic_performance: Dict[str, List[float]] = {}  # setup_id -> [pnl_values]
        self.adjustment_history: List[ParameterAdjustment] = []
        
        # Strategy activation tracking
        self.paused_strategies: set = set()
        
        # Regime-specific parameter configurations
        self.regime_configs = self._initialize_regime_configs()
        
        # Adjustment statistics
        self.total_adjustments = 0
        self.regime_accuracy_history: List[bool] = []  # Track if regime predictions were accurate
    
    def update_market_regime(self, regime: str, confidence: float, market_data: MarketData) -> None:
        """
        Update market regime and adjust setups accordingly
        
        Args:
            regime: Current market regime classification
            confidence: Confidence level in regime classification (0-1)
            market_data: Current market data
        """
        # Check for regime change
        regime_changed = regime != self.current_regime and self.current_regime != "UNKNOWN"
        
        if regime_changed:
            print(f"🔄 Regime change detected: {self.current_regime} -> {regime} (confidence: {confidence:.2f})")
            self.last_regime_change_time = market_data.timestamp
            
            # Track regime accuracy (simplified - assumes previous regime was correct if confidence was high)
            if self.regime_confidence > 0.7:
                self.regime_accuracy_history.append(True)  # Assume previous regime was accurate
        
        # Update current regime
        self.current_regime = regime
        self.regime_confidence = confidence
        
        # Only adjust if confidence is high enough
        if confidence >= 0.6:
            self._adjust_setups_for_regime(regime, market_data)
    
    def get_adjusted_setups(self) -> List[TradingSetup]:
        """
        Get current adjusted setups (excluding paused strategies)
        
        Returns:
            List of active adjusted setups
        """
        return [setup for setup in self.adjusted_setups 
                if setup.setup_id not in self.paused_strategies]
    
    def should_pause_strategy(self, setup_id: str) -> bool:
        """
        Check if a strategy should be paused based on market conditions
        
        Args:
            setup_id: Strategy setup ID to check
            
        Returns:
            True if strategy should be paused
        """
        return setup_id in self.paused_strategies
    
    def adjust_parameters_for_regime(self, setup: TradingSetup, regime: str) -> TradingSetup:
        """
        Adjust individual setup parameters for specific regime
        
        Args:
            setup: Setup to adjust
            regime: Target regime
            
        Returns:
            Adjusted setup
        """
        adjusted_setup = copy.deepcopy(setup)
        
        if regime in self.regime_configs:
            config = self.regime_configs[regime]
            
            # Apply regime-specific multipliers
            if 'target_pct_multiplier' in config:
                adjusted_setup.target_pct *= config['target_pct_multiplier']
            
            if 'stop_loss_pct_multiplier' in config:
                adjusted_setup.stop_loss_pct *= config['stop_loss_pct_multiplier']
            
            if 'scalping_price_multiplier' in config:
                adjusted_setup.scalping_price *= config['scalping_price_multiplier']
        
        return adjusted_setup
    
    def track_adjustment_performance(self, trade: Trade, was_adjusted: bool) -> None:
        """
        Track performance of dynamic adjustments vs static parameters
        
        Args:
            trade: Completed trade
            was_adjusted: Whether trade was made with adjusted parameters
        """
        setup_id = trade.setup_id
        
        if was_adjusted:
            if setup_id not in self.dynamic_performance:
                self.dynamic_performance[setup_id] = []
            self.dynamic_performance[setup_id].append(trade.pnl)
        else:
            if setup_id not in self.static_performance:
                self.static_performance[setup_id] = []
            self.static_performance[setup_id].append(trade.pnl)
        
        # Update adjustment performance tracking
        adjustment_type = f"{self.current_regime}_{setup_id}"
        if adjustment_type not in self.adjustment_performance:
            self.adjustment_performance[adjustment_type] = 0.0
        
        # Simple running average of P&L impact
        current_avg = self.adjustment_performance[adjustment_type]
        count = len(self.dynamic_performance.get(setup_id, []))
        if count > 0:
            self.adjustment_performance[adjustment_type] = (current_avg * (count - 1) + trade.pnl) / count
    
    def get_regime_specific_config(self, regime: str) -> Dict[str, Dict[str, float]]:
        """
        Get regime-specific configuration
        
        Args:
            regime: Market regime
            
        Returns:
            Configuration dictionary for the regime
        """
        return self.regime_configs.get(regime, {})
    
    def reset_daily_adjustments(self) -> None:
        """Reset daily adjustment tracking"""
        # Clear daily adjustment history but keep performance tracking
        self.adjustment_history = []
        
        # Reset paused strategies for new day
        self.paused_strategies.clear()
        
        # Reset adjusted setups to base setups
        self.adjusted_setups = [copy.deepcopy(setup) for setup in self.base_setups]
    
    def get_adjustment_statistics(self) -> Dict[str, float]:
        """
        Get comprehensive adjustment statistics
        
        Returns:
            Dictionary of adjustment statistics
        """
        # Calculate static vs dynamic comparison
        static_avg = 0.0
        dynamic_avg = 0.0
        
        all_static_pnls = []
        all_dynamic_pnls = []
        
        for setup_id in self.static_performance:
            all_static_pnls.extend(self.static_performance[setup_id])
        
        for setup_id in self.dynamic_performance:
            all_dynamic_pnls.extend(self.dynamic_performance[setup_id])
        
        if all_static_pnls:
            static_avg = sum(all_static_pnls) / len(all_static_pnls)
        
        if all_dynamic_pnls:
            dynamic_avg = sum(all_dynamic_pnls) / len(all_dynamic_pnls)
        
        # Calculate regime accuracy
        regime_accuracy = (sum(self.regime_accuracy_history) / len(self.regime_accuracy_history) 
                          if self.regime_accuracy_history else 0.0)
        
        return {
            'total_adjustments': self.total_adjustments,
            'static_vs_dynamic_comparison': dynamic_avg - static_avg,
            'regime_accuracy': regime_accuracy,
            'static_avg_pnl': static_avg,
            'dynamic_avg_pnl': dynamic_avg,
            'static_trade_count': len(all_static_pnls),
            'dynamic_trade_count': len(all_dynamic_pnls)
        }
    
    def _adjust_setups_for_regime(self, regime: str, market_data: MarketData) -> None:
        """
        Adjust all setups for the current market regime
        
        Args:
            regime: Current market regime
            market_data: Current market data
        """
        if regime not in self.regime_configs:
            return
        
        config = self.regime_configs[regime]
        
        for i, base_setup in enumerate(self.base_setups):
            # Check if strategy should be paused for this regime
            if self._should_pause_strategy_for_regime(base_setup.setup_id, regime):
                self.paused_strategies.add(base_setup.setup_id)
                continue
            else:
                self.paused_strategies.discard(base_setup.setup_id)
            
            # Apply adjustments
            old_setup = copy.deepcopy(self.adjusted_setups[i])
            self.adjusted_setups[i] = self.adjust_parameters_for_regime(base_setup, regime)
            
            # Track parameter changes
            self._track_parameter_changes(old_setup, self.adjusted_setups[i], regime, market_data.timestamp)
    
    def _should_pause_strategy_for_regime(self, setup_id: str, regime: str) -> bool:
        """
        Determine if a strategy should be paused for the current regime
        
        Args:
            setup_id: Strategy setup ID
            regime: Current market regime
            
        Returns:
            True if strategy should be paused
        """
        # Strategy-specific regime compatibility
        strategy_regime_compatibility = {
            # Straddle strategies work better in ranging/low vol markets
            'straddle': ['RANGING', 'LOW_VOL'],
            'hedged_straddle': ['RANGING', 'LOW_VOL', 'HIGH_VOL'],
            
            # Scalping strategies work better in trending markets
            'ce_scalping': ['TRENDING_UP', 'HIGH_VOL'],
            'pe_scalping': ['TRENDING_DOWN', 'HIGH_VOL'],
            
            # Iron condors work best in ranging markets
            'iron_condor': ['RANGING', 'LOW_VOL'],
            
            # Butterflies work best in low volatility
            'butterfly': ['LOW_VOL', 'RANGING'],
            
            # Vertical spreads work in trending markets
            'vertical_spread': ['TRENDING_UP', 'TRENDING_DOWN'],
            
            # Ratio spreads work in specific volatility conditions
            'ratio_spread': ['RANGING', 'LOW_VOL']
        }
        
        # Extract strategy type from setup_id (simplified)
        strategy_type = None
        for key in strategy_regime_compatibility:
            if key in setup_id.lower():
                strategy_type = key
                break
        
        if strategy_type and strategy_type in strategy_regime_compatibility:
            compatible_regimes = strategy_regime_compatibility[strategy_type]
            return regime not in compatible_regimes
        
        # If we can't determine strategy type, don't pause
        return False
    
    def _track_parameter_changes(self, old_setup: TradingSetup, new_setup: TradingSetup, 
                                regime: str, timestamp: int) -> None:
        """
        Track parameter changes for reporting
        
        Args:
            old_setup: Setup before adjustment
            new_setup: Setup after adjustment
            regime: Current regime that triggered adjustment
            timestamp: Current timestamp
        """
        # Track target_pct changes
        if abs(old_setup.target_pct - new_setup.target_pct) > 0.001:
            self.adjustment_history.append(ParameterAdjustment(
                timestamp=timestamp,
                setup_id=new_setup.setup_id,
                parameter_name='target_pct',
                old_value=old_setup.target_pct,
                new_value=new_setup.target_pct,
                reason=f'regime_change_to_{regime}'
            ))
            self.total_adjustments += 1
        
        # Track stop_loss_pct changes
        if abs(old_setup.stop_loss_pct - new_setup.stop_loss_pct) > 0.001:
            self.adjustment_history.append(ParameterAdjustment(
                timestamp=timestamp,
                setup_id=new_setup.setup_id,
                parameter_name='stop_loss_pct',
                old_value=old_setup.stop_loss_pct,
                new_value=new_setup.stop_loss_pct,
                reason=f'regime_change_to_{regime}'
            ))
            self.total_adjustments += 1
        
        # Track scalping_price changes
        if abs(old_setup.scalping_price - new_setup.scalping_price) > 0.001:
            self.adjustment_history.append(ParameterAdjustment(
                timestamp=timestamp,
                setup_id=new_setup.setup_id,
                parameter_name='scalping_price',
                old_value=old_setup.scalping_price,
                new_value=new_setup.scalping_price,
                reason=f'regime_change_to_{regime}'
            ))
            self.total_adjustments += 1
    
    def _initialize_regime_configs(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize regime-specific parameter configurations
        
        Returns:
            Dictionary mapping regimes to parameter adjustments
        """
        return {
            'TRENDING_UP': {
                'target_pct_multiplier': 1.2,  # Increase targets in trending markets
                'stop_loss_pct_multiplier': 0.8,  # Tighter stops in trending markets
                'scalping_price_multiplier': 1.1,  # Slightly higher premium requirements
                'description': 'Strong upward trend - favor directional strategies'
            },
            
            'TRENDING_DOWN': {
                'target_pct_multiplier': 1.2,  # Increase targets in trending markets
                'stop_loss_pct_multiplier': 0.8,  # Tighter stops in trending markets
                'scalping_price_multiplier': 1.1,  # Slightly higher premium requirements
                'description': 'Strong downward trend - favor directional strategies'
            },
            
            'HIGH_VOL': {
                'target_pct_multiplier': 1.5,  # Higher targets in high volatility
                'stop_loss_pct_multiplier': 1.3,  # Wider stops for volatility
                'scalping_price_multiplier': 1.3,  # Higher premium requirements
                'description': 'High volatility - adjust for larger price swings'
            },
            
            'LOW_VOL': {
                'target_pct_multiplier': 0.8,  # Lower targets in low volatility
                'stop_loss_pct_multiplier': 0.9,  # Tighter stops in low volatility
                'scalping_price_multiplier': 0.8,  # Lower premium requirements
                'description': 'Low volatility - favor premium selling strategies'
            },
            
            'RANGING': {
                'target_pct_multiplier': 1.0,  # Keep targets neutral in ranging markets
                'stop_loss_pct_multiplier': 1.1,  # Slightly wider stops for chop
                'scalping_price_multiplier': 0.9,  # Lower premium requirements
                'description': 'Ranging market - favor neutral strategies'
            }
        }