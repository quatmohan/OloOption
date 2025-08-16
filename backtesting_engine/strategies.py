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
            print(f"    CE strikes (OTM to ITM): {all_ce_strikes[:5]}...")  # Show first 5
            
            for strike in all_ce_strikes:
                premium = option_chain["CE"][strike]
                if premium >= self.scalping_price:
                    selected["CE"] = strike
                    print(f"    Selected CE strike {strike} with premium {premium:.3f}")
                    break
        
        # For PE options: iterate from OTM to ITM (e.g., 570 up to 580)
        if "PE" in option_chain:
            # Get OTM strikes (below spot) and sort from lowest to highest
            otm_strikes = sorted([s for s in option_chain["PE"].keys() if s <= spot_price])
            
            # Then get ITM strikes (above spot) and sort from lowest to highest
            itm_strikes = sorted([s for s in option_chain["PE"].keys() if s > spot_price])
            
            # Combine: OTM first, then ITM
            all_pe_strikes = otm_strikes + itm_strikes
            print(f"    PE strikes (OTM to ITM): {all_pe_strikes[-5:][::-1]}...")  # Show last 5 reversed
            
            for strike in all_pe_strikes:
                premium = option_chain["PE"][strike]
                if premium >= self.scalping_price:
                    selected["PE"] = strike
                    print(f"    Selected PE strike {strike} with premium {premium:.3f}")
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
                # Apply slippage to entry price
                market_price = market_data.option_prices[option_type][strike]
                # For selling, we receive less (market_price - slippage)
                # For buying, we pay more (market_price + slippage)
                entry_price = market_price - 0.005  # Default to selling straddle
                entry_prices[f"{option_type}_{strike}"] = entry_price
        
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