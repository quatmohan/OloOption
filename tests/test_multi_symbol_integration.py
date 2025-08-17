#!/usr/bin/env python3
"""
Integration tests for multi-symbol data loading and processing
"""

import sys
import os
import tempfile
import csv
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting_engine.data_loader import DataLoader
from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup
from backtesting_engine.models import MarketData


class TestMultiSymbolIntegration(unittest.TestCase):
    """Integration tests for multi-symbol functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(self.test_dir)
        
        # Create test data for multiple symbols
        self.symbols = ["QQQ", "SPY", "QQQ 1DTE", "SPY 1DTE"]
        self.test_date = "2025-08-13"
        
        for symbol in self.symbols:
            self._create_test_data_for_symbol(symbol, self.test_date)
    
    def _create_test_data_for_symbol(self, symbol: str, date: str):
        """Create comprehensive test data for a symbol"""
        # Create directories
        symbol_dir = os.path.join(self.test_dir, symbol)
        spot_dir = os.path.join(symbol_dir, "Spot")
        os.makedirs(symbol_dir, exist_ok=True)
        os.makedirs(spot_dir, exist_ok=True)
        
        # Get file suffix
        suffix = self.data_loader._get_file_suffix(symbol)
        
        # Create option data file
        option_file = os.path.join(symbol_dir, f"{date}{suffix}_BK.csv")
        with open(option_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Create realistic option chain data
            base_spot = 580.0 if "QQQ" in symbol else 450.0
            strikes = [base_spot - 10, base_spot - 5, base_spot, base_spot + 5, base_spot + 10]
            
            for timestamp in range(1000, 4700, 5):  # Full trading day
                for strike in strikes:
                    # CE options - higher for ITM, lower for OTM
                    ce_price = max(0.05, (base_spot - strike) + 2.0 + (timestamp - 1000) * 0.0001)
                    writer.writerow([timestamp, "CE", strike, ce_price])
                    
                    # PE options - higher for ITM, lower for OTM  
                    pe_price = max(0.05, (strike - base_spot) + 2.0 + (timestamp - 1000) * 0.0001)
                    writer.writerow([timestamp, "PE", strike, pe_price])
        
        # Create spot data file
        spot_filename = "qqq.csv" if "QQQ" in symbol else "spy.csv"
        spot_file = os.path.join(spot_dir, spot_filename)
        with open(spot_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Open", "High", "Low", "Close"])
            
            base_price = 580.0 if "QQQ" in symbol else 450.0
            for i, timestamp in enumerate(range(1000, 4700, 5)):
                # Simulate intraday price movement
                price_change = (i % 100 - 50) * 0.01  # Small oscillations
                current_price = base_price + price_change
                
                writer.writerow([
                    date, timestamp, current_price, 
                    current_price + 0.25, current_price - 0.25, current_price
                ])
        
        # Create prop file
        prop_file = os.path.join(symbol_dir, f"{date}{suffix}.prop")
        with open(prop_file, 'w') as f:
            f.write("jobEndIdx=4650\n")
            f.write("idxEnd=4700\n")
            f.write(f"dte={'0' if '1DTE' not in symbol else '1'}\n")
    
    def test_all_symbols_loading(self):
        """Test loading data for all supported symbols"""
        for symbol in self.symbols:
            with self.subTest(symbol=symbol):
                trading_data = self.data_loader.load_trading_day(symbol, self.test_date)
                
                self.assertIsNotNone(trading_data, f"Failed to load data for {symbol}")
                self.assertEqual(trading_data.symbol, symbol)
                self.assertEqual(trading_data.date, self.test_date)
                self.assertGreater(len(trading_data.spot_data), 0)
                self.assertGreater(len(trading_data.option_data), 0)
                self.assertEqual(trading_data.job_end_idx, 4650)
    
    def test_concurrent_multi_symbol_loading(self):
        """Test concurrent loading of multiple symbols"""
        multi_data = self.data_loader.load_multiple_symbols(self.symbols, self.test_date)
        
        self.assertEqual(len(multi_data), len(self.symbols))
        
        for symbol in self.symbols:
            self.assertIn(symbol, multi_data)
            self.assertIsNotNone(multi_data[symbol])
            self.assertEqual(multi_data[symbol].symbol, symbol)
    
    def test_symbol_specific_file_naming(self):
        """Test that file naming conventions work correctly"""
        expected_suffixes = {
            "QQQ": "",
            "QQQ 1DTE": "F", 
            "SPY": "B",
            "SPY 1DTE": "M"
        }
        
        for symbol, expected_suffix in expected_suffixes.items():
            actual_suffix = self.data_loader._get_file_suffix(symbol)
            self.assertEqual(actual_suffix, expected_suffix, 
                           f"Wrong suffix for {symbol}: expected '{expected_suffix}', got '{actual_suffix}'")
    
    def test_cross_symbol_data_consistency(self):
        """Test data consistency across symbols"""
        all_data = {}
        
        for symbol in self.symbols:
            trading_data = self.data_loader.load_trading_day(symbol, self.test_date)
            all_data[symbol] = trading_data
        
        # Check that all symbols have data for the same timestamps
        timestamps_sets = [set(data.spot_data.keys()) for data in all_data.values()]
        
        # All should have similar timestamp coverage
        min_timestamps = min(len(ts) for ts in timestamps_sets)
        max_timestamps = max(len(ts) for ts in timestamps_sets)
        
        # Allow some variation but should be mostly consistent
        self.assertLess(max_timestamps - min_timestamps, 100, 
                       "Timestamp coverage varies too much between symbols")
    
    def test_multi_symbol_backtest_integration(self):
        """Test running backtest with multiple symbols"""
        # Create simple straddle setup
        setup = StraddleSetup(
            setup_id="multi_symbol_test",
            target_pct=50.0,
            stop_loss_pct=100.0,
            entry_timeindex=2000,
            scalping_price=0.30
        )
        
        # Test with each symbol individually
        for symbol in self.symbols[:2]:  # Test with QQQ and SPY
            with self.subTest(symbol=symbol):
                engine = BacktestEngine(
                    data_path=self.test_dir,
                    setups=[setup],
                    daily_max_loss=500.0
                )
                
                # Mock the backtest run to avoid full execution
                with patch.object(engine, 'process_trading_day') as mock_process:
                    mock_process.return_value = MagicMock()
                    mock_process.return_value.daily_pnl = 25.0
                    mock_process.return_value.trades_count = 2
                    
                    # This should not raise an exception
                    try:
                        result = engine.run_backtest(symbol, self.test_date, self.test_date)
                        self.assertIsNotNone(result)
                    except Exception as e:
                        self.fail(f"Backtest failed for {symbol}: {e}")
    
    def test_symbol_specific_strike_selection(self):
        """Test that strike selection works correctly for different symbols"""
        for symbol in self.symbols:
            with self.subTest(symbol=symbol):
                trading_data = self.data_loader.load_trading_day(symbol, self.test_date)
                
                # Get a sample timestamp
                sample_timestamp = list(trading_data.option_data.keys())[100]
                option_chain = trading_data.option_data[sample_timestamp]
                spot_price = trading_data.spot_data[sample_timestamp]
                
                # Test strike selection
                strikes = self.data_loader.get_strikes_near_spot(
                    spot_price, option_chain, num_strikes=5
                )
                
                self.assertEqual(len(strikes), 5)
                self.assertTrue(all(isinstance(strike, float) for strike in strikes))
                
                # Strikes should be reasonably close to spot
                max_distance = max(abs(strike - spot_price) for strike in strikes)
                expected_max_distance = 20.0 if "QQQ" in symbol else 15.0
                self.assertLess(max_distance, expected_max_distance)
    
    def test_option_price_lookup_across_symbols(self):
        """Test option price lookup functionality across symbols"""
        for symbol in self.symbols:
            with self.subTest(symbol=symbol):
                trading_data = self.data_loader.load_trading_day(symbol, self.test_date)
                
                # Test price lookup
                sample_timestamp = list(trading_data.option_data.keys())[50]
                option_data = trading_data.option_data
                
                # Test existing option
                if "CE" in option_data[sample_timestamp]:
                    ce_strikes = list(option_data[sample_timestamp]["CE"].keys())
                    if ce_strikes:
                        price = self.data_loader.get_option_price(
                            option_data, sample_timestamp, "CE", ce_strikes[0]
                        )
                        self.assertIsNotNone(price)
                        self.assertGreater(price, 0)
                
                # Test non-existing option
                price = self.data_loader.get_option_price(
                    option_data, sample_timestamp, "CE", 999.0
                )
                self.assertIsNone(price)
    
    def test_data_validation_across_symbols(self):
        """Test data validation works for all symbols"""
        for symbol in self.symbols:
            with self.subTest(symbol=symbol):
                trading_data = self.data_loader.load_trading_day(symbol, self.test_date)
                
                # Validate spot data
                self.assertGreater(len(trading_data.spot_data), 100)
                spot_prices = list(trading_data.spot_data.values())
                self.assertTrue(all(price > 0 for price in spot_prices))
                
                # Validate option data
                self.assertGreater(len(trading_data.option_data), 100)
                
                # Check a few timestamps
                for timestamp in list(trading_data.option_data.keys())[:10]:
                    option_chain = trading_data.option_data[timestamp]
                    
                    if "CE" in option_chain:
                        ce_prices = list(option_chain["CE"].values())
                        self.assertTrue(all(price > 0 for price in ce_prices))
                    
                    if "PE" in option_chain:
                        pe_prices = list(option_chain["PE"].values())
                        self.assertTrue(all(price > 0 for price in pe_prices))


def run_multi_symbol_tests():
    """Run multi-symbol integration tests"""
    print("Running Multi-Symbol Integration Tests")
    print("=" * 50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiSymbolIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nMulti-Symbol Tests: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    run_multi_symbol_tests()