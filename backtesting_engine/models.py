"""
Core data models for the options backtesting engine
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from abc import ABC, abstractmethod


@dataclass
class TradingDayData:
    """Container for all data related to a single trading day"""
    date: str
    spot_data: Dict[int, float]  # timestamp -> spot_price
    option_data: Dict[int, Dict[str, Dict[float, float]]]  # timestamp -> {CE/PE -> {strike -> price}}
    job_end_idx: int  # from .prop file - last valid timeindex for the day
    metadata: Dict  # other data from .prop file


@dataclass
class MultiSymbolTradingData:
    """Container for multi-symbol trading data with regime tracking"""
    date: str
    symbol: str  # "QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"
    spot_data: Dict[int, float]  # timestamp -> spot_price
    option_data: Dict[int, Dict[str, Dict[float, float]]]  # timestamp -> {CE/PE -> {strike -> price}}
    job_end_idx: int  # from .prop file - last valid timeindex for the day
    metadata: Dict  # other data from .prop file
    
    # Market regime tracking
    volatility_history: List[float] = field(default_factory=list)
    price_momentum: List[float] = field(default_factory=list)
    regime_indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketData:
    """Market data at a specific timestamp with regime indicators"""
    timestamp: int
    symbol: str
    spot_price: float
    option_prices: Dict[str, Dict[float, float]]  # {CE/PE -> {strike -> price}}
    available_strikes: List[float]
    
    # Market condition indicators
    price_velocity: float = 0.0
    estimated_volatility: float = 0.0
    trend_strength: float = 0.0
    regime_classification: str = "UNKNOWN"  # TRENDING_UP, TRENDING_DOWN, RANGING, HIGH_VOL, LOW_VOL


@dataclass
class Position:
    """Represents a single options position (e.g., short straddle, iron condor, butterfly)"""
    setup_id: str
    entry_timeindex: int
    entry_prices: Dict[str, float]  # {option_key -> entry_price_with_slippage}
    strikes: Dict[str, float]  # {option_type -> strike} or {option_type_action -> strike}
    quantity: int
    lot_size: int = 100
    target_pnl: float = 0.0
    stop_loss_pnl: float = 0.0
    current_pnl: float = 0.0
    position_type: str = "SELL"  # "SELL", "BUY", "IRON_CONDOR", "BUTTERFLY", "VERTICAL_SPREAD", "RATIO_SPREAD", "HEDGED", "VOLATILITY_SKEW", "GAMMA_SCALP", "GAMMA_SCALP_REBALANCED"
    force_close_timeindex: int = 4650
    slippage: float = 0.005
    symbol: str = ""  # Symbol for multi-symbol support
    
    # Gamma scalping specific fields
    gamma_pnl: float = 0.0  # P&L from underlying movement
    theta_pnl: float = 0.0  # P&L from time decay
    current_delta: float = 0.0  # Current position delta
    rebalance_count: int = 0  # Number of rebalances performed
    
    # Multi-leg position specific fields
    leg_count: int = 1  # Number of legs in the position
    max_risk: float = 0.0  # Maximum theoretical risk for the position
    max_profit: float = 0.0  # Maximum theoretical profit for the position
    breakeven_points: List[float] = field(default_factory=list)  # Breakeven price points
    
    # Risk management flags
    unlimited_risk: bool = False  # True for positions with unlimited risk (e.g., ratio spreads)
    requires_coordination: bool = False  # True if all legs must be closed together
    partial_closure_allowed: bool = True  # False if position cannot be partially closed


@dataclass
class Trade:
    """Completed trade record"""
    setup_id: str
    entry_timeindex: int
    exit_timeindex: int
    entry_prices: Dict[str, float]
    exit_prices: Dict[str, float]
    strikes: Dict[str, float]
    quantity: int
    pnl: float
    exit_reason: str  # "TARGET", "STOP_LOSS", "TIME_BASED", "FORCE_CLOSE", "DAILY_LIMIT", "CROSS_SYMBOL_LIMIT"
    date: str = ""  # Trading date
    symbol: str = ""  # Symbol for multi-symbol support
    
    # Gamma scalping specific fields
    gamma_pnl: float = 0.0  # P&L from underlying movement
    theta_pnl: float = 0.0  # P&L from time decay
    final_delta: float = 0.0  # Final position delta at exit
    rebalance_count: int = 0  # Number of rebalances performed during trade


@dataclass
class TradeSignal:
    """Signal to open or close positions"""
    setup_id: str
    signal_type: str  # 'OPEN', 'CLOSE'
    positions_to_create: List[Position]
    positions_to_close: List[str]  # position_ids


@dataclass
class RegimeTransition:
    """Record of a market regime transition"""
    timestamp: int
    from_regime: str
    to_regime: str
    confidence: float


@dataclass
class ParameterAdjustment:
    """Record of a dynamic parameter adjustment"""
    timestamp: int
    setup_id: str
    parameter_name: str
    old_value: float
    new_value: float
    reason: str


@dataclass
class DailyResults:
    """Results for a single trading day"""
    date: str
    daily_pnl: float
    trades_count: int
    positions_forced_closed_at_job_end: int
    setup_pnls: Dict[str, float]
    symbol_pnls: Dict[str, float] = field(default_factory=dict)
    regime_transitions: List[RegimeTransition] = field(default_factory=list)
    parameter_adjustments: List[ParameterAdjustment] = field(default_factory=list)


@dataclass
class RegimeResults:
    """Performance results for a specific market regime"""
    regime: str
    total_pnl: float
    total_trades: int
    win_rate: float
    avg_duration: float
    transition_performance: float


@dataclass
class SymbolResults:
    """Performance results for a specific symbol"""
    symbol: str
    total_pnl: float
    total_trades: int
    win_rate: float
    correlation_with_other_symbols: Dict[str, float]


@dataclass
class DynamicAdjustmentResults:
    """Results tracking dynamic parameter adjustments"""
    total_adjustments: int
    adjustment_performance: Dict[str, float]  # adjustment_type -> avg_pnl_impact
    static_vs_dynamic_comparison: float
    regime_accuracy: float


@dataclass
class BacktestResults:
    """Complete backtesting results"""
    total_pnl: float
    daily_results: List[DailyResults]
    trade_log: List[Trade]
    setup_performance: Dict[str, 'SetupResults']
    symbol_performance: Dict[str, SymbolResults] = field(default_factory=dict)
    regime_performance: Dict[str, RegimeResults] = field(default_factory=dict)
    dynamic_adjustment_performance: Optional[DynamicAdjustmentResults] = None
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0


@dataclass
class SetupResults:
    """Performance results for a specific setup"""
    setup_id: str
    total_pnl: float
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    regime_performance: Dict[str, float] = field(default_factory=dict)
    symbol_performance: Dict[str, float] = field(default_factory=dict)


class TradingSetup(ABC):
    """Abstract base class for different trading strategies"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2):
        self.setup_id = setup_id
        self.target_pct = target_pct
        self.stop_loss_pct = stop_loss_pct
        self.entry_timeindex = entry_timeindex
        self.close_timeindex = close_timeindex
        self.strike_selection = strike_selection
        self.scalping_price = scalping_price
        self.strikes_away = strikes_away
    
    @abstractmethod
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met"""
        pass
    
    @abstractmethod
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on strategy logic"""
        pass
    
    @abstractmethod
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create positions when entry conditions are met"""
        pass
    
    def should_force_close(self, current_timeindex: int) -> bool:
        """Check if time-based close needed"""
        return current_timeindex >= self.close_timeindex
    
    def reset_daily_state(self):
        """Reset daily state for new trading day - override in subclasses if needed"""
        pass