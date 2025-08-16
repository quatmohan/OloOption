"""
Efficient option chain data structures and utilities
"""

from typing import Dict, List, Optional, Tuple
from .models import MarketData


class OptionChainManager:
    """Manages option chain data with efficient lookups and strike selection"""
    
    def __init__(self):
        self.option_data: Dict[int, Dict[str, Dict[float, float]]] = {}
        self.strike_cache: Dict[float, List[float]] = {}  # spot_price -> nearby_strikes
    
    def load_option_data(self, option_data: Dict[int, Dict[str, Dict[float, float]]]):
        """Load option data and build indexes"""
        self.option_data = option_data
        self._build_strike_cache()
    
    def _build_strike_cache(self):
        """Build cache of strikes for efficient lookup"""
        # Get all unique strikes across all timestamps
        all_strikes = set()
        for timestamp_data in self.option_data.values():
            for option_type_data in timestamp_data.values():
                all_strikes.update(option_type_data.keys())
        
        self.all_strikes = sorted(all_strikes)
    
    def get_strikes_near_spot(self, spot_price: float, num_strikes: int = 15) -> List[float]:
        """Get strikes closest to spot price with caching"""
        cache_key = round(spot_price, 2)  # Round to avoid too many cache entries
        
        if cache_key not in self.strike_cache:
            # Find strikes closest to spot price
            strikes_with_distance = [(strike, abs(strike - spot_price)) for strike in self.all_strikes]
            strikes_with_distance.sort(key=lambda x: x[1])  # Sort by distance
            
            nearby_strikes = [strike for strike, _ in strikes_with_distance[:num_strikes]]
            self.strike_cache[cache_key] = nearby_strikes
        
        return self.strike_cache[cache_key]
    
    def get_option_price(self, timestamp: int, option_type: str, strike: float) -> Optional[float]:
        """Get option price with efficient lookup"""
        if (timestamp in self.option_data and 
            option_type in self.option_data[timestamp] and 
            strike in self.option_data[timestamp][option_type]):
            return self.option_data[timestamp][option_type][strike]
        return None
    
    def get_available_strikes_at_timestamp(self, timestamp: int) -> Dict[str, List[float]]:
        """Get all available strikes at a specific timestamp"""
        if timestamp not in self.option_data:
            return {}
        
        available_strikes = {}
        for option_type, strikes_data in self.option_data[timestamp].items():
            available_strikes[option_type] = list(strikes_data.keys())
        
        return available_strikes
    
    def validate_data_completeness(self, timestamp: int, required_strikes: List[float]) -> Dict[str, List[float]]:
        """Validate that required strikes have data at timestamp"""
        missing_data = {"CE": [], "PE": []}
        
        if timestamp not in self.option_data:
            missing_data["CE"] = required_strikes
            missing_data["PE"] = required_strikes
            return missing_data
        
        for option_type in ["CE", "PE"]:
            if option_type not in self.option_data[timestamp]:
                missing_data[option_type] = required_strikes
            else:
                for strike in required_strikes:
                    if strike not in self.option_data[timestamp][option_type]:
                        missing_data[option_type].append(strike)
        
        return missing_data
    
    def get_market_data(self, timestamp: int, spot_price: float) -> Optional[MarketData]:
        """Create MarketData object for a specific timestamp"""
        if timestamp not in self.option_data:
            return None
        
        # Get all available strikes at this timestamp
        all_strikes = set()
        for option_type_data in self.option_data[timestamp].values():
            all_strikes.update(option_type_data.keys())
        
        return MarketData(
            timestamp=timestamp,
            spot_price=spot_price,
            option_prices=self.option_data[timestamp].copy(),
            available_strikes=sorted(all_strikes)
        )
    
    def get_otm_strikes(self, spot_price: float, option_type: str, timestamp: int) -> List[float]:
        """Get out-of-the-money strikes for a specific option type"""
        if timestamp not in self.option_data or option_type not in self.option_data[timestamp]:
            return []
        
        available_strikes = list(self.option_data[timestamp][option_type].keys())
        
        if option_type == "CE":
            # For calls, OTM strikes are above spot price
            otm_strikes = [strike for strike in available_strikes if strike > spot_price]
        else:  # PE
            # For puts, OTM strikes are below spot price
            otm_strikes = [strike for strike in available_strikes if strike < spot_price]
        
        return sorted(otm_strikes)
    
    def get_itm_strikes(self, spot_price: float, option_type: str, timestamp: int) -> List[float]:
        """Get in-the-money strikes for a specific option type"""
        if timestamp not in self.option_data or option_type not in self.option_data[timestamp]:
            return []
        
        available_strikes = list(self.option_data[timestamp][option_type].keys())
        
        if option_type == "CE":
            # For calls, ITM strikes are below spot price
            itm_strikes = [strike for strike in available_strikes if strike < spot_price]
        else:  # PE
            # For puts, ITM strikes are above spot price
            itm_strikes = [strike for strike in available_strikes if strike > spot_price]
        
        return sorted(itm_strikes)
    
    def get_atm_strike(self, spot_price: float, timestamp: int) -> Optional[float]:
        """Get the at-the-money strike closest to spot price"""
        if timestamp not in self.option_data:
            return None
        
        # Get all available strikes at this timestamp
        all_strikes = set()
        for option_type_data in self.option_data[timestamp].values():
            all_strikes.update(option_type_data.keys())
        
        if not all_strikes:
            return None
        
        # Find strike closest to spot price
        closest_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
        return closest_strike