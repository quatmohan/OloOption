"""
DataLoader for parsing 5SecData files with multi-symbol support
"""

import os
import csv
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from .models import TradingDayData, MultiSymbolTradingData


class DataLoader:
    """Multi-symbol data loading and parsing for option chains, spot prices, and trading session metadata"""
    
    def __init__(self, data_path: str = "5SecData"):
        self.data_path = data_path
        self.supported_symbols = ["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"]
        self.file_suffixes = {
            "QQQ": "",
            "QQQ 1DTE": "F", 
            "SPY": "B",
            "SPY 1DTE": "M"
        }
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.supported_symbols.copy()
    
    def get_available_dates(self, symbol: str) -> List[str]:
        """Get list of available trading dates for a symbol"""
        if symbol not in self.supported_symbols:
            print(f"Unsupported symbol: {symbol}")
            return []
            
        symbol_path = os.path.join(self.data_path, symbol)
        if not os.path.exists(symbol_path):
            return []
        
        dates = []
        suffix = self._get_file_suffix(symbol)
        
        for file in os.listdir(symbol_path):
            if file.endswith("_BK.csv"):
                # Remove suffix and _BK.csv to get base date
                date_part = file.replace("_BK.csv", "")
                if suffix and date_part.endswith(suffix):
                    date = date_part[:-len(suffix)]
                else:
                    date = date_part
                dates.append(date)
        
        return sorted(dates)
    
    def _get_file_suffix(self, symbol: str) -> str:
        """Get file suffix for symbol"""
        return self.file_suffixes.get(symbol, "")
    
    def load_trading_day(self, symbol: str, date: str) -> Optional[MultiSymbolTradingData]:
        """Load all data for a specific trading day and symbol"""
        if symbol not in self.supported_symbols:
            print(f"Unsupported symbol: {symbol}")
            return None
            
        symbol_path = os.path.join(self.data_path, symbol)
        suffix = self._get_file_suffix(symbol)
        
        # Build file names with appropriate suffix
        option_file = os.path.join(symbol_path, f"{date}{suffix}_BK.csv")
        prop_file = os.path.join(symbol_path, f"{date}{suffix}.prop")
        
        if not os.path.exists(option_file):
            print(f"Option data file not found: {option_file}")
            return None
        
        option_data = self._parse_option_data(option_file)
        
        # Load spot data - use base symbol name for spot file
        base_symbol = symbol.split()[0].lower()  # "QQQ 1DTE" -> "qqq"
        spot_file = os.path.join(symbol_path, "Spot", f"{base_symbol}.csv")
        spot_data = self._parse_spot_data(spot_file, date)
        
        # Load metadata
        metadata = self._parse_prop_file(prop_file)
        
        return MultiSymbolTradingData(
            date=date,
            symbol=symbol,
            spot_data=spot_data,
            option_data=option_data,
            job_end_idx=metadata.get("jobEndIdx", 4660),
            metadata=metadata
        )
    
    def load_multiple_symbols(self, symbols: List[str], date: str, concurrent: bool = True) -> Dict[str, MultiSymbolTradingData]:
        """Load data for multiple symbols on the same date
        
        Args:
            symbols: List of symbols to load
            date: Trading date to load
            concurrent: If True, use concurrent loading; if False, use sequential loading
        """
        if concurrent:
            return self._load_multiple_symbols_concurrent(symbols, date)
        else:
            return self._load_multiple_symbols_sequential(symbols, date)
    
    def _load_multiple_symbols_sequential(self, symbols: List[str], date: str) -> Dict[str, MultiSymbolTradingData]:
        """Load data for multiple symbols sequentially"""
        results = {}
        
        for symbol in symbols:
            data = self.load_trading_day(symbol, date)
            if data:
                results[symbol] = data
            else:
                print(f"Failed to load data for {symbol} on {date}")
        
        return results
    
    def _load_multiple_symbols_concurrent(self, symbols: List[str], date: str, max_workers: int = 4) -> Dict[str, MultiSymbolTradingData]:
        """Load data for multiple symbols concurrently using ThreadPoolExecutor"""
        results = {}
        
        # Use ThreadPoolExecutor for concurrent loading
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all loading tasks
            future_to_symbol = {
                executor.submit(self.load_trading_day, symbol, date): symbol 
                for symbol in symbols
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        results[symbol] = data
                    else:
                        print(f"Failed to load data for {symbol} on {date}")
                except Exception as e:
                    print(f"Error loading data for {symbol} on {date}: {e}")
        
        return results
    
    def load_symbol_date_range(self, symbol: str, start_date: str, end_date: str, concurrent: bool = True) -> Dict[str, MultiSymbolTradingData]:
        """Load data for a single symbol across multiple dates
        
        Args:
            symbol: Symbol to load
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            concurrent: If True, use concurrent loading
        """
        available_dates = self.get_available_dates(symbol)
        date_range = [date for date in available_dates if start_date <= date <= end_date]
        
        if not date_range:
            print(f"No dates found for {symbol} between {start_date} and {end_date}")
            return {}
        
        if concurrent:
            return self._load_symbol_dates_concurrent(symbol, date_range)
        else:
            return self._load_symbol_dates_sequential(symbol, date_range)
    
    def _load_symbol_dates_sequential(self, symbol: str, dates: List[str]) -> Dict[str, MultiSymbolTradingData]:
        """Load data for a single symbol across multiple dates sequentially"""
        results = {}
        
        for date in dates:
            data = self.load_trading_day(symbol, date)
            if data:
                results[date] = data
            else:
                print(f"Failed to load data for {symbol} on {date}")
        
        return results
    
    def _load_symbol_dates_concurrent(self, symbol: str, dates: List[str], max_workers: int = 4) -> Dict[str, MultiSymbolTradingData]:
        """Load data for a single symbol across multiple dates concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_date = {
                executor.submit(self.load_trading_day, symbol, date): date 
                for date in dates
            }
            
            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    data = future.result()
                    if data:
                        results[date] = data
                    else:
                        print(f"Failed to load data for {symbol} on {date}")
                except Exception as e:
                    print(f"Error loading data for {symbol} on {date}: {e}")
        
        return results
    
    def load_all_symbols_date_range(self, symbols: List[str], start_date: str, end_date: str, 
                                   concurrent: bool = True) -> Dict[str, Dict[str, MultiSymbolTradingData]]:
        """Load data for multiple symbols across multiple dates
        
        Returns:
            Dict[symbol, Dict[date, MultiSymbolTradingData]]
        """
        results = {}
        
        if concurrent:
            # Load all symbol-date combinations concurrently
            all_tasks = []
            for symbol in symbols:
                available_dates = self.get_available_dates(symbol)
                date_range = [date for date in available_dates if start_date <= date <= end_date]
                for date in date_range:
                    all_tasks.append((symbol, date))
            
            symbol_date_results = {}
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_task = {
                    executor.submit(self.load_trading_day, symbol, date): (symbol, date)
                    for symbol, date in all_tasks
                }
                
                for future in as_completed(future_to_task):
                    symbol, date = future_to_task[future]
                    try:
                        data = future.result()
                        if data:
                            symbol_date_results[(symbol, date)] = data
                        else:
                            print(f"Failed to load data for {symbol} on {date}")
                    except Exception as e:
                        print(f"Error loading data for {symbol} on {date}: {e}")
            
            # Organize results by symbol then date
            for (symbol, date), data in symbol_date_results.items():
                if symbol not in results:
                    results[symbol] = {}
                results[symbol][date] = data
        else:
            # Load sequentially
            for symbol in symbols:
                symbol_data = self.load_symbol_date_range(symbol, start_date, end_date, concurrent=False)
                if symbol_data:
                    results[symbol] = symbol_data
        
        return results
    
    def get_common_dates(self, symbols: List[str]) -> List[str]:
        """Get dates that are available for all specified symbols"""
        if not symbols:
            return []
        
        # Get dates for first symbol
        common_dates = set(self.get_available_dates(symbols[0]))
        
        # Intersect with dates from other symbols
        for symbol in symbols[1:]:
            symbol_dates = set(self.get_available_dates(symbol))
            common_dates = common_dates.intersection(symbol_dates)
        
        return sorted(list(common_dates))
    
    def validate_symbol_data_availability(self, symbols: List[str], dates: List[str]) -> Dict[str, Dict[str, bool]]:
        """Check data availability for symbols and dates without loading
        
        Returns:
            Dict[symbol, Dict[date, is_available]]
        """
        availability = {}
        
        for symbol in symbols:
            if symbol not in self.supported_symbols:
                availability[symbol] = {date: False for date in dates}
                continue
                
            symbol_path = os.path.join(self.data_path, symbol)
            suffix = self._get_file_suffix(symbol)
            availability[symbol] = {}
            
            for date in dates:
                option_file = os.path.join(symbol_path, f"{date}{suffix}_BK.csv")
                prop_file = os.path.join(symbol_path, f"{date}{suffix}.prop")
                base_symbol = symbol.split()[0].lower()
                spot_file = os.path.join(symbol_path, "Spot", f"{base_symbol}.csv")
                
                availability[symbol][date] = (
                    os.path.exists(option_file) and 
                    os.path.exists(prop_file) and 
                    os.path.exists(spot_file)
                )
        
        return availability
    
    # Keep backward compatibility
    def load_trading_day_legacy(self, symbol: str, date: str) -> Optional[TradingDayData]:
        """Legacy method for backward compatibility"""
        multi_data = self.load_trading_day(symbol, date)
        if multi_data:
            return TradingDayData(
                date=multi_data.date,
                spot_data=multi_data.spot_data,
                option_data=multi_data.option_data,
                job_end_idx=multi_data.job_end_idx,
                metadata=multi_data.metadata
            )
        return None
    
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
    
    def get_symbol_statistics(self, symbol: str) -> Dict[str, any]:
        """Get statistics about available data for a symbol"""
        if symbol not in self.supported_symbols:
            return {"error": f"Unsupported symbol: {symbol}"}
        
        dates = self.get_available_dates(symbol)
        if not dates:
            return {"symbol": symbol, "available_dates": 0, "date_range": None}
        
        return {
            "symbol": symbol,
            "file_suffix": self._get_file_suffix(symbol),
            "available_dates": len(dates),
            "date_range": {"start": dates[0], "end": dates[-1]},
            "dates": dates
        }
    
    def get_all_symbols_statistics(self) -> Dict[str, Dict[str, any]]:
        """Get statistics for all supported symbols"""
        return {symbol: self.get_symbol_statistics(symbol) for symbol in self.supported_symbols}
    
    def verify_data_integrity(self, symbol: str, date: str) -> Dict[str, any]:
        """Verify data integrity for a specific symbol and date"""
        result = {
            "symbol": symbol,
            "date": date,
            "valid": True,
            "issues": []
        }
        
        if symbol not in self.supported_symbols:
            result["valid"] = False
            result["issues"].append(f"Unsupported symbol: {symbol}")
            return result
        
        # Check file existence
        symbol_path = os.path.join(self.data_path, symbol)
        suffix = self._get_file_suffix(symbol)
        
        option_file = os.path.join(symbol_path, f"{date}{suffix}_BK.csv")
        prop_file = os.path.join(symbol_path, f"{date}{suffix}.prop")
        base_symbol = symbol.split()[0].lower()
        spot_file = os.path.join(symbol_path, "Spot", f"{base_symbol}.csv")
        
        if not os.path.exists(option_file):
            result["valid"] = False
            result["issues"].append(f"Missing option file: {option_file}")
        
        if not os.path.exists(prop_file):
            result["valid"] = False
            result["issues"].append(f"Missing prop file: {prop_file}")
        
        if not os.path.exists(spot_file):
            result["valid"] = False
            result["issues"].append(f"Missing spot file: {spot_file}")
        
        if not result["valid"]:
            return result
        
        # Try to load and check data consistency
        try:
            data = self.load_trading_day(symbol, date)
            if not data:
                result["valid"] = False
                result["issues"].append("Failed to load data")
                return result
            
            # Check data consistency
            if not data.spot_data:
                result["issues"].append("No spot data found")
            
            if not data.option_data:
                result["issues"].append("No option data found")
            
            # Check if timestamps align
            spot_timestamps = set(data.spot_data.keys())
            option_timestamps = set(data.option_data.keys())
            
            if spot_timestamps != option_timestamps:
                result["issues"].append(f"Timestamp mismatch: {len(spot_timestamps)} spot vs {len(option_timestamps)} option timestamps")
            
            # Check for reasonable data ranges
            if data.spot_data:
                spot_prices = list(data.spot_data.values())
                min_spot = min(spot_prices)
                max_spot = max(spot_prices)
                
                if min_spot <= 0:
                    result["issues"].append(f"Invalid spot prices found (min: {min_spot})")
                
                if max_spot / min_spot > 2:  # More than 100% move in a day seems suspicious
                    result["issues"].append(f"Suspicious spot price range: {min_spot} to {max_spot}")
            
            result["data_points"] = {
                "spot_data": len(data.spot_data),
                "option_timestamps": len(data.option_data),
                "job_end_idx": data.job_end_idx
            }
            
            if result["issues"]:
                result["valid"] = False
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error loading data: {str(e)}")
        
        return result