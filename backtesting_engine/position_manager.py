"""
Position management and P&L tracking
"""

from typing import Dict, List, Optional
from .models import Position, Trade, MarketData, TradingSetup


class PositionManager:
    """Tracks all open positions and calculates real-time P&L"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}  # position_id -> Position
        self.position_counter = 0
    
    def add_position(self, position: Position) -> str:
        """Add a new position and return position ID"""
        position_id = f"{position.setup_id}_{self.position_counter}"
        self.position_counter += 1
        self.positions[position_id] = position
        return position_id
    
    def update_positions(self, market_data: MarketData, date: str = "") -> List[Trade]:
        """Update all positions and return closed positions as trades"""
        closed_trades = []
        positions_to_remove = []
        
        for position_id, position in self.positions.items():
            # Calculate current P&L
            current_pnl = self._calculate_position_pnl(position, market_data)
            position.current_pnl = current_pnl
            
            # Check exit conditions
            exit_reason = self._check_exit_conditions(position, market_data.timestamp)
            
            if exit_reason:
                trade = self._close_position(position, market_data, exit_reason, date)
                closed_trades.append(trade)
                positions_to_remove.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_remove:
            del self.positions[position_id]
        
        return closed_trades
    
    def check_time_based_closures(self, current_timeindex: int, setups: List[TradingSetup]) -> List[Trade]:
        """Check for time-based position closures"""
        closed_trades = []
        positions_to_remove = []
        
        # Create setup lookup for force close times
        setup_close_times = {setup.setup_id: setup.close_timeindex for setup in setups}
        
        for position_id, position in self.positions.items():
            setup_close_time = setup_close_times.get(position.setup_id, position.force_close_timeindex)
            
            if current_timeindex >= setup_close_time:
                # Create dummy market data for closure (we'll need actual market data in real implementation)
                market_data = MarketData(
                    timestamp=current_timeindex,
                    spot_price=0.0,  # Will be filled by caller
                    option_prices={},  # Will be filled by caller
                    available_strikes=[]
                )
                
                trade = self._close_position(position, market_data, "TIME_BASED")
                closed_trades.append(trade)
                positions_to_remove.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_remove:
            del self.positions[position_id]
        
        return closed_trades
    
    def get_total_pnl(self) -> float:
        """Get total P&L across all positions"""
        return sum(position.current_pnl for position in self.positions.values())
    
    def get_setup_pnl(self, setup_id: str) -> float:
        """Get P&L for a specific setup"""
        return sum(position.current_pnl for position in self.positions.values() 
                  if position.setup_id == setup_id)
    
    def close_all_positions(self, market_data: MarketData, reason: str = "FORCE_CLOSE", date: str = "") -> List[Trade]:
        """Close all open positions"""
        closed_trades = []
        
        for position in self.positions.values():
            trade = self._close_position(position, market_data, reason, date)
            closed_trades.append(trade)
        
        self.positions.clear()
        return closed_trades
    
    def close_setup_positions(self, setup_id: str, market_data: MarketData, reason: str = "SETUP_CLOSE", date: str = "") -> List[Trade]:
        """Close all positions for a specific setup"""
        closed_trades = []
        positions_to_remove = []
        
        for position_id, position in self.positions.items():
            if position.setup_id == setup_id:
                trade = self._close_position(position, market_data, reason, date)
                closed_trades.append(trade)
                positions_to_remove.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_remove:
            del self.positions[position_id]
        
        return closed_trades
    
    def force_close_at_job_end(self, job_end_idx: int, market_data: MarketData, date: str = "") -> List[Trade]:
        """Force close all positions at job end index"""
        return self.close_all_positions(market_data, "JOB_END", date)
    
    def reset_positions(self):
        """Clear all positions for new trading day"""
        self.positions.clear()
        self.position_counter = 0
    
    def _calculate_position_pnl(self, position: Position, market_data: MarketData) -> float:
        """Calculate current P&L for a position"""
        total_pnl = 0.0
        
        for option_key, entry_price in position.entry_prices.items():
            # Parse option key - handle both formats:
            # Simple: "CE_580.0" or Hedged: "CE_580.0_SELL"
            parts = option_key.split('_')
            option_type = parts[0]  # CE or PE
            strike = float(parts[1])
            
            # Determine if this is a SELL or BUY position
            if len(parts) >= 3:  # Hedged position format
                leg_type = parts[2]  # SELL or BUY
            else:  # Simple position format
                leg_type = position.position_type
            
            # Get current market price
            current_price = 0.0
            if (option_type in market_data.option_prices and 
                strike in market_data.option_prices[option_type]):
                current_price = market_data.option_prices[option_type][strike]
            
            # Calculate P&L based on leg type
            if leg_type == "SELL":
                # Selling: P&L = (entry_price - current_price) * quantity * lot_size
                option_pnl = (entry_price - current_price) * position.quantity * position.lot_size
            else:  # BUY
                # Buying: P&L = (current_price - entry_price) * quantity * lot_size
                option_pnl = (current_price - entry_price) * position.quantity * position.lot_size
            
            total_pnl += option_pnl
        
        return total_pnl
    
    def _check_exit_conditions(self, position: Position, current_timeindex: int) -> Optional[str]:
        """Check if position should be closed"""
        # Check target
        if position.target_pnl > 0 and position.current_pnl >= position.target_pnl:
            return "TARGET"
        
        # Check stop loss
        if position.stop_loss_pnl < 0 and position.current_pnl <= position.stop_loss_pnl:
            return "STOP_LOSS"
        
        # Check time-based close
        if current_timeindex >= position.force_close_timeindex:
            return "TIME_BASED"
        
        return None
    
    def _close_position(self, position: Position, market_data: MarketData, exit_reason: str, date: str = "") -> Trade:
        """Close a position and create trade record"""
        exit_prices = {}
        
        # Get exit prices with slippage
        for option_key, entry_price in position.entry_prices.items():
            # Parse option key - handle both formats
            parts = option_key.split('_')
            option_type = parts[0]  # CE or PE
            strike = float(parts[1])
            
            # Determine if this is a SELL or BUY position
            if len(parts) >= 3:  # Hedged position format
                leg_type = parts[2]  # SELL or BUY
            else:  # Simple position format
                leg_type = position.position_type
            
            # Get current market price
            market_price = 0.0
            if (option_type in market_data.option_prices and 
                strike in market_data.option_prices[option_type]):
                market_price = market_data.option_prices[option_type][strike]
            
            # Apply exit slippage based on leg type
            if leg_type == "SELL":
                exit_price = market_price - position.slippage  # Pay slippage to buy back
            else:  # BUY
                exit_price = market_price + position.slippage  # Pay slippage to sell
            
            exit_prices[option_key] = exit_price
        
        # Calculate final P&L with exit slippage
        final_pnl = 0.0
        for option_key, entry_price in position.entry_prices.items():
            exit_price = exit_prices[option_key]
            
            # Parse leg type again for P&L calculation
            parts = option_key.split('_')
            if len(parts) >= 3:
                leg_type = parts[2]
            else:
                leg_type = position.position_type
            
            if leg_type == "SELL":
                option_pnl = (entry_price - exit_price) * position.quantity * position.lot_size
            else:  # BUY
                option_pnl = (exit_price - entry_price) * position.quantity * position.lot_size
            
            final_pnl += option_pnl
        
        return Trade(
            setup_id=position.setup_id,
            entry_timeindex=position.entry_timeindex,
            exit_timeindex=market_data.timestamp,
            entry_prices=position.entry_prices,
            exit_prices=exit_prices,
            strikes=position.strikes,
            quantity=position.quantity,
            pnl=final_pnl,
            exit_reason=exit_reason,
            date=date
        )