"""
Concrete trading strategy implementations
"""

from typing import Dict, List
from .models import TradingSetup, Position, MarketData


class StraddleSetup(TradingSetup):
    """Straddle selling strategy implementation"""
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on premium or distance strategy"""
        selected_strikes = {}
        
        if self.strike_selection == "premium":
            selected_strikes = self._select_premium_based_strikes(spot_price, option_chain)
        elif self.strike_selection == "distance":
            selected_strikes = self._select_distance_based_strikes(spot_price, option_chain)
        
        return selected_strikes
    
    def _select_premium_based_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on premium >= scalping_price"""
        selected = {}
        
        # For CE options: iterate from OTM to ITM (e.g., 590 down to 580)
        if "CE" in option_chain:
            # Get OTM strikes (above spot) and sort from highest to lowest
            otm_strikes = sorted([s for s in option_chain["CE"].keys() if s >= spot_price], reverse=True)
            
            # Then get ITM strikes (below spot) and sort from highest to lowest  
            itm_strikes = sorted([s for s in option_chain["CE"].keys() if s < spot_price], reverse=True)
            
            # Combine: OTM first, then ITM
            all_ce_strikes = otm_strikes + itm_strikes
            # print(f"    CE strikes (OTM to ITM): {all_ce_strikes[:5]}...")  # Show first 5
            
            for strike in all_ce_strikes:
                premium = option_chain["CE"][strike]
                if premium >= self.scalping_price:
                    selected["CE"] = strike
                    # print(f"    Selected CE strike {strike} with premium {premium:.3f}")
                    break
        
        # For PE options: iterate from OTM to ITM (e.g., 570 up to 580)
        if "PE" in option_chain:
            # Get OTM strikes (below spot) and sort from lowest to highest
            otm_strikes = sorted([s for s in option_chain["PE"].keys() if s <= spot_price])
            
            # Then get ITM strikes (above spot) and sort from lowest to highest
            itm_strikes = sorted([s for s in option_chain["PE"].keys() if s > spot_price])
            
            # Combine: OTM first, then ITM
            all_pe_strikes = otm_strikes + itm_strikes
            # print(f"    PE strikes (OTM to ITM): {all_pe_strikes[-5:][::-1]}...")  # Show last 5 reversed
            
            for strike in all_pe_strikes:
                premium = option_chain["PE"][strike]
                if premium >= self.scalping_price:
                    selected["PE"] = strike
                    # print(f"    Selected PE strike {strike} with premium {premium:.3f}")
                    break
        
        return selected
    
    def _select_distance_based_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes N positions away from spot"""
        selected = {}
        
        # Get available strikes and find closest to spot
        if "CE" in option_chain:
            ce_strikes = sorted(option_chain["CE"].keys())
            spot_idx = min(range(len(ce_strikes)), key=lambda i: abs(ce_strikes[i] - spot_price))
            target_idx = min(spot_idx + self.strikes_away, len(ce_strikes) - 1)
            selected["CE"] = ce_strikes[target_idx]
        
        if "PE" in option_chain:
            pe_strikes = sorted(option_chain["PE"].keys())
            spot_idx = min(range(len(pe_strikes)), key=lambda i: abs(pe_strikes[i] - spot_price))
            target_idx = max(spot_idx - self.strikes_away, 0)
            selected["PE"] = pe_strikes[target_idx]
        
        return selected
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create straddle positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for selected strikes
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                # Store original market price (slippage applied in P&L calculation)
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",  # Default to selling straddle
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions

class HedgedStraddleSetup(TradingSetup):
    """Hedged straddle strategy - sell straddle + buy hedge options"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, hedge_strikes_away: int = 5):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.hedge_strikes_away = hedge_strikes_away  # How far to place hedge strikes
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes for both straddle and hedge positions"""
        selected_strikes = {}
        
        if self.strike_selection == "premium":
            selected_strikes = self._select_premium_based_strikes(spot_price, option_chain)
        elif self.strike_selection == "distance":
            selected_strikes = self._select_distance_based_strikes(spot_price, option_chain)
        
        # Add hedge strikes
        hedge_strikes = self._select_hedge_strikes(spot_price, option_chain, selected_strikes)
        selected_strikes.update(hedge_strikes)
        
        return selected_strikes
    
    def _select_premium_based_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select main straddle strikes based on premium >= scalping_price"""
        selected = {}
        
        # For CE options: iterate from OTM to ITM
        if "CE" in option_chain:
            otm_strikes = sorted([s for s in option_chain["CE"].keys() if s >= spot_price], reverse=True)
            itm_strikes = sorted([s for s in option_chain["CE"].keys() if s < spot_price], reverse=True)
            all_ce_strikes = otm_strikes + itm_strikes
            
            for strike in all_ce_strikes:
                premium = option_chain["CE"][strike]
                if premium >= self.scalping_price:
                    selected["CE_SELL"] = strike
                    break
        
        # For PE options: iterate from OTM to ITM
        if "PE" in option_chain:
            otm_strikes = sorted([s for s in option_chain["PE"].keys() if s <= spot_price])
            itm_strikes = sorted([s for s in option_chain["PE"].keys() if s > spot_price])
            all_pe_strikes = otm_strikes + itm_strikes
            
            for strike in all_pe_strikes:
                premium = option_chain["PE"][strike]
                if premium >= self.scalping_price:
                    selected["PE_SELL"] = strike
                    break
        
        return selected
    
    def _select_distance_based_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select main straddle strikes N positions away from spot"""
        selected = {}
        
        if "CE" in option_chain:
            ce_strikes = sorted(option_chain["CE"].keys())
            spot_idx = min(range(len(ce_strikes)), key=lambda i: abs(ce_strikes[i] - spot_price))
            target_idx = min(spot_idx + self.strikes_away, len(ce_strikes) - 1)
            selected["CE_SELL"] = ce_strikes[target_idx]
        
        if "PE" in option_chain:
            pe_strikes = sorted(option_chain["PE"].keys())
            spot_idx = min(range(len(pe_strikes)), key=lambda i: abs(pe_strikes[i] - spot_price))
            target_idx = max(spot_idx - self.strikes_away, 0)
            selected["PE_SELL"] = pe_strikes[target_idx]
        
        return selected
    
    def _select_hedge_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]], 
                             main_strikes: Dict[str, float]) -> Dict[str, float]:
        """Select hedge strikes further OTM"""
        hedge_strikes = {}
        
        # CE hedge - further OTM (higher strike)
        if "CE_SELL" in main_strikes and "CE" in option_chain:
            ce_strikes = sorted(option_chain["CE"].keys())
            main_strike = main_strikes["CE_SELL"]
            
            # Find strikes further OTM than main strike
            otm_strikes = [s for s in ce_strikes if s > main_strike]
            if len(otm_strikes) >= self.hedge_strikes_away:
                hedge_strikes["CE_BUY"] = otm_strikes[self.hedge_strikes_away - 1]
            elif otm_strikes:
                hedge_strikes["CE_BUY"] = otm_strikes[-1]  # Use furthest available
        
        # PE hedge - further OTM (lower strike)
        if "PE_SELL" in main_strikes and "PE" in option_chain:
            pe_strikes = sorted(option_chain["PE"].keys(), reverse=True)
            main_strike = main_strikes["PE_SELL"]
            
            # Find strikes further OTM than main strike
            otm_strikes = [s for s in pe_strikes if s < main_strike]
            if len(otm_strikes) >= self.hedge_strikes_away:
                hedge_strikes["PE_BUY"] = otm_strikes[self.hedge_strikes_away - 1]
            elif otm_strikes:
                hedge_strikes["PE_BUY"] = otm_strikes[-1]  # Use furthest available
        
        return hedge_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create hedged straddle positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        position_strikes = {}
        
        # Create positions for selected strikes
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            position_type = strike_key.split('_')[1]  # SELL or BUY
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                
                # Store original market price (slippage applied in P&L calculation)
                entry_prices[f"{option_type}_{strike}_{position_type}"] = market_price
                position_strikes[strike_key] = strike
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=position_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="HEDGED",  # Mixed position type
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions


class CEScalpingSetup(TradingSetup):
    """CE (Call) scalping strategy with re-entry capability"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, max_reentries: int = 3, reentry_gap: int = 300):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.max_reentries = max_reentries  # Maximum number of re-entries
        self.reentry_gap = reentry_gap  # Minimum gap between entries (timeindex)
        self.last_entry_time = 0  # Track last entry time
        self.entry_count = 0  # Track number of entries
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met - initial entry or re-entry"""
        # Initial entry - must be at exact entry timeindex
        if self.entry_count == 0 and current_timeindex == self.entry_timeindex:
            return True
        
        # Re-entry conditions - only after initial entry and after entry timeindex
        if (self.entry_count > 0 and 
            self.entry_count < self.max_reentries and 
            current_timeindex >= max(self.entry_timeindex, self.last_entry_time + self.reentry_gap) and
            current_timeindex <= self.close_timeindex - 100):  # Don't enter too close to close
            return True
        
        return False
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select CE strikes only"""
        selected_strikes = {}
        
        if "CE" not in option_chain:
            return selected_strikes
        
        if self.strike_selection == "premium":
            # For CE options: iterate from OTM to ITM
            otm_strikes = sorted([s for s in option_chain["CE"].keys() if s >= spot_price], reverse=True)
            itm_strikes = sorted([s for s in option_chain["CE"].keys() if s < spot_price], reverse=True)
            all_ce_strikes = otm_strikes + itm_strikes
            
            for strike in all_ce_strikes:
                premium = option_chain["CE"][strike]
                if premium >= self.scalping_price:
                    selected_strikes["CE"] = strike
                    break
        
        elif self.strike_selection == "distance":
            ce_strikes = sorted(option_chain["CE"].keys())
            spot_idx = min(range(len(ce_strikes)), key=lambda i: abs(ce_strikes[i] - spot_price))
            target_idx = min(spot_idx + self.strikes_away, len(ce_strikes) - 1)
            selected_strikes["CE"] = ce_strikes[target_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create CE scalping positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create CE position
        if "CE" in selected_strikes and "CE" in market_data.option_prices:
            strike = selected_strikes["CE"]
            if strike in market_data.option_prices["CE"]:
                market_price = market_data.option_prices["CE"][strike]
                entry_prices[f"CE_{strike}"] = market_price  # Store original price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
            
            # Update tracking
            self.last_entry_time = market_data.timestamp
            self.entry_count += 1
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.last_entry_time = 0
        self.entry_count = 0


class PEScalpingSetup(TradingSetup):
    """PE (Put) scalping strategy with re-entry capability"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, max_reentries: int = 3, reentry_gap: int = 300):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.max_reentries = max_reentries
        self.reentry_gap = reentry_gap
        self.last_entry_time = 0
        self.entry_count = 0
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met - initial entry or re-entry"""
        # Initial entry - must be at exact entry timeindex
        if self.entry_count == 0 and current_timeindex == self.entry_timeindex:
            return True
        
        # Re-entry conditions - only after initial entry and after entry timeindex
        if (self.entry_count > 0 and 
            self.entry_count < self.max_reentries and 
            current_timeindex >= max(self.entry_timeindex, self.last_entry_time + self.reentry_gap) and
            current_timeindex <= self.close_timeindex - 100):
            return True
        
        return False
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select PE strikes only"""
        selected_strikes = {}
        
        if "PE" not in option_chain:
            return selected_strikes
        
        if self.strike_selection == "premium":
            # For PE options: iterate from OTM to ITM
            otm_strikes = sorted([s for s in option_chain["PE"].keys() if s <= spot_price])
            itm_strikes = sorted([s for s in option_chain["PE"].keys() if s > spot_price])
            all_pe_strikes = otm_strikes + itm_strikes
            
            for strike in all_pe_strikes:
                premium = option_chain["PE"][strike]
                if premium >= self.scalping_price:
                    selected_strikes["PE"] = strike
                    break
        
        elif self.strike_selection == "distance":
            pe_strikes = sorted(option_chain["PE"].keys())
            spot_idx = min(range(len(pe_strikes)), key=lambda i: abs(pe_strikes[i] - spot_price))
            target_idx = max(spot_idx - self.strikes_away, 0)
            selected_strikes["PE"] = pe_strikes[target_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create PE scalping positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create PE position
        if "PE" in selected_strikes and "PE" in market_data.option_prices:
            strike = selected_strikes["PE"]
            if strike in market_data.option_prices["PE"]:
                market_price = market_data.option_prices["PE"][strike]
                entry_prices[f"PE_{strike}"] = market_price  # Store original price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
            
            # Update tracking
            self.last_entry_time = market_data.timestamp
            self.entry_count += 1
        
        return positions 
   
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.last_entry_time = 0
        self.entry_count = 0


class IronCondorSetup(TradingSetup):
    """Iron Condor strategy - sell call spread + sell put spread for range-bound markets"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "distance", scalping_price: float = 0.40, 
                 strikes_away: int = 2, wing_width: int = 10, short_strike_distance: int = 5):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.wing_width = wing_width  # Distance between short and long strikes
        self.short_strike_distance = short_strike_distance  # Distance of short strikes from spot
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select four strikes for iron condor: short call, long call, short put, long put"""
        selected_strikes = {}
        
        # Get available strikes
        ce_strikes = sorted(option_chain.get("CE", {}).keys()) if "CE" in option_chain else []
        pe_strikes = sorted(option_chain.get("PE", {}).keys()) if "PE" in option_chain else []
        
        if not ce_strikes or not pe_strikes:
            return selected_strikes
        
        # Find strikes closest to spot
        ce_spot_idx = min(range(len(ce_strikes)), key=lambda i: abs(ce_strikes[i] - spot_price))
        pe_spot_idx = min(range(len(pe_strikes)), key=lambda i: abs(pe_strikes[i] - spot_price))
        
        # Select call spread strikes (above spot) - short closer to spot, long further out
        short_call_idx = min(ce_spot_idx + 1, len(ce_strikes) - 1)  # 1 strike above spot
        long_call_idx = min(short_call_idx + 1, len(ce_strikes) - 1)  # 1 more strike out
        
        # Select put spread strikes (below spot) - short closer to spot, long further out  
        short_put_idx = max(pe_spot_idx - 1, 0)  # 1 strike below spot
        long_put_idx = max(short_put_idx - 1, 0)  # 1 more strike out
        
        # Assign strikes if valid
        if short_call_idx < len(ce_strikes) and long_call_idx < len(ce_strikes) and long_call_idx > short_call_idx:
            selected_strikes["CE_SELL"] = ce_strikes[short_call_idx]
            selected_strikes["CE_BUY"] = ce_strikes[long_call_idx]
        
        if short_put_idx >= 0 and long_put_idx >= 0 and long_put_idx < short_put_idx:
            selected_strikes["PE_SELL"] = pe_strikes[short_put_idx]
            selected_strikes["PE_BUY"] = pe_strikes[long_put_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create four-leg iron condor position"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if len(selected_strikes) != 4:  # Need all four legs
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for all four legs
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            action = strike_key.split('_')[1]  # SELL or BUY
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}_{action}"] = market_price
        
        if len(entry_prices) == 4:  # All legs available
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="IRON_CONDOR",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def calculate_max_profit(self) -> float:
        """Calculate theoretical maximum profit for iron condor"""
        # Max profit = net credit received (premium collected from short strikes - premium paid for long strikes)
        # This would be calculated at position creation with actual market prices
        return self.target_pct
    
    def check_early_closure_conditions(self, current_pnl: float) -> bool:
        """Check if position should be closed early based on percentage of max profit"""
        # Close if we've captured 50% of maximum theoretical profit
        return current_pnl >= (self.target_pct * 0.5)


class ButterflySetup(TradingSetup):
    """Butterfly spread strategy - buy-sell-sell-buy (1-2-1 ratio) for low volatility"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "distance", scalping_price: float = 0.40, 
                 strikes_away: int = 2, wing_distance: int = 5, butterfly_type: str = "CALL"):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.wing_distance = wing_distance  # Distance between body and wings
        self.butterfly_type = butterfly_type  # "CALL" or "PUT"
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select three strikes for butterfly: lower wing, body, upper wing"""
        selected_strikes = {}
        option_type = "CE" if self.butterfly_type == "CALL" else "PE"
        
        if option_type not in option_chain:
            return selected_strikes
        
        strikes = sorted(option_chain[option_type].keys())
        
        # Find strike closest to spot for body
        spot_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
        
        # Select body strike (at or near the money)
        body_idx = spot_idx
        
        # Select wing strikes
        lower_wing_idx = max(body_idx - max(1, self.wing_distance // 5), 0)  # Ensure at least 1 strike difference
        upper_wing_idx = min(body_idx + max(1, self.wing_distance // 5), len(strikes) - 1)  # Ensure at least 1 strike difference
        
        if lower_wing_idx >= 0 and upper_wing_idx < len(strikes):
            selected_strikes[f"{option_type}_BUY_LOWER"] = strikes[lower_wing_idx]
            selected_strikes[f"{option_type}_SELL_BODY"] = strikes[body_idx]
            selected_strikes[f"{option_type}_BUY_UPPER"] = strikes[upper_wing_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create butterfly position with 1-2-1 ratio"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if len(selected_strikes) != 3:  # Need all three legs
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for all three legs
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[strike_key] = market_price
        
        if len(entry_prices) == 3:  # All legs available
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="BUTTERFLY",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def calculate_breakeven_points(self) -> tuple:
        """Calculate upper and lower breakeven points"""
        # This would be calculated with actual strike prices and premiums
        # Lower breakeven = lower strike + net debit
        # Upper breakeven = upper strike - net debit
        return (0.0, 0.0)  # Placeholder


class VerticalSpreadSetup(TradingSetup):
    """Vertical spread strategy - two-leg directional strategies"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "distance", scalping_price: float = 0.40, 
                 strikes_away: int = 2, spread_width: int = 5, direction: str = "BULL_CALL"):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.spread_width = spread_width  # Distance between strikes
        self.direction = direction  # "BULL_CALL", "BEAR_CALL", "BULL_PUT", "BEAR_PUT"
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select two strikes for vertical spread based on direction"""
        selected_strikes = {}
        
        if self.direction in ["BULL_CALL", "BEAR_CALL"]:
            option_type = "CE"
        else:  # BULL_PUT, BEAR_PUT
            option_type = "PE"
        
        if option_type not in option_chain:
            return selected_strikes
        
        strikes = sorted(option_chain[option_type].keys())
        spot_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
        
        if self.direction == "BULL_CALL":
            # Buy lower strike, sell higher strike
            lower_idx = max(spot_idx - 1, 0)
            upper_idx = min(lower_idx + max(1, self.spread_width // 5), len(strikes) - 1)
            selected_strikes[f"{option_type}_BUY"] = strikes[lower_idx]
            selected_strikes[f"{option_type}_SELL"] = strikes[upper_idx]
            
        elif self.direction == "BEAR_CALL":
            # Sell lower strike, buy higher strike
            lower_idx = max(spot_idx - 1, 0)
            upper_idx = min(lower_idx + max(1, self.spread_width // 5), len(strikes) - 1)
            selected_strikes[f"{option_type}_SELL"] = strikes[lower_idx]
            selected_strikes[f"{option_type}_BUY"] = strikes[upper_idx]
            
        elif self.direction == "BULL_PUT":
            # Sell higher strike, buy lower strike
            upper_idx = min(spot_idx + 1, len(strikes) - 1)
            lower_idx = max(upper_idx - max(1, self.spread_width // 5), 0)
            selected_strikes[f"{option_type}_SELL"] = strikes[upper_idx]
            selected_strikes[f"{option_type}_BUY"] = strikes[lower_idx]
            
        elif self.direction == "BEAR_PUT":
            # Buy higher strike, sell lower strike
            upper_idx = min(spot_idx + 1, len(strikes) - 1)
            lower_idx = max(upper_idx - max(1, self.spread_width // 5), 0)
            selected_strikes[f"{option_type}_BUY"] = strikes[upper_idx]
            selected_strikes[f"{option_type}_SELL"] = strikes[lower_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create vertical spread position"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if len(selected_strikes) != 2:  # Need both legs
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for both legs
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            action = strike_key.split('_')[1]  # BUY or SELL
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}_{action}"] = market_price
        
        if len(entry_prices) == 2:  # Both legs available
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="VERTICAL_SPREAD",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions


class RatioSpreadSetup(TradingSetup):
    """Ratio spread strategy - unbalanced spreads with configurable ratios"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "distance", scalping_price: float = 0.40, 
                 strikes_away: int = 2, ratio: str = "1:2", spread_type: str = "CALL"):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.ratio = ratio  # "1:2", "1:3", "2:3", etc.
        self.spread_type = spread_type  # "CALL" or "PUT"
        self.long_qty, self.short_qty = self._parse_ratio(ratio)
    
    def _parse_ratio(self, ratio: str) -> tuple:
        """Parse ratio string into long and short quantities"""
        parts = ratio.split(':')
        return int(parts[0]), int(parts[1])
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes for ratio spread"""
        selected_strikes = {}
        option_type = "CE" if self.spread_type == "CALL" else "PE"
        
        if option_type not in option_chain:
            return selected_strikes
        
        strikes = sorted(option_chain[option_type].keys())
        spot_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
        
        if self.spread_type == "CALL":
            # Call ratio spread: buy lower strike, sell multiple higher strikes
            long_idx = max(spot_idx - 1, 0)
            short_idx = min(long_idx + 2, len(strikes) - 1)  # 2 strikes higher
        else:
            # Put ratio spread: buy higher strike, sell multiple lower strikes
            long_idx = min(spot_idx + 1, len(strikes) - 1)
            short_idx = max(long_idx - 2, 0)  # 2 strikes lower
        
        selected_strikes[f"{option_type}_BUY"] = strikes[long_idx]
        selected_strikes[f"{option_type}_SELL"] = strikes[short_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create ratio spread position with unbalanced quantities"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if len(selected_strikes) != 2:  # Need both legs
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for both legs with different quantities
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            action = strike_key.split('_')[1]  # BUY or SELL
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                
                # Apply ratio quantities
                if action == "BUY":
                    entry_prices[f"{option_type}_{strike}_{action}_{self.long_qty}"] = market_price
                else:  # SELL
                    entry_prices[f"{option_type}_{strike}_{action}_{self.short_qty}"] = market_price
        
        if len(entry_prices) == 2:  # Both legs available
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,  # Base quantity, actual quantities encoded in entry_prices keys
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="RATIO_SPREAD",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def calculate_breakeven_points(self) -> List[float]:
        """Calculate breakeven points for ratio spread"""
        # This would be calculated with actual strike prices and premiums
        # Multiple breakeven points possible with ratio spreads
        return [0.0, 0.0]  # Placeholder
    
    def check_unlimited_risk_protection(self) -> bool:
        """Check if unlimited risk protection should be triggered"""
        # Implement logic to protect against unlimited risk on the short side
        # This would typically involve monitoring the underlying price movement
        return False


class MomentumReversalSetup(TradingSetup):
    """Pattern recognition strategy based on price velocity and mean reversion"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, momentum_threshold: float = 0.02, 
                 reversion_lookback: int = 12, strategy_type: str = "MOMENTUM"):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.momentum_threshold = momentum_threshold  # Minimum price velocity for signal
        self.reversion_lookback = reversion_lookback  # Number of 5-second intervals to analyze
        self.strategy_type = strategy_type  # "MOMENTUM" or "REVERSION"
        self.price_history = []  # Track recent price movements
        self.velocity_history = []  # Track price velocity
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on momentum/reversion signals"""
        # Only check after initial entry time and if we have enough price history
        if current_timeindex < self.entry_timeindex or len(self.price_history) < self.reversion_lookback:
            return False
        
        if self.strategy_type == "MOMENTUM":
            return self.detect_momentum_signal()
        else:  # REVERSION
            return self.detect_reversion_signal()
    
    def update_price_data(self, market_data: MarketData):
        """Update price history and calculate velocity"""
        self.price_history.append(market_data.spot_price)
        
        # Keep only recent history
        if len(self.price_history) > self.reversion_lookback + 5:
            self.price_history = self.price_history[-self.reversion_lookback:]
        
        # Calculate price velocity if we have enough data
        if len(self.price_history) >= 2:
            velocity = self.calculate_price_velocity(self.price_history[-5:] if len(self.price_history) >= 5 else self.price_history)
            self.velocity_history.append(velocity)
            
            # Keep velocity history manageable
            if len(self.velocity_history) > self.reversion_lookback:
                self.velocity_history = self.velocity_history[-self.reversion_lookback:]
    
    def detect_momentum_signal(self) -> bool:
        """Detect momentum-based entry signal"""
        if len(self.velocity_history) < 3:
            return False
        
        # Check for sustained momentum in one direction
        recent_velocity = self.velocity_history[-3:]
        avg_velocity = sum(recent_velocity) / len(recent_velocity)
        
        # Signal if average velocity exceeds threshold and is consistent
        if abs(avg_velocity) >= self.momentum_threshold:
            # Check for consistency (all velocities in same direction)
            if all(v > 0 for v in recent_velocity) or all(v < 0 for v in recent_velocity):
                return True
        
        return False
    
    def detect_reversion_signal(self) -> bool:
        """Detect mean reversion entry signal"""
        if len(self.price_history) < self.reversion_lookback:
            return False
        
        # Calculate recent price movement vs longer-term average
        recent_prices = self.price_history[-3:]  # Last 3 intervals (15 seconds)
        longer_term_prices = self.price_history[-self.reversion_lookback:]
        
        recent_avg = sum(recent_prices) / len(recent_prices)
        longer_avg = sum(longer_term_prices) / len(longer_term_prices)
        
        # Signal if recent price has moved significantly away from longer-term average
        price_deviation = abs(recent_avg - longer_avg) / longer_avg
        
        # Also check if velocity is slowing (indicating potential reversal)
        if len(self.velocity_history) >= 3:
            velocity_trend = self.velocity_history[-1] - self.velocity_history[-3]
            velocity_slowing = abs(velocity_trend) < abs(self.velocity_history[-3]) * 0.5
            
            return price_deviation >= self.momentum_threshold and velocity_slowing
        
        return price_deviation >= self.momentum_threshold
    
    def calculate_price_velocity(self, price_history: List[float]) -> float:
        """Calculate price velocity from recent price changes"""
        if len(price_history) < 2:
            return 0.0
        
        # Calculate percentage change per interval
        total_change = 0.0
        for i in range(1, len(price_history)):
            change = (price_history[i] - price_history[i-1]) / price_history[i-1]
            total_change += change
        
        # Average change per interval
        return total_change / (len(price_history) - 1)
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on momentum/reversion direction"""
        selected_strikes = {}
        
        # Determine direction bias from recent velocity
        direction_bias = 0
        if len(self.velocity_history) >= 2:
            recent_velocity = sum(self.velocity_history[-2:]) / 2
            direction_bias = 1 if recent_velocity > 0 else -1
        
        if self.strategy_type == "MOMENTUM":
            # For momentum, trade in direction of movement
            if direction_bias > 0:  # Upward momentum - favor calls
                if "CE" in option_chain:
                    selected_strikes.update(self._select_option_strikes("CE", spot_price, option_chain))
            elif direction_bias < 0:  # Downward momentum - favor puts
                if "PE" in option_chain:
                    selected_strikes.update(self._select_option_strikes("PE", spot_price, option_chain))
        else:  # REVERSION
            # For reversion, trade against recent movement
            if direction_bias > 0:  # Recent upward movement - expect reversion down, favor puts
                if "PE" in option_chain:
                    selected_strikes.update(self._select_option_strikes("PE", spot_price, option_chain))
            elif direction_bias < 0:  # Recent downward movement - expect reversion up, favor calls
                if "CE" in option_chain:
                    selected_strikes.update(self._select_option_strikes("CE", spot_price, option_chain))
        
        return selected_strikes
    
    def _select_option_strikes(self, option_type: str, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes for specific option type"""
        selected = {}
        
        if self.strike_selection == "premium":
            if option_type == "CE":
                # For CE: iterate from OTM to ITM
                otm_strikes = sorted([s for s in option_chain[option_type].keys() if s >= spot_price], reverse=True)
                itm_strikes = sorted([s for s in option_chain[option_type].keys() if s < spot_price], reverse=True)
                all_strikes = otm_strikes + itm_strikes
            else:  # PE
                # For PE: iterate from OTM to ITM
                otm_strikes = sorted([s for s in option_chain[option_type].keys() if s <= spot_price])
                itm_strikes = sorted([s for s in option_chain[option_type].keys() if s > spot_price])
                all_strikes = otm_strikes + itm_strikes
            
            for strike in all_strikes:
                premium = option_chain[option_type][strike]
                if premium >= self.scalping_price:
                    selected[option_type] = strike
                    break
        
        elif self.strike_selection == "distance":
            strikes = sorted(option_chain[option_type].keys())
            spot_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
            
            if option_type == "CE":
                target_idx = min(spot_idx + self.strikes_away, len(strikes) - 1)
            else:  # PE
                target_idx = max(spot_idx - self.strikes_away, 0)
            
            selected[option_type] = strikes[target_idx]
        
        return selected
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create momentum/reversion positions"""
        # Update price data first
        self.update_price_data(market_data)
        
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for selected strikes
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",  # Default to selling options
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.price_history = []
        self.velocity_history = []


class VolatilitySkewSetup(TradingSetup):
    """Strategy to exploit relative implied volatility differences across strikes"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, skew_threshold: float = 0.05, 
                 iv_lookback: int = 20):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.skew_threshold = skew_threshold  # Minimum IV difference for signal
        self.iv_lookback = iv_lookback  # Number of intervals to track IV
        self.iv_history = {}  # Track IV estimates by strike
        self.price_history = {}  # Track option prices by strike for IV estimation
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on volatility skew"""
        if current_timeindex < self.entry_timeindex:
            return False
        
        # Need sufficient data to detect skew
        if len(self.iv_history) < 2:
            return False
        
        return self.detect_skew_opportunity()
    
    def update_iv_data(self, market_data: MarketData):
        """Update implied volatility estimates from option price changes"""
        timestamp = market_data.timestamp
        
        # Track option prices for IV estimation
        for option_type in ["CE", "PE"]:
            if option_type not in market_data.option_prices:
                continue
            
            for strike, price in market_data.option_prices[option_type].items():
                key = f"{option_type}_{strike}"
                
                if key not in self.price_history:
                    self.price_history[key] = []
                
                self.price_history[key].append((timestamp, price))
                
                # Keep only recent history
                if len(self.price_history[key]) > self.iv_lookback:
                    self.price_history[key] = self.price_history[key][-self.iv_lookback:]
                
                # Estimate IV from price volatility if we have enough data
                if len(self.price_history[key]) >= 5:
                    iv_estimate = self._estimate_iv_from_prices(self.price_history[key])
                    
                    if key not in self.iv_history:
                        self.iv_history[key] = []
                    
                    self.iv_history[key].append(iv_estimate)
                    
                    # Keep IV history manageable
                    if len(self.iv_history[key]) > self.iv_lookback:
                        self.iv_history[key] = self.iv_history[key][-self.iv_lookback:]
    
    def _estimate_iv_from_prices(self, price_data: List[tuple]) -> float:
        """Estimate implied volatility from option price changes"""
        if len(price_data) < 2:
            return 0.0
        
        # Calculate price volatility as proxy for IV
        prices = [p[1] for p in price_data]
        price_changes = []
        
        for i in range(1, len(prices)):
            if prices[i-1] > 0:  # Avoid division by zero
                change = (prices[i] - prices[i-1]) / prices[i-1]
                price_changes.append(change)
        
        if not price_changes:
            return 0.0
        
        # Calculate standard deviation of price changes as IV proxy
        mean_change = sum(price_changes) / len(price_changes)
        variance = sum((change - mean_change) ** 2 for change in price_changes) / len(price_changes)
        
        return variance ** 0.5  # Standard deviation
    
    def detect_skew_opportunity(self) -> bool:
        """Detect volatility skew trading opportunity"""
        if len(self.iv_history) < 2:
            return False
        
        # Get current IV estimates for different strikes
        current_ivs = {}
        for key, iv_list in self.iv_history.items():
            if iv_list:
                current_ivs[key] = iv_list[-1]
        
        if len(current_ivs) < 2:
            return False
        
        # Look for significant IV differences between strikes
        iv_values = list(current_ivs.values())
        max_iv = max(iv_values)
        min_iv = min(iv_values)
        
        # Signal if IV skew exceeds threshold
        skew_magnitude = (max_iv - min_iv) / max(max_iv, 0.001)  # Avoid division by zero
        
        return skew_magnitude >= self.skew_threshold
    
    def estimate_relative_iv(self, option_prices: Dict[float, float]) -> Dict[float, float]:
        """Estimate relative IV across strikes"""
        relative_ivs = {}
        
        for strike in option_prices.keys():
            # Use recent IV history if available
            for key, iv_list in self.iv_history.items():
                if f"_{strike}" in key and iv_list:
                    relative_ivs[strike] = iv_list[-1]
                    break
        
        return relative_ivs
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on volatility skew - buy low IV, sell high IV"""
        selected_strikes = {}
        
        # Find strikes with highest and lowest relative IV
        high_iv_strike = None
        low_iv_strike = None
        high_iv_value = 0
        low_iv_value = float('inf')
        high_iv_type = None
        low_iv_type = None
        
        for option_type in ["CE", "PE"]:
            if option_type not in option_chain:
                continue
            
            relative_ivs = self.estimate_relative_iv(option_chain[option_type])
            
            for strike, iv in relative_ivs.items():
                if iv > high_iv_value:
                    high_iv_value = iv
                    high_iv_strike = strike
                    high_iv_type = option_type
                
                if iv < low_iv_value:
                    low_iv_value = iv
                    low_iv_strike = strike
                    low_iv_type = option_type
        
        # Create skew position: sell high IV, buy low IV
        if high_iv_strike and low_iv_strike and high_iv_type and low_iv_type:
            selected_strikes[f"{high_iv_type}_SELL"] = high_iv_strike
            selected_strikes[f"{low_iv_type}_BUY"] = low_iv_strike
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create volatility skew positions"""
        # Update IV data first
        self.update_iv_data(market_data)
        
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for selected strikes
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            action = strike_key.split('_')[1]  # SELL or BUY
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}_{action}"] = market_price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="VOLATILITY_SKEW",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.iv_history = {}
        self.price_history = {}


class TimeDecaySetup(TradingSetup):
    """Strategy optimized for accelerating theta decay in final trading hours"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, theta_acceleration_time: int = 4500,
                 high_theta_threshold: float = 0.60):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.theta_acceleration_time = theta_acceleration_time  # Time when theta accelerates
        self.high_theta_threshold = high_theta_threshold  # Minimum premium for high theta options
        self.theta_history = {}  # Track theta estimates
        self.last_prices = {}  # Track previous prices for theta calculation
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met - focus on final trading hours"""
        # Only enter during theta acceleration period
        if current_timeindex < max(self.entry_timeindex, self.theta_acceleration_time):
            return False
        
        # Don't enter too close to market close
        if current_timeindex >= self.close_timeindex - 50:
            return False
        
        return True
    
    def update_theta_estimates(self, market_data: MarketData):
        """Update theta estimates from price decay over time"""
        timestamp = market_data.timestamp
        
        for option_type in ["CE", "PE"]:
            if option_type not in market_data.option_prices:
                continue
            
            for strike, current_price in market_data.option_prices[option_type].items():
                key = f"{option_type}_{strike}"
                
                # Calculate theta if we have previous price
                if key in self.last_prices:
                    prev_timestamp, prev_price = self.last_prices[key]
                    time_diff = timestamp - prev_timestamp
                    
                    if time_diff > 0 and prev_price > 0:
                        # Theta approximation: price change per time unit
                        theta_estimate = (current_price - prev_price) / time_diff
                        
                        if key not in self.theta_history:
                            self.theta_history[key] = []
                        
                        self.theta_history[key].append(theta_estimate)
                        
                        # Keep only recent theta estimates
                        if len(self.theta_history[key]) > 10:
                            self.theta_history[key] = self.theta_history[key][-10:]
                
                # Update last price
                self.last_prices[key] = (timestamp, current_price)
    
    def calculate_theta_acceleration(self, current_timeindex: int) -> float:
        """Calculate theta acceleration factor based on time to expiration"""
        # Time remaining until market close
        time_remaining = self.close_timeindex - current_timeindex
        total_time = self.close_timeindex - self.theta_acceleration_time
        
        if total_time <= 0:
            return 1.0
        
        # Theta accelerates exponentially as expiration approaches
        time_factor = time_remaining / total_time
        acceleration_factor = 1.0 / max(time_factor, 0.1)  # Avoid division by zero
        
        return min(acceleration_factor, 5.0)  # Cap acceleration
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select high-theta options for time decay strategy"""
        selected_strikes = {}
        
        # Focus on options with high time value (high theta)
        best_theta_options = []
        
        for option_type in ["CE", "PE"]:
            if option_type not in option_chain:
                continue
            
            for strike, price in option_chain[option_type].items():
                # Prefer options with higher premiums (more time value to decay)
                if price >= self.high_theta_threshold:
                    # Calculate distance from spot to assess time value
                    if option_type == "CE":
                        time_value_factor = max(0, price - max(0, spot_price - strike))
                    else:  # PE
                        time_value_factor = max(0, price - max(0, strike - spot_price))
                    
                    best_theta_options.append((option_type, strike, price, time_value_factor))
        
        # Sort by time value factor and select best options
        best_theta_options.sort(key=lambda x: x[3], reverse=True)
        
        # Select top options for both calls and puts if available
        ce_selected = False
        pe_selected = False
        
        for option_type, strike, price, time_value in best_theta_options:
            if option_type == "CE" and not ce_selected:
                selected_strikes["CE"] = strike
                ce_selected = True
            elif option_type == "PE" and not pe_selected:
                selected_strikes["PE"] = strike
                pe_selected = True
            
            # Stop if we have both types
            if ce_selected and pe_selected:
                break
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create time decay positions optimized for theta capture"""
        # Update theta estimates
        self.update_theta_estimates(market_data)
        
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Calculate theta acceleration factor
        acceleration_factor = self.calculate_theta_acceleration(market_data.timestamp)
        
        # Adjust target based on theta acceleration
        adjusted_target = self.target_pct * acceleration_factor
        
        # Create positions for selected strikes
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=adjusted_target,  # Use accelerated target
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",  # Sell options to capture theta
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.theta_history = {}
        self.last_prices = {}


def detect_put_call_parity_violation(market_data: MarketData, risk_free_rate: float = 0.05) -> List[Dict]:
    """
    Detect put-call parity violations for arbitrage opportunities
    Put-Call Parity: C - P = S - K * e^(-r*T)
    Where: C = call price, P = put price, S = spot price, K = strike, r = risk-free rate, T = time to expiration
    """
    violations = []
    
    if "CE" not in market_data.option_prices or "PE" not in market_data.option_prices:
        return violations
    
    # Get common strikes between calls and puts
    ce_strikes = set(market_data.option_prices["CE"].keys())
    pe_strikes = set(market_data.option_prices["PE"].keys())
    common_strikes = ce_strikes.intersection(pe_strikes)
    
    # Estimate time to expiration (assuming same-day expiration)
    # Use remaining time in trading day as proxy
    time_to_expiration = max(0.01, (4650 - market_data.timestamp) / 4650.0 / 365.0)  # Convert to years
    
    for strike in common_strikes:
        call_price = market_data.option_prices["CE"][strike]
        put_price = market_data.option_prices["PE"][strike]
        spot_price = market_data.spot_price
        
        # Calculate theoretical put-call parity relationship
        discount_factor = (strike * (risk_free_rate * time_to_expiration))  # Simplified for short-term
        theoretical_difference = spot_price - strike + discount_factor
        actual_difference = call_price - put_price
        
        # Check for significant deviation (potential arbitrage)
        parity_violation = abs(actual_difference - theoretical_difference)
        violation_threshold = 0.10  # $0.10 threshold for arbitrage opportunity
        
        if parity_violation > violation_threshold:
            arbitrage_type = "BUY_CALL_SELL_PUT" if actual_difference < theoretical_difference else "SELL_CALL_BUY_PUT"
            
            violations.append({
                "strike": strike,
                "call_price": call_price,
                "put_price": put_price,
                "spot_price": spot_price,
                "theoretical_difference": theoretical_difference,
                "actual_difference": actual_difference,
                "violation_amount": parity_violation,
                "arbitrage_type": arbitrage_type,
                "timestamp": market_data.timestamp
            })
    
    return violations


class MomentumReversalSetup(TradingSetup):
    """Pattern recognition strategy based on price velocity and momentum detection"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, strategy_type: str = "MOMENTUM", 
                 momentum_threshold: float = 0.02, reversion_lookback: int = 12):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.strategy_type = strategy_type  # "MOMENTUM" or "REVERSION"
        self.momentum_threshold = momentum_threshold  # Minimum velocity for signal
        self.reversion_lookback = reversion_lookback  # Periods to look back for reversion
        self.price_history = []  # Store recent price movements
        self.velocity_history = []  # Store calculated velocities
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on momentum/reversion signals"""
        if current_timeindex < self.entry_timeindex:
            return False
        
        if len(self.price_history) < self.reversion_lookback:
            return False  # Need sufficient history
        
        if self.strategy_type == "MOMENTUM":
            return self.detect_momentum_signal()
        elif self.strategy_type == "REVERSION":
            return self.detect_reversion_signal()
        
        return False
    
    def detect_momentum_signal(self) -> bool:
        """Detect momentum continuation signal"""
        if len(self.velocity_history) < 3:
            return False
        
        # Check if recent velocity exceeds threshold and is accelerating
        recent_velocity = self.velocity_history[-1]
        prev_velocity = self.velocity_history[-2]
        
        return (abs(recent_velocity) > self.momentum_threshold and 
                abs(recent_velocity) > abs(prev_velocity))
    
    def detect_reversion_signal(self) -> bool:
        """Detect mean reversion signal"""
        if len(self.velocity_history) < self.reversion_lookback:
            return False
        
        # Check if price has moved significantly and velocity is decelerating
        recent_velocities = self.velocity_history[-3:]
        
        # Look for deceleration after significant movement
        if len(recent_velocities) >= 3:
            is_decelerating = (abs(recent_velocities[-1]) < abs(recent_velocities[-2]) < 
                             abs(recent_velocities[-3]))
            has_moved_significantly = max(abs(v) for v in recent_velocities) > self.momentum_threshold
            
            return is_decelerating and has_moved_significantly
        
        return False
    
    def calculate_price_velocity(self, price_history: List[float]) -> float:
        """Calculate price velocity from recent price changes"""
        if len(price_history) < 2:
            return 0.0
        
        # Calculate velocity as rate of change over recent periods
        recent_change = price_history[-1] - price_history[-2]
        return recent_change / price_history[-2] if price_history[-2] != 0 else 0.0
    
    def update_price_data(self, market_data: MarketData):
        """Update price history for momentum/reversion analysis"""
        self.price_history.append(market_data.spot_price)
        
        # Keep only recent history
        if len(self.price_history) > self.reversion_lookback * 2:
            self.price_history = self.price_history[-self.reversion_lookback:]
        
        # Calculate and store velocity
        velocity = self.calculate_price_velocity(self.price_history)
        self.velocity_history.append(velocity)
        
        # Keep velocity history manageable
        if len(self.velocity_history) > self.reversion_lookback:
            self.velocity_history = self.velocity_history[-self.reversion_lookback:]
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on momentum direction"""
        selected_strikes = {}
        
        if not self.velocity_history:
            return selected_strikes
        
        recent_velocity = self.velocity_history[-1]
        
        # For momentum strategy, trade in direction of movement
        # For reversion strategy, trade against recent movement
        if self.strategy_type == "MOMENTUM":
            # Positive velocity -> expect continued upward movement -> sell puts
            # Negative velocity -> expect continued downward movement -> sell calls
            if recent_velocity > 0 and "PE" in option_chain:
                selected_strikes.update(self._select_premium_based_strikes_pe(spot_price, option_chain))
            elif recent_velocity < 0 and "CE" in option_chain:
                selected_strikes.update(self._select_premium_based_strikes_ce(spot_price, option_chain))
        
        elif self.strategy_type == "REVERSION":
            # Expect reversal -> sell straddle or strangle
            if "CE" in option_chain and "PE" in option_chain:
                ce_strikes = self._select_premium_based_strikes_ce(spot_price, option_chain)
                pe_strikes = self._select_premium_based_strikes_pe(spot_price, option_chain)
                selected_strikes.update(ce_strikes)
                selected_strikes.update(pe_strikes)
        
        return selected_strikes
    
    def _select_premium_based_strikes_ce(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select CE strikes based on premium"""
        selected = {}
        
        if "CE" not in option_chain:
            return selected
        
        # Iterate from OTM to ITM for CE
        otm_strikes = sorted([s for s in option_chain["CE"].keys() if s >= spot_price], reverse=True)
        itm_strikes = sorted([s for s in option_chain["CE"].keys() if s < spot_price], reverse=True)
        all_ce_strikes = otm_strikes + itm_strikes
        
        for strike in all_ce_strikes:
            premium = option_chain["CE"][strike]
            if premium >= self.scalping_price:
                selected["CE"] = strike
                break
        
        return selected
    
    def _select_premium_based_strikes_pe(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select PE strikes based on premium"""
        selected = {}
        
        if "PE" not in option_chain:
            return selected
        
        # Iterate from OTM to ITM for PE
        otm_strikes = sorted([s for s in option_chain["PE"].keys() if s <= spot_price])
        itm_strikes = sorted([s for s in option_chain["PE"].keys() if s > spot_price])
        all_pe_strikes = otm_strikes + itm_strikes
        
        for strike in all_pe_strikes:
            premium = option_chain["PE"][strike]
            if premium >= self.scalping_price:
                selected["PE"] = strike
                break
        
        return selected
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create positions based on momentum/reversion signals"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Create positions for selected strikes
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.price_history = []
        self.velocity_history = []


class VolatilitySkewSetup(TradingSetup):
    """Strategy to exploit relative implied volatility differences across strikes"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, skew_threshold: float = 0.05):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.skew_threshold = skew_threshold  # Minimum IV difference for signal
        self.iv_history = {}  # Store IV estimates by strike
        self.price_history = {}  # Store price history by strike for IV calculation
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on volatility skew"""
        if current_timeindex < self.entry_timeindex:
            return False
        
        # Need sufficient IV history to detect skew
        return len(self.iv_history) >= 3
    
    def estimate_relative_iv(self, option_prices: Dict[float, float]) -> Dict[float, float]:
        """Estimate relative implied volatility from option price changes"""
        relative_iv = {}
        
        for strike, price in option_prices.items():
            if strike in self.price_history and len(self.price_history[strike]) >= 2:
                # Simple IV proxy: price volatility over recent periods
                prices = self.price_history[strike]
                if len(prices) >= 3:
                    # Calculate price volatility as proxy for IV
                    price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                                   for i in range(1, len(prices)) if prices[i-1] != 0]
                    if price_changes:
                        relative_iv[strike] = sum(price_changes) / len(price_changes)
        
        return relative_iv
    
    def detect_skew_opportunity(self, market_data: MarketData) -> Dict[str, Dict[str, float]]:
        """Detect volatility skew trading opportunities"""
        opportunities = {"CE": {}, "PE": {}}
        
        for option_type in ["CE", "PE"]:
            if option_type not in market_data.option_prices:
                continue
            
            # Estimate current relative IV
            relative_iv = self.estimate_relative_iv(market_data.option_prices[option_type])
            
            if len(relative_iv) < 3:
                continue
            
            # Find strikes with significantly different IV
            iv_values = list(relative_iv.values())
            avg_iv = sum(iv_values) / len(iv_values)
            
            for strike, iv in relative_iv.items():
                iv_diff = abs(iv - avg_iv)
                if iv_diff > self.skew_threshold:
                    opportunities[option_type][strike] = {
                        "iv_diff": iv_diff,
                        "action": "SELL" if iv > avg_iv else "BUY",  # Sell high IV, buy low IV
                        "relative_iv": iv
                    }
        
        return opportunities
    
    def update_iv_data(self, market_data: MarketData):
        """Update IV history for skew analysis"""
        for option_type in ["CE", "PE"]:
            if option_type not in market_data.option_prices:
                continue
            
            for strike, price in market_data.option_prices[option_type].items():
                strike_key = f"{option_type}_{strike}"
                
                if strike_key not in self.price_history:
                    self.price_history[strike_key] = []
                
                self.price_history[strike_key].append(price)
                
                # Keep only recent history
                if len(self.price_history[strike_key]) > 20:
                    self.price_history[strike_key] = self.price_history[strike_key][-10:]
        
        # Update IV estimates
        for option_type in ["CE", "PE"]:
            if option_type in market_data.option_prices:
                relative_iv = self.estimate_relative_iv(market_data.option_prices[option_type])
                self.iv_history[option_type] = relative_iv
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes based on volatility skew opportunities"""
        selected_strikes = {}
        
        # Create temporary market data for skew detection
        temp_market_data = MarketData(
            timestamp=0,
            symbol="",
            spot_price=spot_price,
            option_prices=option_chain,
            available_strikes=[]
        )
        
        opportunities = self.detect_skew_opportunity(temp_market_data)
        
        # Select best opportunities for each option type
        for option_type in ["CE", "PE"]:
            if opportunities[option_type]:
                # Sort by IV difference (highest first)
                sorted_opps = sorted(opportunities[option_type].items(), 
                                   key=lambda x: x[1]["iv_diff"], reverse=True)
                
                if sorted_opps:
                    best_strike, opp_data = sorted_opps[0]
                    # Use action from skew analysis
                    action = opp_data["action"]
                    selected_strikes[f"{option_type}_{action}"] = best_strike
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create skew-based positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        position_strikes = {}
        
        # Create positions for selected strikes
        for strike_key, strike in selected_strikes.items():
            option_type = strike_key.split('_')[0]  # CE or PE
            action = strike_key.split('_')[1]  # SELL or BUY
            
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}_{action}"] = market_price
                position_strikes[strike_key] = strike
        
        if entry_prices:
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=position_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SKEW",
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.iv_history = {}
        self.price_history = {}


class TimeDecaySetup(TradingSetup):
    """Strategy optimized for accelerating theta decay in final trading hours"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "premium", scalping_price: float = 0.40, 
                 strikes_away: int = 2, theta_acceleration_time: int = 4500, 
                 high_theta_threshold: float = 0.50):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.theta_acceleration_time = theta_acceleration_time  # When theta accelerates
        self.high_theta_threshold = high_theta_threshold  # Minimum premium for theta plays
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met - focus on theta acceleration period"""
        if current_timeindex < self.entry_timeindex:
            return False
        
        # Prefer entries during theta acceleration period
        return current_timeindex >= self.theta_acceleration_time
    
    def calculate_theta_acceleration(self, current_timeindex: int) -> float:
        """Calculate theta acceleration factor based on time to expiration"""
        if current_timeindex < self.theta_acceleration_time:
            return 1.0
        
        # Time remaining until close
        time_remaining = max(self.close_timeindex - current_timeindex, 1)
        total_acceleration_period = self.close_timeindex - self.theta_acceleration_time
        
        if total_acceleration_period <= 0:
            return 2.0  # Maximum acceleration
        
        # Acceleration increases as expiration approaches
        acceleration_factor = 1.0 + (total_acceleration_period - time_remaining) / total_acceleration_period
        return min(acceleration_factor, 3.0)  # Cap at 3x acceleration
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select high-theta strikes (high premium options near the money)"""
        selected_strikes = {}
        
        # Focus on ATM and slightly OTM options with high premiums
        for option_type in ["CE", "PE"]:
            if option_type not in option_chain:
                continue
            
            # Find strikes with premium >= high_theta_threshold
            high_premium_strikes = []
            for strike, premium in option_chain[option_type].items():
                if premium >= self.high_theta_threshold:
                    distance_from_spot = abs(strike - spot_price)
                    high_premium_strikes.append((strike, premium, distance_from_spot))
            
            if high_premium_strikes:
                # Sort by premium (highest first), then by distance from spot (closest first)
                high_premium_strikes.sort(key=lambda x: (-x[1], x[2]))
                selected_strikes[option_type] = high_premium_strikes[0][0]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create time decay optimized positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if not selected_strikes:
            return []
        
        positions = []
        entry_prices = {}
        
        # Calculate theta acceleration for target adjustment
        theta_acceleration = self.calculate_theta_acceleration(market_data.timestamp)
        
        # Create positions for selected strikes
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            # Adjust target based on theta acceleration
            accelerated_target = self.target_pct * theta_acceleration
            
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=accelerated_target,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="SELL",  # Selling for theta decay
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
        
        return positions


class GammaScalpingSetup(TradingSetup):
    """Intraday gamma scalping strategy with delta-neutral position construction and dynamic rebalancing"""
    
    def __init__(self, setup_id: str, target_pct: float, stop_loss_pct: float, 
                 entry_timeindex: int, close_timeindex: int = 4650, 
                 strike_selection: str = "distance", scalping_price: float = 0.40, 
                 strikes_away: int = 2, delta_threshold: float = 0.10, 
                 rebalance_frequency: int = 60, max_rebalances: int = 5):
        super().__init__(setup_id, target_pct, stop_loss_pct, entry_timeindex, 
                        close_timeindex, strike_selection, scalping_price, strikes_away)
        self.delta_threshold = delta_threshold  # Delta threshold for rebalancing (e.g., 0.10)
        self.rebalance_frequency = rebalance_frequency  # Minimum time between rebalances (timeindex)
        self.max_rebalances = max_rebalances  # Maximum rebalances per day
        
        # Tracking variables
        self.last_rebalance_time = 0
        self.rebalance_count = 0
        self.current_delta = 0.0
        self.gamma_pnl = 0.0  # P&L from underlying movement
        self.theta_pnl = 0.0  # P&L from time decay
        self.last_spot_price = 0.0
        self.position_ratios = {"CE": 1, "PE": 1}  # Current position ratios for delta neutrality
    
    def check_entry_condition(self, current_timeindex: int) -> bool:
        """Check if entry conditions are met based on timeindex"""
        return current_timeindex == self.entry_timeindex
    
    def select_strikes(self, spot_price: float, option_chain: Dict[str, Dict[float, float]]) -> Dict[str, float]:
        """Select strikes for delta-neutral position construction"""
        selected_strikes = {}
        
        if "CE" not in option_chain or "PE" not in option_chain:
            return selected_strikes
        
        # For delta-neutral construction, select ATM or near-ATM strikes
        ce_strikes = sorted(option_chain["CE"].keys())
        pe_strikes = sorted(option_chain["PE"].keys())
        
        # Find strikes closest to spot price
        ce_spot_idx = min(range(len(ce_strikes)), key=lambda i: abs(ce_strikes[i] - spot_price))
        pe_spot_idx = min(range(len(pe_strikes)), key=lambda i: abs(pe_strikes[i] - spot_price))
        
        # Select ATM strikes for initial delta-neutral position
        selected_strikes["CE"] = ce_strikes[ce_spot_idx]
        selected_strikes["PE"] = pe_strikes[pe_spot_idx]
        
        return selected_strikes
    
    def create_positions(self, market_data: MarketData) -> List[Position]:
        """Create initial delta-neutral positions"""
        selected_strikes = self.select_strikes(market_data.spot_price, market_data.option_prices)
        
        if len(selected_strikes) != 2:  # Need both CE and PE
            return []
        
        positions = []
        entry_prices = {}
        
        # Create initial delta-neutral position (sell straddle)
        for option_type, strike in selected_strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if len(entry_prices) == 2:  # Both legs available
            position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=selected_strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="GAMMA_SCALP",  # Special position type for gamma scalping
                force_close_timeindex=self.close_timeindex
            )
            positions.append(position)
            
            # Initialize tracking variables
            self.last_spot_price = market_data.spot_price
            self.current_delta = self._estimate_position_delta(market_data, selected_strikes)
        
        return positions
    
    def check_rebalancing_condition(self, current_timeindex: int, market_data: MarketData, 
                                   current_positions: List[Position]) -> bool:
        """Check if position needs rebalancing based on delta threshold"""
        # Don't rebalance too close to market close
        if current_timeindex >= self.close_timeindex - 300:  # 25 minutes before close
            return False
        
        # Check rebalancing frequency and max rebalances
        if (self.rebalance_count >= self.max_rebalances or 
            current_timeindex < self.last_rebalance_time + self.rebalance_frequency):
            return False
        
        # Calculate current delta
        if current_positions:
            position = current_positions[0]  # Assume single gamma scalping position
            current_delta = self._estimate_position_delta(market_data, position.strikes)
            
            # Check if delta exceeds threshold
            if abs(current_delta) > self.delta_threshold:
                return True
        
        return False
    
    def rebalance_position(self, market_data: MarketData, current_position: Position) -> List[Position]:
        """Rebalance position to maintain delta neutrality"""
        rebalanced_positions = []
        
        # Calculate current delta
        current_delta = self._estimate_position_delta(market_data, current_position.strikes)
        
        # Determine rebalancing action
        if current_delta > self.delta_threshold:
            # Position is too long delta - need to sell more calls or buy more puts
            # For simplicity, adjust position ratios
            self.position_ratios["CE"] += 0.2  # Increase call selling
        elif current_delta < -self.delta_threshold:
            # Position is too short delta - need to buy more calls or sell more puts
            self.position_ratios["PE"] += 0.2  # Increase put selling
        
        # Create rebalanced position with adjusted ratios
        entry_prices = {}
        for option_type, strike in current_position.strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                market_price = market_data.option_prices[option_type][strike]
                entry_prices[f"{option_type}_{strike}"] = market_price
        
        if entry_prices:
            rebalanced_position = Position(
                setup_id=self.setup_id,
                entry_timeindex=market_data.timestamp,
                entry_prices=entry_prices,
                strikes=current_position.strikes,
                quantity=1,
                target_pnl=self.target_pct,
                stop_loss_pnl=-abs(self.stop_loss_pct),
                position_type="GAMMA_SCALP_REBALANCED",
                force_close_timeindex=self.close_timeindex
            )
            rebalanced_positions.append(rebalanced_position)
            
            # Update tracking
            self.last_rebalance_time = market_data.timestamp
            self.rebalance_count += 1
            self.current_delta = self._estimate_position_delta(market_data, current_position.strikes)
        
        return rebalanced_positions
    
    def calculate_gamma_theta_pnl(self, market_data: MarketData, position: Position) -> Dict[str, float]:
        """Calculate separate gamma P&L and theta P&L"""
        gamma_pnl = 0.0
        theta_pnl = 0.0
        
        if self.last_spot_price > 0:
            # Estimate gamma P&L from underlying movement
            spot_move = market_data.spot_price - self.last_spot_price
            
            # Simplified gamma P&L calculation
            # Gamma P&L ≈ 0.5 * gamma * (spot_move)^2 * position_size
            estimated_gamma = 0.05  # Simplified gamma estimate
            gamma_pnl = 0.5 * estimated_gamma * (spot_move ** 2) * position.quantity * position.lot_size
            
            # Estimate theta P&L (time decay)
            # For short positions, theta decay is positive
            time_passed_hours = 1.0 / 78.0  # Approximate 5-second interval as fraction of trading day
            estimated_theta = -0.02  # Simplified theta estimate (negative for long options)
            theta_pnl = -estimated_theta * time_passed_hours * position.quantity * position.lot_size
        
        # Update tracking
        self.gamma_pnl += gamma_pnl
        self.theta_pnl += theta_pnl
        self.last_spot_price = market_data.spot_price
        
        return {
            "gamma_pnl": gamma_pnl,
            "theta_pnl": theta_pnl,
            "total_gamma_pnl": self.gamma_pnl,
            "total_theta_pnl": self.theta_pnl
        }
    
    def _estimate_position_delta(self, market_data: MarketData, strikes: Dict[str, float]) -> float:
        """Estimate position delta for rebalancing decisions"""
        total_delta = 0.0
        
        for option_type, strike in strikes.items():
            if option_type in market_data.option_prices and strike in market_data.option_prices[option_type]:
                # Simplified delta estimation
                if option_type == "CE":
                    # Call delta approximation: 0.5 for ATM, higher for ITM, lower for OTM
                    if strike <= market_data.spot_price:
                        delta = 0.6  # ITM call
                    else:
                        delta = 0.4  # OTM call
                    total_delta += delta * self.position_ratios.get("CE", 1)
                
                elif option_type == "PE":
                    # Put delta approximation: -0.5 for ATM, more negative for ITM, less negative for OTM
                    if strike >= market_data.spot_price:
                        delta = -0.6  # ITM put
                    else:
                        delta = -0.4  # OTM put
                    total_delta += delta * self.position_ratios.get("PE", 1)
        
        return total_delta
    
    def should_prioritize_closure(self, current_timeindex: int) -> bool:
        """Check if position closure should be prioritized over delta neutrality"""
        # Prioritize closure in final 30 minutes of trading
        return current_timeindex >= self.close_timeindex - 360  # 30 minutes before close
    
    def reset_daily_state(self):
        """Reset daily state for new trading day"""
        self.last_rebalance_time = 0
        self.rebalance_count = 0
        self.current_delta = 0.0
        self.gamma_pnl = 0.0
        self.theta_pnl = 0.0
        self.last_spot_price = 0.0
        self.position_ratios = {"CE": 1, "PE": 1}


def detect_put_call_parity_violation(market_data: MarketData, risk_free_rate: float = 0.05) -> List[Dict]:
    """
    Detect put-call parity violations for arbitrage opportunities
    Put-Call Parity: C - P = S - K * e^(-r*T)
    Where: C = Call price, P = Put price, S = Spot price, K = Strike, r = risk-free rate, T = time to expiration
    """
    violations = []
    
    if "CE" not in market_data.option_prices or "PE" not in market_data.option_prices:
        return violations
    
    # Get common strikes between calls and puts
    ce_strikes = set(market_data.option_prices["CE"].keys())
    pe_strikes = set(market_data.option_prices["PE"].keys())
    common_strikes = ce_strikes.intersection(pe_strikes)
    
    # Assume very short time to expiration for intraday (approximate T as 0)
    # This simplifies parity to: C - P ≈ S - K
    
    for strike in common_strikes:
        call_price = market_data.option_prices["CE"][strike]
        put_price = market_data.option_prices["PE"][strike]
        
        # Calculate theoretical difference
        theoretical_diff = market_data.spot_price - strike
        actual_diff = call_price - put_price
        
        # Calculate violation amount
        violation_amount = abs(actual_diff - theoretical_diff)
        
        # Consider significant violations (> $0.10)
        if violation_amount > 0.10:
            # Determine arbitrage type
            if actual_diff > theoretical_diff:
                # Calls overpriced relative to puts
                arbitrage_type = "SELL_CALL_BUY_PUT"
            else:
                # Puts overpriced relative to calls
                arbitrage_type = "BUY_CALL_SELL_PUT"
            
            violations.append({
                "strike": strike,
                "call_price": call_price,
                "put_price": put_price,
                "spot_price": market_data.spot_price,
                "theoretical_diff": theoretical_diff,
                "actual_diff": actual_diff,
                "violation_amount": violation_amount,
                "arbitrage_type": arbitrage_type
            })
    
    # Sort by violation amount (largest first)
    violations.sort(key=lambda x: x["violation_amount"], reverse=True)
    
    return violations