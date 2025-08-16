"""
Core data models for the options backtesting engine
"""

from dataclasses import dataclass
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
class MarketData:
    """Market data at a specific timestamp"""
    timestamp: int
    spot_price: float
    option_prices: Dict[str, Dict[float, float]]  # {CE/PE -> {strike -> price}}
    available_strikes: List[float]


@dataclass
class Position:
    """Represents a single options position (e.g., short straddle)"""
    setup_id: str
    entry_timeindex: int
    entry_prices: Dict[str, float]  # {option_key -> entry_price_with_slippage}
    strikes: Dict[str, float]  # {option_type -> strike}
    quantity: int
    lot_size: int = 100
    target_pnl: float = 0.0
    stop_loss_pnl: float = 0.0
    current_pnl: float = 0.0
    position_type: str = "SELL"  # "SELL" or "BUY"
    force_close_timeindex: int = 4650
    slippage: float = 0.005


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
    exit_reason: str  # "TARGET", "STOP_LOSS", "TIME_BASED", "FORCE_CLOSE", "DAILY_LIMIT"


@dataclass
class TradeSignal:
    """Signal to open or close positions"""
    setup_id: str
    signal_type: str  # 'OPEN', 'CLOSE'
    positions_to_create: List[Position]
    positions_to_close: List[str]  # position_ids


@dataclass
class DailyResults:
    """Results for a single trading day"""
    date: str
    daily_pnl: float
    trades_count: int
    positions_forced_closed_at_job_end: int
    setup_pnls: Dict[str, float]


@dataclass
class BacktestResults:
    """Complete backtesting results"""
    total_pnl: float
    daily_results: List[DailyResults]
    trade_log: List[Trade]
    setup_performance: Dict[str, 'SetupResults']
    win_rate: float
    max_drawdown: float
    total_trades: int


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