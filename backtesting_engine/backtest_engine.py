"""
Main backtesting engine orchestrator
"""

from typing import List, Dict, Optional, Union
from .models import TradingSetup, BacktestResults, DailyResults, MarketData, Trade, SetupResults, MultiSymbolTradingData
from .data_loader import DataLoader
from .position_manager import PositionManager
from .risk_manager import RiskManager
from .market_regime_detector import MarketRegimeDetector
from .dynamic_setup_manager import DynamicSetupManager


class BacktestEngine:
    """Main orchestrator that iterates through time intervals with multi-symbol support"""
    
    def __init__(self, data_path: str, setups: List[TradingSetup], daily_max_loss: float = 1000.0, 
                 enable_dynamic_management: bool = True, enable_multi_symbol: bool = False,
                 cross_symbol_risk_limit: float = 2000.0):
        self.data_loader = DataLoader(data_path)
        self.base_setups = setups
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager(daily_max_loss)
        
        # Multi-symbol support
        self.enable_multi_symbol = enable_multi_symbol
        self.cross_symbol_risk_limit = cross_symbol_risk_limit
        self.symbol_regime_detectors: Dict[str, MarketRegimeDetector] = {}
        self.symbol_setup_managers: Dict[str, DynamicSetupManager] = {}
        self.symbol_position_managers: Dict[str, PositionManager] = {}
        self.symbol_risk_managers: Dict[str, RiskManager] = {}
        
        # Market regime detection and dynamic setup management
        self.enable_dynamic_management = enable_dynamic_management
        self.market_regime_detector = MarketRegimeDetector() if enable_dynamic_management else None
        self.dynamic_setup_manager = DynamicSetupManager(setups) if enable_dynamic_management else None
        
        # Cross-symbol correlation tracking
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.correlation_history: Dict[str, List[float]] = {}  # symbol_pair -> correlation_values
        
        # Results tracking
        self.all_trades: List[Trade] = []
        self.daily_results: List[DailyResults] = []
        self.cumulative_pnl = 0.0
        self.symbol_performance: Dict[str, Dict] = {}  # symbol -> performance_metrics
    
    def run_backtest(self, symbols, start_date: str, end_date: str) -> BacktestResults:
        """Run backtest across multiple symbols and dates"""
        if isinstance(symbols, str):
            symbols = [symbols]  # Support single symbol as string
        
        if self.enable_multi_symbol and len(symbols) > 1:
            return self._run_multi_symbol_backtest(symbols, start_date, end_date)
        else:
            return self._run_single_symbol_backtest(symbols[0], start_date, end_date)
    
    def _run_single_symbol_backtest(self, symbol: str, start_date: str, end_date: str) -> BacktestResults:
        """Run backtest for a single symbol (original behavior)"""
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
    
    def _run_multi_symbol_backtest(self, symbols: List[str], start_date: str, end_date: str) -> BacktestResults:
        """Run backtest across multiple symbols with coordination and correlation monitoring"""
        print(f"Running multi-symbol backtest for {symbols} from {start_date} to {end_date}")
        
        # Initialize symbol-specific components
        self._initialize_symbol_components(symbols)
        
        # Get common available dates across all symbols
        common_dates = self._get_common_dates(symbols, start_date, end_date)
        print(f"Found {len(common_dates)} common trading days: {common_dates}")
        
        for date in common_dates:
            print(f"\nProcessing multi-symbol day {date}...")
            daily_result = self._process_multi_symbol_trading_day(symbols, date)
            if daily_result:
                self.daily_results.append(daily_result)
                self.cumulative_pnl += daily_result.daily_pnl
        
        return self._generate_final_results()
    
    def _initialize_symbol_components(self, symbols: List[str]) -> None:
        """Initialize symbol-specific components for multi-symbol backtesting"""
        for symbol in symbols:
            # Create symbol-specific regime detector and setup manager
            if self.enable_dynamic_management:
                self.symbol_regime_detectors[symbol] = MarketRegimeDetector()
                self.symbol_setup_managers[symbol] = DynamicSetupManager(self.base_setups)
            
            # Create symbol-specific position and risk managers
            self.symbol_position_managers[symbol] = PositionManager()
            self.symbol_risk_managers[symbol] = RiskManager(self.risk_manager.daily_max_loss)
            
            # Initialize performance tracking
            self.symbol_performance[symbol] = {
                'trades': [],
                'daily_pnls': [],
                'regime_performance': {}
            }
            
            # Initialize correlation tracking
            for other_symbol in symbols:
                if symbol != other_symbol:
                    pair_key = f"{symbol}_{other_symbol}"
                    self.correlation_history[pair_key] = []
    
    def _get_common_dates(self, symbols: List[str], start_date: str, end_date: str) -> List[str]:
        """Get dates that are available for all symbols"""
        symbol_dates = {}
        for symbol in symbols:
            available_dates = self.data_loader.get_available_dates(symbol)
            symbol_dates[symbol] = set(date for date in available_dates 
                                     if start_date <= date <= end_date)
        
        # Find intersection of all symbol dates
        if symbol_dates:
            common_dates = set.intersection(*symbol_dates.values())
            return sorted(list(common_dates))
        return []
    
    def _process_multi_symbol_trading_day(self, symbols: List[str], date: str) -> Optional[DailyResults]:
        """Process a single trading day across multiple symbols with coordination"""
        # Load data for all symbols
        symbol_data = self.data_loader.load_multiple_symbols(symbols, date, concurrent=True)
        
        if not symbol_data:
            print(f"Could not load data for any symbols on {date}")
            return None
        
        # Reset for new day across all symbols
        for symbol in symbols:
            if symbol in self.symbol_position_managers:
                self.symbol_position_managers[symbol].reset_positions()
                self.symbol_risk_managers[symbol].reset_daily_tracking()
            
            if self.enable_dynamic_management and symbol in self.symbol_setup_managers:
                self.symbol_setup_managers[symbol].reset_daily_adjustments()
        
        # Reset daily state for all setups
        for setup in self.base_setups:
            setup.reset_daily_state()
        
        daily_trades = []
        symbol_daily_pnls = {}
        positions_forced_closed = 0
        
        # Get all timestamps across all symbols and sort them
        all_timestamps = set()
        for data in symbol_data.values():
            all_timestamps.update(data.option_data.keys())
            all_timestamps.update(data.spot_data.keys())
        sorted_timestamps = sorted(all_timestamps)
        
        print(f"Processing {len(sorted_timestamps)} time intervals across {len(symbols)} symbols...")
        
        for timestamp in sorted_timestamps:
            # Create market data for each symbol at this timestamp
            symbol_market_data = {}
            for symbol, data in symbol_data.items():
                if (timestamp in data.option_data and timestamp in data.spot_data):
                    market_data = MarketData(
                        timestamp=timestamp,
                        symbol=symbol,
                        spot_price=data.spot_data[timestamp],
                        option_prices=data.option_data[timestamp],
                        available_strikes=list(set().union(*[
                            strikes.keys() for strikes in data.option_data[timestamp].values()
                        ]))
                    )
                    symbol_market_data[symbol] = market_data
            
            if not symbol_market_data:
                continue
            
            # Update regime detection and calculate cross-symbol correlations
            if self.enable_dynamic_management:
                self._update_cross_symbol_regimes(symbol_market_data)
                self._calculate_cross_symbol_correlations(symbol_market_data)
            
            # Process each symbol's time interval
            for symbol, market_data in symbol_market_data.items():
                if symbol in self.symbol_position_managers:
                    interval_trades = self._process_symbol_time_interval(
                        symbol, market_data, date)
                    daily_trades.extend(interval_trades)
            
            # Check cross-symbol risk limits
            if self._check_cross_symbol_risk_limits():
                print(f"Cross-symbol risk limit hit at timestamp {timestamp}. Closing all positions.")
                for symbol in symbols:
                    if symbol in symbol_market_data and symbol in self.symbol_position_managers:
                        emergency_trades = self.symbol_position_managers[symbol].close_all_positions(
                            symbol_market_data[symbol], "CROSS_SYMBOL_LIMIT", date)
                        daily_trades.extend(emergency_trades)
                break
            
            # Check if we've reached job end for any symbol
            job_end_reached = False
            for symbol, data in symbol_data.items():
                if timestamp >= data.job_end_idx:
                    print(f"Reached job end index {data.job_end_idx} for {symbol}. Force closing positions.")
                    if symbol in symbol_market_data and symbol in self.symbol_position_managers:
                        job_end_trades = self.symbol_position_managers[symbol].force_close_at_job_end(
                            data.job_end_idx, symbol_market_data[symbol], date)
                        daily_trades.extend(job_end_trades)
                        positions_forced_closed += len(job_end_trades)
                    job_end_reached = True
            
            if job_end_reached:
                break
        
        # Calculate daily results
        daily_pnl = sum(trade.pnl for trade in daily_trades)
        
        # Calculate symbol-specific P&Ls
        for symbol in symbols:
            symbol_pnl = sum(trade.pnl for trade in daily_trades 
                           if hasattr(trade, 'symbol') and trade.symbol == symbol)
            symbol_daily_pnls[symbol] = symbol_pnl
            
            # Update symbol performance tracking
            if symbol in self.symbol_performance:
                self.symbol_performance[symbol]['daily_pnls'].append(symbol_pnl)
                self.symbol_performance[symbol]['trades'].extend([
                    trade for trade in daily_trades 
                    if hasattr(trade, 'symbol') and trade.symbol == symbol
                ])
        
        # Calculate setup P&Ls
        setup_pnls = {}
        for setup in self.base_setups:
            setup_pnl = sum(trade.pnl for trade in daily_trades if trade.setup_id == setup.setup_id)
            setup_pnls[setup.setup_id] = setup_pnl
        
        # Collect regime transitions and parameter adjustments
        regime_transitions = []
        parameter_adjustments = []
        if self.enable_dynamic_management:
            for symbol in symbols:
                if symbol in self.symbol_setup_managers:
                    parameter_adjustments.extend(self.symbol_setup_managers[symbol].adjustment_history)
        
        # Add to all trades
        self.all_trades.extend(daily_trades)
        
        regime_info = ""
        if self.enable_dynamic_management and symbols:
            regimes = [self.symbol_regime_detectors[symbol].current_regime 
                      for symbol in symbols if symbol in self.symbol_regime_detectors]
            if regimes:
                regime_info = f" [Regimes: {', '.join(regimes)}]"
        
        print(f"Multi-symbol day {date} completed: {len(daily_trades)} trades, P&L: {daily_pnl:.2f}{regime_info}")
        
        return DailyResults(
            date=date,
            daily_pnl=daily_pnl,
            trades_count=len(daily_trades),
            positions_forced_closed_at_job_end=positions_forced_closed,
            setup_pnls=setup_pnls,
            symbol_pnls=symbol_daily_pnls,
            regime_transitions=regime_transitions,
            parameter_adjustments=parameter_adjustments
        )
    
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
        
        # Reset dynamic management for new day
        if self.enable_dynamic_management:
            self.dynamic_setup_manager.reset_daily_adjustments()
        
        # Reset daily state for all setups
        current_setups = self._get_current_setups()
        for setup in current_setups:
            setup.reset_daily_state()
        
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
                symbol=getattr(trading_day_data, 'symbol', symbol),  # Use symbol from data if available
                spot_price=trading_day_data.spot_data[timestamp],
                option_prices=trading_day_data.option_data[timestamp],
                available_strikes=list(set().union(*[
                    strikes.keys() for strikes in trading_day_data.option_data[timestamp].values()
                ]))
            )
            
            # Update market regime detection and dynamic setup management
            if self.enable_dynamic_management:
                self.market_regime_detector.update_market_data(market_data)
                current_regime = self.market_regime_detector.get_current_regime()
                regime_confidence = self.market_regime_detector.get_regime_confidence()
                
                # Update dynamic setup manager with regime information
                self.dynamic_setup_manager.update_market_regime(
                    current_regime, regime_confidence, market_data)
            
            # Process this time interval
            interval_trades = self.process_time_interval(market_data, date)
            daily_trades.extend(interval_trades)
            
            # Check daily risk limits
            if self.check_daily_risk_limits():
                print(f"Daily risk limit hit at timestamp {timestamp}. Closing all positions.")
                emergency_trades = self.position_manager.close_all_positions(market_data, "DAILY_LIMIT", date)
                daily_trades.extend(emergency_trades)
                break
            
            # Check if we've reached job end
            if timestamp >= trading_day_data.job_end_idx:
                print(f"Reached job end index {trading_day_data.job_end_idx}. Force closing positions.")
                job_end_trades = self.position_manager.force_close_at_job_end(
                    trading_day_data.job_end_idx, market_data, date)
                daily_trades.extend(job_end_trades)
                positions_forced_closed = len(job_end_trades)
                break
        
        # Calculate daily results
        daily_pnl = sum(trade.pnl for trade in daily_trades)
        setup_pnls = {}
        for setup in self.base_setups:
            setup_pnl = sum(trade.pnl for trade in daily_trades if trade.setup_id == setup.setup_id)
            setup_pnls[setup.setup_id] = setup_pnl
        
        # Collect regime transitions and parameter adjustments if dynamic management enabled
        regime_transitions = []
        parameter_adjustments = []
        if self.enable_dynamic_management:
            # Get regime transitions for the day (simplified - would need more sophisticated tracking)
            if hasattr(self.market_regime_detector, 'regime_change_count') and self.market_regime_detector.regime_change_count > 0:
                from .models import RegimeTransition
                regime_transitions.append(RegimeTransition(
                    timestamp=self.dynamic_setup_manager.last_regime_change_time,
                    from_regime="UNKNOWN",  # Would need better tracking
                    to_regime=self.dynamic_setup_manager.current_regime,
                    confidence=self.dynamic_setup_manager.regime_confidence
                ))
            
            # Get parameter adjustments for the day
            parameter_adjustments = [adj for adj in self.dynamic_setup_manager.adjustment_history]
        
        # Add to all trades
        self.all_trades.extend(daily_trades)
        
        regime_info = f" [{self.dynamic_setup_manager.current_regime}]" if self.enable_dynamic_management else ""
        print(f"Day {date} completed: {len(daily_trades)} trades, P&L: {daily_pnl:.2f}{regime_info}")
        
        return DailyResults(
            date=date,
            daily_pnl=daily_pnl,
            trades_count=len(daily_trades),
            positions_forced_closed_at_job_end=positions_forced_closed,
            setup_pnls=setup_pnls,
            regime_transitions=regime_transitions,
            parameter_adjustments=parameter_adjustments
        )
    
    def process_time_interval(self, market_data: MarketData, date: str = "") -> List[Trade]:
        """Process a single 5-second interval"""
        interval_trades = []
        
        # Get current setups (either base setups or dynamically adjusted ones)
        current_setups = self._get_current_setups()
        
        # 1. Check entry conditions for all setups
        for setup in current_setups:
            if setup.check_entry_condition(market_data.timestamp):
                # 2. Create new positions if entry triggered
                new_positions = setup.create_positions(market_data)
                for position in new_positions:
                    position_id = self.position_manager.add_position(position)
                    # Reduced logging - only show key info
                    regime_info = f" [{market_data.regime_classification}]" if hasattr(market_data, 'regime_classification') else ""
                    print(f"📈 {setup.setup_id}: Opened at {market_data.timestamp}, Spot={market_data.spot_price:.2f}, Strikes={position.strikes}{regime_info}")
        
        # 3. Update P&L for existing positions and check exit conditions
        closed_trades = self.position_manager.update_positions(market_data, date)
        interval_trades.extend(closed_trades)
        
        # 3a. Handle gamma scalping positions with rebalancing logic
        gamma_trades = self.position_manager.update_gamma_scalping_positions(market_data, current_setups, date)
        interval_trades.extend(gamma_trades)
        
        # Track performance of dynamic adjustments
        if self.enable_dynamic_management:
            for trade in closed_trades:
                # Determine if trade was made with adjusted parameters
                was_adjusted = self._was_trade_adjusted(trade)
                self.dynamic_setup_manager.track_adjustment_performance(trade, was_adjusted)
        
        # 4. Check time-based closures
        time_based_trades = self.position_manager.check_time_based_closures(
            market_data.timestamp, current_setups)
        interval_trades.extend(time_based_trades)
        
        # Track performance for time-based closures too
        if self.enable_dynamic_management:
            for trade in time_based_trades:
                was_adjusted = self._was_trade_adjusted(trade)
                self.dynamic_setup_manager.track_adjustment_performance(trade, was_adjusted)
        
        return interval_trades
    
    def check_daily_risk_limits(self) -> bool:
        """Check if daily risk limits are breached"""
        total_pnl = self.position_manager.get_total_pnl()
        return self.risk_manager.should_close_all_positions(total_pnl)
    
    def _generate_final_results(self) -> BacktestResults:
        """Generate final backtest results with multi-symbol support"""
        total_pnl = sum(trade.pnl for trade in self.all_trades)
        total_trades = len(self.all_trades)
        
        # Calculate win rate
        winning_trades = [trade for trade in self.all_trades if trade.pnl > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Calculate setup performance with symbol and regime breakdowns
        setup_performance = {}
        for setup in self.base_setups:
            setup_trades = [trade for trade in self.all_trades if trade.setup_id == setup.setup_id]
            setup_pnl = sum(trade.pnl for trade in setup_trades)
            setup_wins = [trade for trade in setup_trades if trade.pnl > 0]
            setup_losses = [trade for trade in setup_trades if trade.pnl < 0]
            
            # Calculate symbol-specific performance for this setup
            symbol_performance = {}
            if self.enable_multi_symbol:
                for symbol in self.symbol_performance.keys():
                    symbol_setup_trades = [trade for trade in setup_trades 
                                         if hasattr(trade, 'symbol') and trade.symbol == symbol]
                    if symbol_setup_trades:
                        symbol_performance[symbol] = sum(trade.pnl for trade in symbol_setup_trades)
            
            # Calculate regime-specific performance for this setup
            regime_performance = {}
            if self.enable_dynamic_management:
                # This would need more sophisticated tracking of which regime each trade was made in
                # For now, we'll leave it as placeholder
                pass
            
            setup_performance[setup.setup_id] = SetupResults(
                setup_id=setup.setup_id,
                total_pnl=setup_pnl,
                total_trades=len(setup_trades),
                win_rate=len(setup_wins) / len(setup_trades) if setup_trades else 0.0,
                avg_win=sum(trade.pnl for trade in setup_wins) / len(setup_wins) if setup_wins else 0.0,
                avg_loss=sum(trade.pnl for trade in setup_losses) / len(setup_losses) if setup_losses else 0.0,
                max_drawdown=0.0,  # TODO: Calculate setup-specific drawdown
                symbol_performance=symbol_performance,
                regime_performance=regime_performance
            )
        
        # Calculate symbol performance
        symbol_performance_results = {}
        if self.enable_multi_symbol:
            from .models import SymbolResults
            for symbol, perf_data in self.symbol_performance.items():
                symbol_trades = perf_data['trades']
                symbol_pnl = sum(trade.pnl for trade in symbol_trades)
                symbol_wins = [trade for trade in symbol_trades if trade.pnl > 0]
                
                # Calculate correlations with other symbols
                correlations = {}
                for other_symbol in self.symbol_performance.keys():
                    if other_symbol != symbol and symbol in self.correlation_matrix:
                        correlations[other_symbol] = self.correlation_matrix[symbol].get(other_symbol, 0.0)
                
                symbol_performance_results[symbol] = SymbolResults(
                    symbol=symbol,
                    total_pnl=symbol_pnl,
                    total_trades=len(symbol_trades),
                    win_rate=len(symbol_wins) / len(symbol_trades) if symbol_trades else 0.0,
                    correlation_with_other_symbols=correlations
                )
        
        # Calculate regime performance
        regime_performance_results = {}
        if self.enable_dynamic_management:
            # This would need more sophisticated tracking
            # For now, we'll aggregate from symbol-specific regime detectors
            from .models import RegimeResults
            all_regimes = set()
            for detector in self.symbol_regime_detectors.values():
                if hasattr(detector, 'regime_history'):
                    all_regimes.update(detector.regime_history)
            
            # Placeholder regime performance calculation
            for regime in all_regimes:
                regime_performance_results[regime] = RegimeResults(
                    regime=regime,
                    total_pnl=0.0,  # Would need proper tracking
                    total_trades=0,
                    win_rate=0.0,
                    avg_duration=0.0,
                    transition_performance=0.0
                )
        
        # Add dynamic adjustment performance if enabled
        dynamic_adjustment_performance = None
        if self.enable_dynamic_management:
            from .models import DynamicAdjustmentResults
            
            # Aggregate adjustment statistics across all symbols
            total_adjustments = 0
            adjustment_performance = {}
            static_vs_dynamic_comparison = 0.0
            regime_accuracy = 0.0
            
            if self.enable_multi_symbol:
                # Aggregate from symbol-specific setup managers
                for symbol, setup_manager in self.symbol_setup_managers.items():
                    if hasattr(setup_manager, 'get_adjustment_statistics'):
                        stats = setup_manager.get_adjustment_statistics()
                        total_adjustments += stats.get('total_adjustments', 0)
                        
                        # Merge adjustment performance
                        for adj_type, performance in setup_manager.adjustment_performance.items():
                            if adj_type not in adjustment_performance:
                                adjustment_performance[adj_type] = []
                            adjustment_performance[adj_type].append(performance)
                
                # Average the performance metrics
                for adj_type, performances in adjustment_performance.items():
                    adjustment_performance[adj_type] = sum(performances) / len(performances)
            
            elif hasattr(self.dynamic_setup_manager, 'get_adjustment_statistics'):
                adjustment_stats = self.dynamic_setup_manager.get_adjustment_statistics()
                total_adjustments = adjustment_stats['total_adjustments']
                adjustment_performance = self.dynamic_setup_manager.adjustment_performance
                static_vs_dynamic_comparison = adjustment_stats['static_vs_dynamic_comparison']
                regime_accuracy = adjustment_stats['regime_accuracy']
            
            dynamic_adjustment_performance = DynamicAdjustmentResults(
                total_adjustments=total_adjustments,
                adjustment_performance=adjustment_performance,
                static_vs_dynamic_comparison=static_vs_dynamic_comparison,
                regime_accuracy=regime_accuracy
            )
        
        return BacktestResults(
            total_pnl=total_pnl,
            daily_results=self.daily_results,
            trade_log=self.all_trades,
            setup_performance=setup_performance,
            symbol_performance=symbol_performance_results,
            regime_performance=regime_performance_results,
            dynamic_adjustment_performance=dynamic_adjustment_performance,
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
    
    def run_single_symbol_backtest(self, symbol: str, start_date: str, end_date: str) -> BacktestResults:
        """Convenience method for single symbol backtesting (backward compatibility)"""
        return self.run_backtest([symbol], start_date, end_date)
    
    def run_multi_symbol_backtest(self, symbols: List[str], start_date: str, end_date: str) -> BacktestResults:
        """Convenience method for multi-symbol backtesting"""
        original_multi_symbol = self.enable_multi_symbol
        self.enable_multi_symbol = True
        try:
            return self.run_backtest(symbols, start_date, end_date)
        finally:
            self.enable_multi_symbol = original_multi_symbol
    
    def _get_current_setups(self) -> List[TradingSetup]:
        """
        Get current setups (either base setups or dynamically adjusted ones)
        
        Returns:
            List of current active setups
        """
        if self.enable_dynamic_management:
            return self.dynamic_setup_manager.get_adjusted_setups()
        else:
            return self.base_setups
    
    def _process_symbol_time_interval(self, symbol: str, market_data: MarketData, date: str = "") -> List[Trade]:
        """Process a single 5-second interval for a specific symbol"""
        interval_trades = []
        
        # Get symbol-specific components
        position_manager = self.symbol_position_managers.get(symbol, self.position_manager)
        
        # Get current setups for this symbol
        current_setups = self._get_symbol_current_setups(symbol)
        
        # 1. Check entry conditions for all setups
        for setup in current_setups:
            if setup.check_entry_condition(market_data.timestamp):
                # 2. Create new positions if entry triggered
                new_positions = setup.create_positions(market_data)
                for position in new_positions:
                    # Add symbol information to position
                    if hasattr(position, 'symbol'):
                        position.symbol = symbol
                    position_id = position_manager.add_position(position)
                    
                    regime_info = f" [{market_data.regime_classification}]" if hasattr(market_data, 'regime_classification') else ""
                    print(f"📈 {symbol} {setup.setup_id}: Opened at {market_data.timestamp}, Spot={market_data.spot_price:.2f}, Strikes={position.strikes}{regime_info}")
        
        # 3. Update P&L for existing positions and check exit conditions
        closed_trades = position_manager.update_positions(market_data, date)
        
        # Add symbol information to trades
        for trade in closed_trades:
            if hasattr(trade, 'symbol'):
                trade.symbol = symbol
        
        interval_trades.extend(closed_trades)
        
        # 3a. Handle gamma scalping positions with rebalancing logic
        gamma_trades = position_manager.update_gamma_scalping_positions(market_data, current_setups, date)
        for trade in gamma_trades:
            if hasattr(trade, 'symbol'):
                trade.symbol = symbol
        interval_trades.extend(gamma_trades)
        
        # Track performance of dynamic adjustments
        if self.enable_dynamic_management and symbol in self.symbol_setup_managers:
            for trade in closed_trades + gamma_trades:
                was_adjusted = self._was_symbol_trade_adjusted(symbol, trade)
                self.symbol_setup_managers[symbol].track_adjustment_performance(trade, was_adjusted)
        
        # 4. Check time-based closures
        time_based_trades = position_manager.check_time_based_closures(
            market_data.timestamp, current_setups)
        
        for trade in time_based_trades:
            if hasattr(trade, 'symbol'):
                trade.symbol = symbol
        interval_trades.extend(time_based_trades)
        
        # Track performance for time-based closures too
        if self.enable_dynamic_management and symbol in self.symbol_setup_managers:
            for trade in time_based_trades:
                was_adjusted = self._was_symbol_trade_adjusted(symbol, trade)
                self.symbol_setup_managers[symbol].track_adjustment_performance(trade, was_adjusted)
        
        return interval_trades
    
    def _update_cross_symbol_regimes(self, symbol_market_data: Dict[str, MarketData]) -> None:
        """Update regime detection for all symbols and detect cross-symbol divergences"""
        for symbol, market_data in symbol_market_data.items():
            if symbol in self.symbol_regime_detectors:
                self.symbol_regime_detectors[symbol].update_market_data(market_data)
                
                # Update dynamic setup manager with regime information
                if symbol in self.symbol_setup_managers:
                    current_regime = self.symbol_regime_detectors[symbol].get_current_regime()
                    regime_confidence = self.symbol_regime_detectors[symbol].get_regime_confidence()
                    self.symbol_setup_managers[symbol].update_market_regime(
                        current_regime, regime_confidence, market_data)
        
        # Detect cross-symbol regime divergences
        if len(symbol_market_data) > 1:
            self._detect_regime_divergences(symbol_market_data)
    
    def _detect_regime_divergences(self, symbol_market_data: Dict[str, MarketData]) -> None:
        """Detect when different symbols are in different regimes"""
        symbols = list(symbol_market_data.keys())
        regimes = {}
        
        for symbol in symbols:
            if symbol in self.symbol_regime_detectors:
                regimes[symbol] = self.symbol_regime_detectors[symbol].get_current_regime()
        
        # Check for divergences (simplified - could be more sophisticated)
        if len(set(regimes.values())) > 1:
            print(f"⚠️  Regime divergence detected: {regimes}")
            
            # Potentially adjust risk limits or strategy selection based on divergence
            # This is a placeholder for more sophisticated divergence handling
    
    def _calculate_cross_symbol_correlations(self, symbol_market_data: Dict[str, MarketData]) -> None:
        """Calculate and update cross-symbol correlations"""
        symbols = list(symbol_market_data.keys())
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                pair_key = f"{symbol1}_{symbol2}"
                
                # Calculate correlation using price velocity (simplified)
                if (symbol1 in self.symbol_regime_detectors and 
                    symbol2 in self.symbol_regime_detectors):
                    
                    velocity1 = self.symbol_regime_detectors[symbol1].get_price_velocity()
                    velocity2 = self.symbol_regime_detectors[symbol2].get_price_velocity()
                    
                    # Simple correlation approximation (would need more sophisticated calculation)
                    correlation = min(abs(velocity1 * velocity2), 1.0) if velocity1 != 0 and velocity2 != 0 else 0.0
                    
                    if pair_key in self.correlation_history:
                        self.correlation_history[pair_key].append(correlation)
                        
                        # Keep only recent correlations (last 60 periods = 5 minutes)
                        if len(self.correlation_history[pair_key]) > 60:
                            self.correlation_history[pair_key] = self.correlation_history[pair_key][-60:]
                        
                        # Update correlation matrix with average recent correlation
                        if symbol1 not in self.correlation_matrix:
                            self.correlation_matrix[symbol1] = {}
                        self.correlation_matrix[symbol1][symbol2] = sum(self.correlation_history[pair_key]) / len(self.correlation_history[pair_key])
    
    def _check_cross_symbol_risk_limits(self) -> bool:
        """Check if cross-symbol risk limits are breached"""
        if not self.enable_multi_symbol:
            return False
        
        total_cross_symbol_pnl = 0.0
        for symbol, position_manager in self.symbol_position_managers.items():
            total_cross_symbol_pnl += position_manager.get_total_pnl()
        
        return total_cross_symbol_pnl <= -self.cross_symbol_risk_limit
    
    def _get_symbol_current_setups(self, symbol: str) -> List[TradingSetup]:
        """Get current setups for a specific symbol"""
        if self.enable_dynamic_management and symbol in self.symbol_setup_managers:
            return self.symbol_setup_managers[symbol].get_adjusted_setups()
        else:
            return self.base_setups
    
    def _was_symbol_trade_adjusted(self, symbol: str, trade: Trade) -> bool:
        """Determine if a trade was made with dynamically adjusted parameters for a specific symbol"""
        if not self.enable_dynamic_management or symbol not in self.symbol_setup_managers:
            return False
        
        # Check if there were any adjustments for this setup
        for adjustment in self.symbol_setup_managers[symbol].adjustment_history:
            if adjustment.setup_id == trade.setup_id:
                # If adjustment was made before trade entry, consider it adjusted
                if adjustment.timestamp <= trade.entry_timeindex:
                    return True
        
        return False
    
    def _was_trade_adjusted(self, trade: Trade) -> bool:
        """
        Determine if a trade was made with dynamically adjusted parameters
        
        Args:
            trade: Trade to check
            
        Returns:
            True if trade was made with adjusted parameters
        """
        if not self.enable_dynamic_management:
            return False
        
        # For multi-symbol, check symbol-specific adjustments
        if self.enable_multi_symbol and hasattr(trade, 'symbol'):
            return self._was_symbol_trade_adjusted(trade.symbol, trade)
        
        # Check if there were any adjustments for this setup
        for adjustment in self.dynamic_setup_manager.adjustment_history:
            if adjustment.setup_id == trade.setup_id:
                # If adjustment was made before trade entry, consider it adjusted
                if adjustment.timestamp <= trade.entry_timeindex:
                    return True
        
        return False