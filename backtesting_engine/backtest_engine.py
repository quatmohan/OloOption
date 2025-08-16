"""
Main backtesting engine orchestrator
"""

from typing import List, Dict, Optional
from .models import TradingSetup, BacktestResults, DailyResults, MarketData, Trade, SetupResults
from .data_loader import DataLoader
from .position_manager import PositionManager
from .risk_manager import RiskManager


class BacktestEngine:
    """Main orchestrator that iterates through time intervals"""
    
    def __init__(self, data_path: str, setups: List[TradingSetup], daily_max_loss: float = 1000.0):
        self.data_loader = DataLoader(data_path)
        self.setups = setups
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager(daily_max_loss)
        
        # Results tracking
        self.all_trades: List[Trade] = []
        self.daily_results: List[DailyResults] = []
        self.cumulative_pnl = 0.0
    
    def run_backtest(self, symbol: str, start_date: str, end_date: str) -> BacktestResults:
        """Run backtest across multiple dates"""
        available_dates = self.data_loader.get_available_dates(symbol)
        
        # Filter dates within range
        test_dates = [date for date in available_dates 
                     if start_date <= date <= end_date]
        
        print(f"Running backtest for {symbol} from {start_date} to {end_date}")
        print(f"Found {len(test_dates)} trading days: {test_dates}")
        
        for date in test_dates:
            print(f"\nProcessing {date}...")
            daily_result = self.process_trading_day(symbol, date)
            if daily_result:
                self.daily_results.append(daily_result)
                self.cumulative_pnl += daily_result.daily_pnl
        
        return self._generate_final_results()
    
    def process_trading_day(self, symbol: str, date: str) -> Optional[DailyResults]:
        """Process a single trading day"""
        # Load data for the day
        trading_day_data = self.data_loader.load_trading_day(symbol, date)
        if not trading_day_data:
            print(f"Could not load data for {date}")
            return None
        
        # Reset for new day
        self.position_manager.reset_positions()
        self.risk_manager.reset_daily_tracking()
        
        daily_trades = []
        positions_forced_closed = 0
        
        # Get all timestamps and sort them
        all_timestamps = set(trading_day_data.option_data.keys())
        all_timestamps.update(trading_day_data.spot_data.keys())
        sorted_timestamps = sorted(all_timestamps)
        
        print(f"Processing {len(sorted_timestamps)} time intervals...")
        
        for timestamp in sorted_timestamps:
            # Skip if we don't have both option and spot data
            if (timestamp not in trading_day_data.option_data or 
                timestamp not in trading_day_data.spot_data):
                continue
            
            # Create market data
            market_data = MarketData(
                timestamp=timestamp,
                spot_price=trading_day_data.spot_data[timestamp],
                option_prices=trading_day_data.option_data[timestamp],
                available_strikes=list(set().union(*[
                    strikes.keys() for strikes in trading_day_data.option_data[timestamp].values()
                ]))
            )
            
            # Process this time interval
            interval_trades = self.process_time_interval(market_data)
            daily_trades.extend(interval_trades)
            
            # Check daily risk limits
            if self.check_daily_risk_limits():
                print(f"Daily risk limit hit at timestamp {timestamp}. Closing all positions.")
                emergency_trades = self.position_manager.close_all_positions(market_data, "DAILY_LIMIT")
                daily_trades.extend(emergency_trades)
                break
            
            # Check if we've reached job end
            if timestamp >= trading_day_data.job_end_idx:
                print(f"Reached job end index {trading_day_data.job_end_idx}. Force closing positions.")
                job_end_trades = self.position_manager.force_close_at_job_end(
                    trading_day_data.job_end_idx, market_data)
                daily_trades.extend(job_end_trades)
                positions_forced_closed = len(job_end_trades)
                break
        
        # Calculate daily results
        daily_pnl = sum(trade.pnl for trade in daily_trades)
        setup_pnls = {}
        for setup in self.setups:
            setup_pnl = sum(trade.pnl for trade in daily_trades if trade.setup_id == setup.setup_id)
            setup_pnls[setup.setup_id] = setup_pnl
        
        # Add to all trades
        self.all_trades.extend(daily_trades)
        
        print(f"Day {date} completed: {len(daily_trades)} trades, P&L: {daily_pnl:.2f}")
        
        return DailyResults(
            date=date,
            daily_pnl=daily_pnl,
            trades_count=len(daily_trades),
            positions_forced_closed_at_job_end=positions_forced_closed,
            setup_pnls=setup_pnls
        )
    
    def process_time_interval(self, market_data: MarketData) -> List[Trade]:
        """Process a single 5-second interval"""
        interval_trades = []
        
        # 1. Check entry conditions for all setups
        for setup in self.setups:
            if setup.check_entry_condition(market_data.timestamp):
                # 2. Create new positions if entry triggered
                new_positions = setup.create_positions(market_data)
                for position in new_positions:
                    position_id = self.position_manager.add_position(position)
                    print(f"Opened position {position_id} for setup {setup.setup_id} at timestamp {market_data.timestamp}")
                    print(f"  Spot Price: {market_data.spot_price:.2f}")
                    print(f"  Selected Strikes: {position.strikes}")
                    print(f"  Entry Prices: {position.entry_prices}")
                    print(f"  Target P&L: ${position.target_pnl:.2f}, Stop Loss: ${position.stop_loss_pnl:.2f}")
        
        # 3. Update P&L for existing positions and check exit conditions
        closed_trades = self.position_manager.update_positions(market_data)
        interval_trades.extend(closed_trades)
        
        # 4. Check time-based closures
        time_based_trades = self.position_manager.check_time_based_closures(
            market_data.timestamp, self.setups)
        interval_trades.extend(time_based_trades)
        
        return interval_trades
    
    def check_daily_risk_limits(self) -> bool:
        """Check if daily risk limits are breached"""
        total_pnl = self.position_manager.get_total_pnl()
        return self.risk_manager.should_close_all_positions(total_pnl)
    
    def _generate_final_results(self) -> BacktestResults:
        """Generate final backtest results"""
        total_pnl = sum(trade.pnl for trade in self.all_trades)
        total_trades = len(self.all_trades)
        
        # Calculate win rate
        winning_trades = [trade for trade in self.all_trades if trade.pnl > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Calculate setup performance
        setup_performance = {}
        for setup in self.setups:
            setup_trades = [trade for trade in self.all_trades if trade.setup_id == setup.setup_id]
            setup_pnl = sum(trade.pnl for trade in setup_trades)
            setup_wins = [trade for trade in setup_trades if trade.pnl > 0]
            setup_losses = [trade for trade in setup_trades if trade.pnl < 0]
            
            setup_performance[setup.setup_id] = SetupResults(
                setup_id=setup.setup_id,
                total_pnl=setup_pnl,
                total_trades=len(setup_trades),
                win_rate=len(setup_wins) / len(setup_trades) if setup_trades else 0.0,
                avg_win=sum(trade.pnl for trade in setup_wins) / len(setup_wins) if setup_wins else 0.0,
                avg_loss=sum(trade.pnl for trade in setup_losses) / len(setup_losses) if setup_losses else 0.0,
                max_drawdown=0.0  # TODO: Calculate setup-specific drawdown
            )
        
        return BacktestResults(
            total_pnl=total_pnl,
            daily_results=self.daily_results,
            trade_log=self.all_trades,
            setup_performance=setup_performance,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            total_trades=total_trades
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.all_trades:
            return 0.0
        
        cumulative_pnl = 0.0
        peak = 0.0
        max_drawdown = 0.0
        
        for trade in self.all_trades:
            cumulative_pnl += trade.pnl
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown