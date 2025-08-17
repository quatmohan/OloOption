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
        """Calculate current P&L for a position with slippage applied"""
        total_pnl = 0.0
        
        for option_key, entry_price in position.entry_prices.items():
            # Parse option key using enhanced parsing for complex multi-leg positions
            leg_details = self._parse_option_key(option_key, position)
            
            if not leg_details:
                continue
                
            option_type = leg_details['option_type']
            strike = leg_details['strike']
            leg_type = leg_details['action']
            leg_quantity = leg_details['quantity']
            
            # Get current market price
            current_price = 0.0
            if (option_type in market_data.option_prices and 
                strike in market_data.option_prices[option_type]):
                current_price = market_data.option_prices[option_type][strike]
            else:
                # Handle missing price gracefully - use last known price or skip
                continue
            
            # Calculate P&L for this leg with slippage
            option_pnl = self._calculate_leg_pnl(
                entry_price, current_price, leg_type, leg_quantity, position.lot_size, position.slippage
            )
            
            total_pnl += option_pnl
        
        return total_pnl
    
    def _parse_option_key(self, option_key: str, position: Position) -> Dict:
        """Enhanced parsing for complex multi-leg option keys"""
        parts = option_key.split('_')
        option_type = parts[0]  # CE or PE
        
        # Default values
        leg_details = {
            'option_type': option_type,
            'strike': 0.0,
            'action': position.position_type,  # Default
            'quantity': position.quantity  # Default
        }
        
        try:
            if position.position_type in ["IRON_CONDOR", "VERTICAL_SPREAD", "VOLATILITY_SKEW"]:
                # Format: "CE_580.0_SELL" or "PE_575.0_BUY"
                if len(parts) >= 3:
                    leg_details['strike'] = float(parts[1])
                    leg_details['action'] = parts[2]  # SELL or BUY
                    
            elif position.position_type == "BUTTERFLY":
                # Format: "CE_BUY_LOWER", "CE_SELL_BODY", "CE_BUY_UPPER"
                if "LOWER" in option_key:
                    leg_details['strike'] = position.strikes.get(f"{option_type}_BUY_LOWER", 0.0)
                    leg_details['action'] = "BUY"
                    leg_details['quantity'] = 1
                elif "BODY" in option_key:
                    leg_details['strike'] = position.strikes.get(f"{option_type}_SELL_BODY", 0.0)
                    leg_details['action'] = "SELL"
                    leg_details['quantity'] = 2  # Butterfly sells 2 of the body
                elif "UPPER" in option_key:
                    leg_details['strike'] = position.strikes.get(f"{option_type}_BUY_UPPER", 0.0)
                    leg_details['action'] = "BUY"
                    leg_details['quantity'] = 1
                    
            elif position.position_type == "RATIO_SPREAD":
                # Format: "CE_580.0_SELL_2" or "CE_575.0_BUY_1"
                if len(parts) >= 3:
                    leg_details['strike'] = float(parts[1])
                    leg_details['action'] = parts[2]  # SELL or BUY
                    if len(parts) > 3:
                        leg_details['quantity'] = int(parts[3])  # Quantity from key
                        
            elif position.position_type in ["HEDGED", "GAMMA_SCALP", "GAMMA_SCALP_REBALANCED"]:
                # Format: "CE_580.0_SELL" or "PE_575.0_BUY"
                if len(parts) >= 3:
                    leg_details['strike'] = float(parts[1])
                    leg_details['action'] = parts[2]  # SELL or BUY
                else:
                    # Simple format: "CE_580.0"
                    leg_details['strike'] = float(parts[1])
                    leg_details['action'] = position.position_type
                    
            else:  # Simple position format: "CE_580.0" or "PE_575.0"
                if len(parts) >= 2:
                    leg_details['strike'] = float(parts[1])
                    leg_details['action'] = position.position_type
                    
        except (ValueError, IndexError, KeyError) as e:
            # Return None for invalid keys
            return None
            
        return leg_details
    
    def _calculate_leg_pnl(self, entry_price: float, current_price: float, 
                          action: str, quantity: int, lot_size: int, slippage: float) -> float:
        """Calculate P&L for a single option leg with slippage"""
        if action in ["SELL", "SHORT"]:
            # When selling: receive less on entry, pay more on exit
            effective_entry = entry_price - slippage
            effective_exit = current_price + slippage
            return (effective_entry - effective_exit) * quantity * lot_size
        else:  # BUY, LONG, or other buy actions
            # When buying: pay more on entry, receive less on exit
            effective_entry = entry_price + slippage
            effective_exit = current_price - slippage
            return (effective_exit - effective_entry) * quantity * lot_size
    
    def _check_exit_conditions(self, position: Position, current_timeindex: int) -> Optional[str]:
        """Check if position should be closed with enhanced multi-leg support"""
        # Check target
        if position.target_pnl > 0 and position.current_pnl >= position.target_pnl:
            return "TARGET"
        
        # Check stop loss
        if position.stop_loss_pnl < 0 and position.current_pnl <= position.stop_loss_pnl:
            return "STOP_LOSS"
        
        # Enhanced stop loss for unlimited risk positions
        if position.unlimited_risk and position.current_pnl <= position.stop_loss_pnl * 0.5:
            return "UNLIMITED_RISK_PROTECTION"
        
        # Check position-specific early closure conditions
        if position.position_type == "IRON_CONDOR":
            # Close iron condor if we've captured 50% of maximum profit
            if position.max_profit > 0 and position.current_pnl >= position.max_profit * 0.5:
                return "EARLY_PROFIT_TARGET"
                
        elif position.position_type == "BUTTERFLY":
            # Close butterfly if we've captured 60% of maximum profit or if underlying moves too far
            if position.max_profit > 0 and position.current_pnl >= position.max_profit * 0.6:
                return "EARLY_PROFIT_TARGET"
                
        elif position.position_type == "RATIO_SPREAD":
            # Enhanced protection for ratio spreads
            if position.current_pnl <= position.stop_loss_pnl * 0.75:  # Tighter stop loss
                return "RATIO_SPREAD_PROTECTION"
        
        # Check time-based close
        if current_timeindex >= position.force_close_timeindex:
            return "TIME_BASED"
        
        return None
    
    def _close_position(self, position: Position, market_data: MarketData, exit_reason: str, date: str = "") -> Trade:
        """Close a position and create trade record with enhanced multi-leg support"""
        exit_prices = {}
        
        # Get exit prices for all legs
        for option_key, entry_price in position.entry_prices.items():
            leg_details = self._parse_option_key(option_key, position)
            
            if not leg_details:
                # Handle invalid keys gracefully
                exit_prices[option_key] = 0.0
                continue
                
            option_type = leg_details['option_type']
            strike = leg_details['strike']
            
            # Get current market price
            market_price = 0.0
            if (option_type in market_data.option_prices and 
                strike in market_data.option_prices[option_type]):
                market_price = market_data.option_prices[option_type][strike]
            
            # Store original market price (slippage applied in P&L calculation)
            exit_prices[option_key] = market_price
        
        # Calculate final P&L using enhanced leg calculation
        final_pnl = 0.0
        for option_key, entry_price in position.entry_prices.items():
            exit_price = exit_prices.get(option_key, 0.0)
            leg_details = self._parse_option_key(option_key, position)
            
            if not leg_details:
                continue
                
            # Calculate P&L for this leg
            option_pnl = self._calculate_leg_pnl(
                entry_price, exit_price, leg_details['action'], 
                leg_details['quantity'], position.lot_size, position.slippage
            )
            
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
            date=date,
            gamma_pnl=position.gamma_pnl,
            theta_pnl=position.theta_pnl,
            final_delta=position.current_delta,
            rebalance_count=position.rebalance_count
        )
    
    def update_gamma_scalping_positions(self, market_data: MarketData, setups: List[TradingSetup], date: str = "") -> List[Trade]:
        """Update gamma scalping positions with rebalancing logic"""
        closed_trades = []
        positions_to_remove = []
        new_positions = []
        
        for position_id, position in self.positions.items():
            if position.position_type in ["GAMMA_SCALP", "GAMMA_SCALP_REBALANCED"]:
                # Find the corresponding setup
                gamma_setup = None
                for setup in setups:
                    if setup.setup_id == position.setup_id and hasattr(setup, 'calculate_gamma_theta_pnl'):
                        gamma_setup = setup
                        break
                
                if gamma_setup:
                    # Update gamma and theta P&L
                    pnl_breakdown = gamma_setup.calculate_gamma_theta_pnl(market_data, position)
                    position.gamma_pnl = pnl_breakdown["total_gamma_pnl"]
                    position.theta_pnl = pnl_breakdown["total_theta_pnl"]
                    
                    # Update position delta
                    position.current_delta = gamma_setup._estimate_position_delta(market_data, position.strikes)
                    
                    # Check if rebalancing is needed
                    if gamma_setup.check_rebalancing_condition(market_data.timestamp, market_data, [position]):
                        # Close current position
                        trade = self._close_position(position, market_data, "REBALANCE", date)
                        closed_trades.append(trade)
                        positions_to_remove.append(position_id)
                        
                        # Create rebalanced position
                        rebalanced_positions = gamma_setup.rebalance_position(market_data, position)
                        for rebalanced_pos in rebalanced_positions:
                            rebalanced_pos.rebalance_count = position.rebalance_count + 1
                            new_positions.append(rebalanced_pos)
                    
                    # Check if position closure should be prioritized
                    elif gamma_setup.should_prioritize_closure(market_data.timestamp):
                        # Close position for end-of-day
                        trade = self._close_position(position, market_data, "PRIORITY_CLOSE", date)
                        closed_trades.append(trade)
                        positions_to_remove.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_remove:
            del self.positions[position_id]
        
        # Add new rebalanced positions
        for new_position in new_positions:
            self.add_position(new_position)
        
        return closed_trades
    
    def get_gamma_scalping_metrics(self) -> Dict[str, float]:
        """Get aggregated gamma scalping metrics across all positions"""
        total_gamma_pnl = 0.0
        total_theta_pnl = 0.0
        total_delta = 0.0
        total_rebalances = 0
        gamma_positions = 0
        
        for position in self.positions.values():
            if position.position_type in ["GAMMA_SCALP", "GAMMA_SCALP_REBALANCED"]:
                total_gamma_pnl += position.gamma_pnl
                total_theta_pnl += position.theta_pnl
                total_delta += position.current_delta
                total_rebalances += position.rebalance_count
                gamma_positions += 1
        
        return {
            "total_gamma_pnl": total_gamma_pnl,
            "total_theta_pnl": total_theta_pnl,
            "total_delta": total_delta,
            "avg_delta": total_delta / max(gamma_positions, 1),
            "total_rebalances": total_rebalances,
            "gamma_positions": gamma_positions
        }
    
    def close_multi_leg_position_coordinated(self, position_id: str, market_data: MarketData, 
                                           reason: str = "COORDINATED_CLOSE", date: str = "") -> Optional[Trade]:
        """Close a multi-leg position with coordinated execution"""
        if position_id not in self.positions:
            return None
            
        position = self.positions[position_id]
        
        # For complex multi-leg positions, ensure all legs can be closed
        if position.position_type in ["IRON_CONDOR", "BUTTERFLY", "RATIO_SPREAD", "VERTICAL_SPREAD"]:
            # Check if all legs have available market prices
            missing_legs = []
            for option_key in position.entry_prices.keys():
                leg_details = self._parse_option_key(option_key, position)
                if not leg_details:
                    missing_legs.append(option_key)
                    continue
                    
                option_type = leg_details['option_type']
                strike = leg_details['strike']
                
                if (option_type not in market_data.option_prices or 
                    strike not in market_data.option_prices[option_type]):
                    missing_legs.append(option_key)
            
            if missing_legs:
                # Log warning about partial closure
                print(f"Warning: Cannot close all legs of position {position_id}. Missing prices for: {missing_legs}")
                # Could implement partial closure logic here if needed
        
        # Close the position
        trade = self._close_position(position, market_data, reason, date)
        del self.positions[position_id]
        
        return trade
    
    def check_unlimited_risk_positions(self, market_data: MarketData, 
                                     risk_threshold: float = 500.0) -> List[str]:
        """Check for unlimited risk positions that need protection"""
        at_risk_positions = []
        
        for position_id, position in self.positions.items():
            if position.position_type == "RATIO_SPREAD":
                # Check if ratio spread is approaching unlimited risk zone
                current_pnl = self._calculate_position_pnl(position, market_data)
                
                # For ratio spreads, unlimited risk typically occurs when underlying moves significantly
                # beyond the short strikes
                if abs(current_pnl) > risk_threshold:
                    at_risk_positions.append(position_id)
                    
            elif position.position_type in ["IRON_CONDOR", "BUTTERFLY"]:
                # These have limited risk but check for early closure conditions
                current_pnl = self._calculate_position_pnl(position, market_data)
                
                # Close if approaching maximum loss
                max_loss_threshold = abs(position.stop_loss_pnl) * 0.8  # 80% of max loss
                if current_pnl <= -max_loss_threshold:
                    at_risk_positions.append(position_id)
        
        return at_risk_positions
    
    def get_position_risk_metrics(self, position_id: str, market_data: MarketData) -> Dict[str, float]:
        """Get detailed risk metrics for a specific position"""
        if position_id not in self.positions:
            return {}
            
        position = self.positions[position_id]
        current_pnl = self._calculate_position_pnl(position, market_data)
        
        metrics = {
            "current_pnl": current_pnl,
            "target_pnl": position.target_pnl,
            "stop_loss_pnl": position.stop_loss_pnl,
            "pnl_to_target_ratio": current_pnl / max(abs(position.target_pnl), 1),
            "pnl_to_stop_ratio": current_pnl / max(abs(position.stop_loss_pnl), 1),
            "leg_count": len(position.entry_prices),
            "position_type": position.position_type
        }
        
        # Add position-specific metrics
        if position.position_type == "IRON_CONDOR":
            metrics.update(self._calculate_iron_condor_metrics(position, market_data))
        elif position.position_type == "BUTTERFLY":
            metrics.update(self._calculate_butterfly_metrics(position, market_data))
        elif position.position_type == "RATIO_SPREAD":
            metrics.update(self._calculate_ratio_spread_metrics(position, market_data))
            
        return metrics
    
    def _calculate_iron_condor_metrics(self, position: Position, market_data: MarketData) -> Dict[str, float]:
        """Calculate Iron Condor specific risk metrics"""
        metrics = {}
        
        # Calculate distance to breakeven points
        # Iron condor has two breakeven points
        call_strikes = []
        put_strikes = []
        
        for strike_key, strike in position.strikes.items():
            if "CE" in strike_key:
                call_strikes.append(strike)
            elif "PE" in strike_key:
                put_strikes.append(strike)
        
        if len(call_strikes) >= 2 and len(put_strikes) >= 2:
            # Approximate breakeven calculation
            call_strikes.sort()
            put_strikes.sort(reverse=True)
            
            # Lower breakeven ≈ short put strike - net credit
            # Upper breakeven ≈ short call strike + net credit
            # For simplicity, use strike positions
            lower_breakeven = put_strikes[0]  # Short put strike
            upper_breakeven = call_strikes[0]  # Short call strike
            
            spot_price = market_data.spot_price
            metrics["distance_to_lower_breakeven"] = spot_price - lower_breakeven
            metrics["distance_to_upper_breakeven"] = upper_breakeven - spot_price
            metrics["in_profit_zone"] = lower_breakeven < spot_price < upper_breakeven
        
        return metrics
    
    def _calculate_butterfly_metrics(self, position: Position, market_data: MarketData) -> Dict[str, float]:
        """Calculate Butterfly specific risk metrics"""
        metrics = {}
        
        # Find body strike (the sold strike)
        body_strike = None
        for strike_key, strike in position.strikes.items():
            if "BODY" in strike_key:
                body_strike = strike
                break
        
        if body_strike:
            spot_price = market_data.spot_price
            metrics["distance_to_body"] = abs(spot_price - body_strike)
            metrics["at_max_profit_zone"] = abs(spot_price - body_strike) < 2.5  # Within $2.50 of body
        
        return metrics
    
    def _calculate_ratio_spread_metrics(self, position: Position, market_data: MarketData) -> Dict[str, float]:
        """Calculate Ratio Spread specific risk metrics"""
        metrics = {}
        
        # Identify short and long strikes
        short_strikes = []
        long_strikes = []
        
        for option_key in position.entry_prices.keys():
            leg_details = self._parse_option_key(option_key, position)
            if leg_details:
                if leg_details['action'] == "SELL":
                    short_strikes.append(leg_details['strike'])
                elif leg_details['action'] == "BUY":
                    long_strikes.append(leg_details['strike'])
        
        if short_strikes and long_strikes:
            spot_price = market_data.spot_price
            
            # Calculate distance to unlimited risk zone
            # For call ratio spreads: risk increases as spot moves above short strikes
            # For put ratio spreads: risk increases as spot moves below short strikes
            max_short_strike = max(short_strikes)
            min_short_strike = min(short_strikes)
            
            metrics["distance_to_max_short"] = abs(spot_price - max_short_strike)
            metrics["distance_to_min_short"] = abs(spot_price - min_short_strike)
            metrics["approaching_unlimited_risk"] = (
                spot_price > max_short_strike + 10 or spot_price < min_short_strike - 10
            )
        
        return metrics
    
    def get_multi_leg_position_summary(self) -> Dict[str, int]:
        """Get summary of multi-leg positions by type"""
        summary = {
            "IRON_CONDOR": 0,
            "BUTTERFLY": 0,
            "VERTICAL_SPREAD": 0,
            "RATIO_SPREAD": 0,
            "HEDGED": 0,
            "VOLATILITY_SKEW": 0,
            "SIMPLE": 0,
            "GAMMA_SCALP": 0
        }
        
        for position in self.positions.values():
            position_type = position.position_type
            if position_type in summary:
                summary[position_type] += 1
            else:
                summary["SIMPLE"] += 1
        
        return summary
    
    def emergency_close_unlimited_risk_positions(self, market_data: MarketData, 
                                                risk_threshold: float = 1000.0, 
                                                date: str = "") -> List[Trade]:
        """Emergency closure of positions approaching unlimited risk"""
        emergency_trades = []
        positions_to_remove = []
        
        for position_id, position in self.positions.items():
            if position.unlimited_risk:
                current_pnl = self._calculate_position_pnl(position, market_data)
                
                # Emergency close if loss exceeds threshold
                if current_pnl <= -risk_threshold:
                    trade = self._close_position(position, market_data, "EMERGENCY_UNLIMITED_RISK", date)
                    emergency_trades.append(trade)
                    positions_to_remove.append(position_id)
                    
                    print(f"EMERGENCY: Closed unlimited risk position {position_id} with P&L: {current_pnl:.2f}")
        
        # Remove closed positions
        for position_id in positions_to_remove:
            del self.positions[position_id]
        
        return emergency_trades
    
    def validate_multi_leg_position_integrity(self, position_id: str, market_data: MarketData) -> Dict[str, any]:
        """Validate that all legs of a multi-leg position are properly priced and accessible"""
        if position_id not in self.positions:
            return {"valid": False, "error": "Position not found"}
            
        position = self.positions[position_id]
        validation_result = {
            "valid": True,
            "missing_legs": [],
            "invalid_legs": [],
            "total_legs": len(position.entry_prices),
            "accessible_legs": 0
        }
        
        for option_key in position.entry_prices.keys():
            leg_details = self._parse_option_key(option_key, position)
            
            if not leg_details:
                validation_result["invalid_legs"].append(option_key)
                validation_result["valid"] = False
                continue
                
            option_type = leg_details['option_type']
            strike = leg_details['strike']
            
            # Check if market data is available for this leg
            if (option_type not in market_data.option_prices or 
                strike not in market_data.option_prices[option_type]):
                validation_result["missing_legs"].append(option_key)
                validation_result["valid"] = False
            else:
                validation_result["accessible_legs"] += 1
        
        # For positions requiring coordination, all legs must be accessible
        if position.requires_coordination and validation_result["missing_legs"]:
            validation_result["valid"] = False
            validation_result["coordination_error"] = "Cannot close coordinated position with missing legs"
        
        return validation_result
    
    def get_position_leg_details(self, position_id: str) -> List[Dict]:
        """Get detailed information about each leg of a position"""
        if position_id not in self.positions:
            return []
            
        position = self.positions[position_id]
        leg_details = []
        
        for option_key, entry_price in position.entry_prices.items():
            leg_info = self._parse_option_key(option_key, position)
            
            if leg_info:
                leg_info.update({
                    "option_key": option_key,
                    "entry_price": entry_price,
                    "position_id": position_id,
                    "setup_id": position.setup_id
                })
                leg_details.append(leg_info)
        
        return leg_details