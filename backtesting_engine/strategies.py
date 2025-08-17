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
        # Initial entry
        if self.entry_count == 0 and current_timeindex == self.entry_timeindex:
            return True
        
        # Re-entry conditions
        if (self.entry_count < self.max_reentries and 
            current_timeindex >= self.last_entry_time + self.reentry_gap and
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
        # Initial entry
        if self.entry_count == 0 and current_timeindex == self.entry_timeindex:
            return True
        
        # Re-entry conditions
        if (self.entry_count < self.max_reentries and 
            current_timeindex >= self.last_entry_time + self.reentry_gap and
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