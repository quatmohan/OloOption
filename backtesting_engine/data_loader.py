"""
DataLoader for parsing 5SecData files
"""

import os
import csv
from typing import Dict, List, Optional
from .models import TradingDayData


class DataLoader:
    """Unified data loading and parsing for option chains and spot prices"""
    
    def __init__(self, data_path: str = "5SecData"):
        self.data_path = data_path
    
    def get_available_dates(self, symbol: str) -> List[str]:
        """Get list of available trading dates for a symbol"""
        symbol_path = os.path.join(self.data_path, symbol.upper())
        if not os.path.exists(symbol_path):
            return []
        
        dates = []
        for file in os.listdir(symbol_path):
            if file.endswith("_BK.csv"):
                date = file.replace("_BK.csv", "")
                dates.append(date)
        
        return sorted(dates)
    
    def load_trading_day(self, symbol: str, date: str) -> Optional[TradingDayData]:
        """Load all data for a specific trading day"""
        symbol_path = os.path.join(self.data_path, symbol.upper())
        
        # Load option data
        option_file = os.path.join(symbol_path, f"{date}_BK.csv")
        if not os.path.exists(option_file):
            print(f"Option data file not found: {option_file}")
            return None
        
        option_data = self._parse_option_data(option_file)
        
        # Load spot data
        spot_file = os.path.join(symbol_path, "Spot", f"{symbol.lower()}.csv")
        spot_data = self._parse_spot_data(spot_file, date)
        
        # Load metadata
        prop_file = os.path.join(symbol_path, f"{date}.prop")
        metadata = self._parse_prop_file(prop_file)
        
        return TradingDayData(
            date=date,
            spot_data=spot_data,
            option_data=option_data,
            job_end_idx=metadata.get("jobEndIdx", 4660),
            metadata=metadata
        )
    
    def _parse_option_data(self, file_path: str) -> Dict[int, Dict[str, Dict[float, float]]]:
        """Parse option data CSV file"""
        option_data = {}
        
        try:
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) >= 4:
                        timestamp = int(row[0])
                        option_type = row[1]  # CE or PE
                        strike = float(row[2])
                        price = float(row[3])
                        
                        if timestamp not in option_data:
                            option_data[timestamp] = {}
                        if option_type not in option_data[timestamp]:
                            option_data[timestamp][option_type] = {}
                        
                        option_data[timestamp][option_type][strike] = price
        
        except Exception as e:
            print(f"Error parsing option data {file_path}: {e}")
        
        return option_data
    
    def _parse_spot_data(self, file_path: str, target_date: str) -> Dict[int, float]:
        """Parse spot price data CSV file for specific date"""
        spot_data = {}
        
        try:
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) >= 6 and row[0] == target_date:
                        timestamp = int(row[1])
                        close_price = float(row[5])  # Using close price
                        spot_data[timestamp] = close_price
        
        except Exception as e:
            print(f"Error parsing spot data {file_path}: {e}")
        
        return spot_data
    
    def _parse_prop_file(self, file_path: str) -> Dict:
        """Parse .prop file for metadata"""
        metadata = {}
        
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Try to convert to int if possible
                            try:
                                metadata[key] = int(value)
                            except ValueError:
                                metadata[key] = value
        
        except Exception as e:
            print(f"Error parsing prop file {file_path}: {e}")
        
        return metadata
    
    def get_strikes_near_spot(self, spot_price: float, option_chain: Dict[str, Dict[float, float]], 
                             num_strikes: int = 15) -> List[float]:
        """Get strikes closest to spot price"""
        all_strikes = set()
        
        for option_type in option_chain:
            all_strikes.update(option_chain[option_type].keys())
        
        if not all_strikes:
            return []
        
        # Sort strikes by distance from spot price
        sorted_strikes = sorted(all_strikes, key=lambda x: abs(x - spot_price))
        
        return sorted_strikes[:num_strikes]
    
    def get_option_price(self, option_data: Dict[int, Dict[str, Dict[float, float]]], 
                        timestamp: int, option_type: str, strike: float) -> Optional[float]:
        """Get option price for specific timestamp, type, and strike"""
        if (timestamp in option_data and 
            option_type in option_data[timestamp] and 
            strike in option_data[timestamp][option_type]):
            return option_data[timestamp][option_type][strike]
        
        return None