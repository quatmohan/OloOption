"""
Advanced reporting and analytics for backtesting results
"""

import csv
import os
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from .models import (BacktestResults, Trade, DailyResults, SetupResults, 
                     SymbolResults, RegimeResults, DynamicAdjustmentResults,
                     RegimeTransition, ParameterAdjustment)
from .html_reporter import HTMLReporter


class BacktestReporter:
    """Advanced reporting and analytics for backtest results"""
    
    def __init__(self, results: BacktestResults):
        self.results = results
        self.report_dir = "backtest_reports"
        self._ensure_report_dir()
    
    def _ensure_report_dir(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def generate_full_report(self, symbols: List[str], start_date: str, end_date: str) -> str:
        """Generate comprehensive report and save to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol_str = "_".join(symbols) if isinstance(symbols, list) else str(symbols)
        report_prefix = f"{symbol_str}_{start_date}_to_{end_date}_{timestamp}"
        
        # Generate console summary
        summary = self._generate_summary_report(symbols, start_date, end_date)
        
        # Export detailed data to CSV files
        self._export_trades_csv(f"{report_prefix}_trades.csv")
        self._export_daily_results_csv(f"{report_prefix}_daily.csv")
        self._export_setup_performance_csv(f"{report_prefix}_setups.csv")
        
        # Export advanced analytics
        self._export_regime_analysis_csv(f"{report_prefix}_regime_analysis.csv")
        self._export_dynamic_adjustments_csv(f"{report_prefix}_dynamic_adjustments.csv")
        self._export_symbol_performance_csv(f"{report_prefix}_symbol_performance.csv")
        self._export_pattern_analysis_csv(f"{report_prefix}_pattern_analysis.csv")
        self._export_correlation_analysis_csv(f"{report_prefix}_correlation_analysis.csv")
        
        # Save summary to text file
        summary_file = os.path.join(self.report_dir, f"{report_prefix}_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        # Generate HTML report
        html_reporter = HTMLReporter(self.results)
        html_file = html_reporter.generate_html_report(symbols, start_date, end_date)
        
        print(f"\n📊 Advanced Analytics Reports saved to {self.report_dir}/ directory:")
        print(f"   - {report_prefix}_summary.txt")
        print(f"   - {report_prefix}_trades.csv")
        print(f"   - {report_prefix}_daily.csv")
        print(f"   - {report_prefix}_setups.csv")
        print(f"   - {report_prefix}_regime_analysis.csv")
        print(f"   - {report_prefix}_dynamic_adjustments.csv")
        print(f"   - {report_prefix}_symbol_performance.csv")
        print(f"   - {report_prefix}_pattern_analysis.csv")
        print(f"   - {report_prefix}_correlation_analysis.csv")
        print(f"   - {os.path.basename(html_file)} (HTML Report)")
        
        return summary
    
    def _generate_summary_report(self, symbols: List[str], start_date: str, end_date: str) -> str:
        """Generate formatted summary report"""
        lines = []
        lines.append("=" * 80)
        symbol_str = ", ".join(symbols) if isinstance(symbols, list) else str(symbols)
        lines.append(f"OPTIONS BACKTESTING REPORT - {symbol_str}")
        lines.append(f"Period: {start_date} to {end_date}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        # Overall Performance
        lines.append("\n📈 OVERALL PERFORMANCE")
        lines.append("-" * 40)
        lines.append(f"Total P&L:           ${self.results.total_pnl:>10,.2f}")
        lines.append(f"Total Trades:        {self.results.total_trades:>10,}")
        lines.append(f"Win Rate:            {self.results.win_rate:>10.1%}")
        lines.append(f"Max Drawdown:        ${self.results.max_drawdown:>10,.2f}")
        
        if self.results.total_trades > 0:
            avg_trade = self.results.total_pnl / self.results.total_trades
            lines.append(f"Average Trade:       ${avg_trade:>10,.2f}")
        
        # Daily Performance
        lines.append("\n📅 DAILY PERFORMANCE")
        lines.append("-" * 40)
        lines.append(f"{'Date':<12} {'P&L':<10} {'Trades':<8} {'Forced Closes':<14}")
        lines.append("-" * 44)
        
        for daily in self.results.daily_results:
            lines.append(f"{daily.date:<12} ${daily.daily_pnl:>8.2f} {daily.trades_count:>6} {daily.positions_forced_closed_at_job_end:>12}")
        
        # Setup Performance
        lines.append("\n🎯 SETUP PERFORMANCE")
        lines.append("-" * 40)
        lines.append(f"{'Setup ID':<15} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Win':<10} {'Avg Loss':<10}")
        lines.append("-" * 73)
        
        for setup_id, perf in self.results.setup_performance.items():
            avg_win_str = f"${perf.avg_win:.2f}" if perf.avg_win > 0 else "N/A"
            avg_loss_str = f"${perf.avg_loss:.2f}" if perf.avg_loss < 0 else "N/A"
            lines.append(f"{setup_id:<15} ${perf.total_pnl:>8.2f} {perf.total_trades:>6} {perf.win_rate:>8.1%} {avg_win_str:>9} {avg_loss_str:>9}")
        
        # Trade Statistics
        lines.append("\n📊 TRADE STATISTICS")
        lines.append("-" * 40)
        
        winning_trades = [t for t in self.results.trade_log if t.pnl > 0]
        losing_trades = [t for t in self.results.trade_log if t.pnl < 0]
        
        lines.append(f"Winning Trades:      {len(winning_trades):>10}")
        lines.append(f"Losing Trades:       {len(losing_trades):>10}")
        
        if winning_trades:
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades)
            max_win = max(t.pnl for t in winning_trades)
            lines.append(f"Average Win:         ${avg_win:>10.2f}")
            lines.append(f"Largest Win:         ${max_win:>10.2f}")
        
        if losing_trades:
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades)
            max_loss = min(t.pnl for t in losing_trades)
            lines.append(f"Average Loss:        ${avg_loss:>10.2f}")
            lines.append(f"Largest Loss:        ${max_loss:>10.2f}")
        
        # Exit Reason Analysis
        lines.append("\n🚪 EXIT REASON ANALYSIS")
        lines.append("-" * 40)
        
        exit_reasons = {}
        for trade in self.results.trade_log:
            exit_reasons[trade.exit_reason] = exit_reasons.get(trade.exit_reason, 0) + 1
        
        for reason, count in sorted(exit_reasons.items()):
            pct = count / self.results.total_trades * 100 if self.results.total_trades > 0 else 0
            lines.append(f"{reason:<15} {count:>6} ({pct:>5.1f}%)")
        
        # Multi-Symbol Performance (if available)
        if self.results.symbol_performance:
            lines.append("\n🎯 MULTI-SYMBOL PERFORMANCE")
            lines.append("-" * 40)
            lines.append(f"{'Symbol':<15} {'P&L':<10} {'Trades':<8} {'Win Rate':<10}")
            lines.append("-" * 43)
            
            for symbol, perf in self.results.symbol_performance.items():
                lines.append(f"{symbol:<15} ${perf.total_pnl:>8.2f} {perf.total_trades:>6} {perf.win_rate:>8.1%}")
        
        # Regime Performance (if available)
        if self.results.regime_performance:
            lines.append("\n🌊 REGIME PERFORMANCE")
            lines.append("-" * 40)
            lines.append(f"{'Regime':<15} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Duration':<12}")
            lines.append("-" * 55)
            
            for regime, perf in self.results.regime_performance.items():
                lines.append(f"{regime:<15} ${perf.total_pnl:>8.2f} {perf.total_trades:>6} {perf.win_rate:>8.1%} {perf.avg_duration:>10.1f}")
        
        # Dynamic Adjustment Performance (if available)
        if self.results.dynamic_adjustment_performance:
            lines.append("\n⚡ DYNAMIC ADJUSTMENT PERFORMANCE")
            lines.append("-" * 40)
            adj_perf = self.results.dynamic_adjustment_performance
            lines.append(f"Total Adjustments:   {adj_perf.total_adjustments:>10}")
            lines.append(f"Static vs Dynamic:   ${adj_perf.static_vs_dynamic_comparison:>10.2f}")
            lines.append(f"Regime Accuracy:     {adj_perf.regime_accuracy:>10.1%}")
        
        return "\n".join(lines)
    
    def _export_trades_csv(self, filename: str):
        """Export detailed trade log to CSV"""
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'trade_id', 'setup_id', 'date', 'entry_time', 'exit_time', 'duration',
                'exit_reason', 'ce_sell_strike', 'pe_sell_strike', 'ce_sell_entry', 
                'pe_sell_entry', 'ce_sell_exit', 'pe_sell_exit', 'ce_sell_pnl', 'pe_sell_pnl',
                'ce_hedge_strike', 'pe_hedge_strike', 'ce_hedge_buy_entry', 'pe_hedge_buy_entry', 
                'ce_hedge_buy_exit', 'pe_hedge_buy_exit', 'ce_hedge_pnl', 'pe_hedge_pnl',
                'total_pnl', 'quantity'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, trade in enumerate(self.results.trade_log, 1):
                # Initialize all values
                ce_sell_strike = pe_sell_strike = ce_buy_strike = pe_buy_strike = 'N/A'
                ce_sell_entry = pe_sell_entry = ce_buy_entry = pe_buy_entry = 0.0
                ce_sell_exit = pe_sell_exit = ce_buy_exit = pe_buy_exit = 0.0
                ce_sell_pnl = pe_sell_pnl = ce_buy_pnl = pe_buy_pnl = 0.0
                
                # Parse strikes
                ce_sell_strike = trade.strikes.get('CE_SELL', trade.strikes.get('CE', 'N/A'))
                pe_sell_strike = trade.strikes.get('PE_SELL', trade.strikes.get('PE', 'N/A'))
                ce_buy_strike = trade.strikes.get('CE_BUY', 'N/A')
                pe_buy_strike = trade.strikes.get('PE_BUY', 'N/A')
                
                # Parse all entry/exit prices and calculate P&L
                for key, entry_price in trade.entry_prices.items():
                    exit_price = trade.exit_prices.get(key, 0)
                    parts = key.split('_')
                    
                    if len(parts) >= 3:  # Hedged format: CE_580.0_SELL
                        option_type, strike, position_type = parts[0], parts[1], parts[2]
                        pnl = 0
                        
                        if position_type == "SELL":
                            pnl = (entry_price - exit_price) * trade.quantity * 100
                        else:  # BUY
                            pnl = (exit_price - entry_price) * trade.quantity * 100
                        
                        if option_type == "CE" and position_type == "SELL":
                            ce_sell_entry, ce_sell_exit, ce_sell_pnl = entry_price, exit_price, pnl
                        elif option_type == "PE" and position_type == "SELL":
                            pe_sell_entry, pe_sell_exit, pe_sell_pnl = entry_price, exit_price, pnl
                        elif option_type == "CE" and position_type == "BUY":
                            ce_buy_entry, ce_buy_exit, ce_buy_pnl = entry_price, exit_price, pnl
                        elif option_type == "PE" and position_type == "BUY":
                            pe_buy_entry, pe_buy_exit, pe_buy_pnl = entry_price, exit_price, pnl
                    
                    elif len(parts) == 2:  # Simple format: CE_580.0
                        option_type, strike = parts[0], parts[1]
                        pnl = (entry_price - exit_price) * trade.quantity * 100  # Assume SELL
                        
                        if option_type == "CE":
                            ce_sell_entry, ce_sell_exit, ce_sell_pnl = entry_price, exit_price, pnl
                        elif option_type == "PE":
                            pe_sell_entry, pe_sell_exit, pe_sell_pnl = entry_price, exit_price, pnl
                
                writer.writerow({
                    'trade_id': i,
                    'setup_id': trade.setup_id,
                    'date': trade.date,
                    'entry_time': trade.entry_timeindex,
                    'exit_time': trade.exit_timeindex,
                    'duration': trade.exit_timeindex - trade.entry_timeindex,
                    'exit_reason': trade.exit_reason,
                    'ce_sell_strike': ce_sell_strike,
                    'pe_sell_strike': pe_sell_strike,
                    'ce_sell_entry': f"{ce_sell_entry:.3f}",
                    'pe_sell_entry': f"{pe_sell_entry:.3f}",
                    'ce_sell_exit': f"{ce_sell_exit:.3f}",
                    'pe_sell_exit': f"{pe_sell_exit:.3f}",
                    'ce_sell_pnl': f"{ce_sell_pnl:.2f}",
                    'pe_sell_pnl': f"{pe_sell_pnl:.2f}",
                    'ce_hedge_strike': ce_buy_strike,
                    'pe_hedge_strike': pe_buy_strike,
                    'ce_hedge_buy_entry': f"{ce_buy_entry:.3f}",
                    'pe_hedge_buy_entry': f"{pe_buy_entry:.3f}",
                    'ce_hedge_buy_exit': f"{ce_buy_exit:.3f}",
                    'pe_hedge_buy_exit': f"{pe_buy_exit:.3f}",
                    'ce_hedge_pnl': f"{ce_buy_pnl:.2f}",
                    'pe_hedge_pnl': f"{pe_buy_pnl:.2f}",
                    'total_pnl': f"{trade.pnl:.2f}",
                    'quantity': trade.quantity
                })
    
    def _export_daily_results_csv(self, filename: str):
        """Export daily results to CSV"""
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['date', 'daily_pnl', 'trades_count', 'positions_forced_closed']
            
            # Add setup-specific P&L columns
            if self.results.daily_results:
                setup_ids = list(self.results.daily_results[0].setup_pnls.keys())
                for setup_id in setup_ids:
                    fieldnames.append(f'{setup_id}_pnl')
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for daily in self.results.daily_results:
                row = {
                    'date': daily.date,
                    'daily_pnl': f"{daily.daily_pnl:.2f}",
                    'trades_count': daily.trades_count,
                    'positions_forced_closed': daily.positions_forced_closed_at_job_end
                }
                
                # Add setup-specific P&L
                for setup_id, pnl in daily.setup_pnls.items():
                    row[f'{setup_id}_pnl'] = f"{pnl:.2f}"
                
                writer.writerow(row)
    
    def _export_setup_performance_csv(self, filename: str):
        """Export setup performance to CSV"""
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'setup_id', 'total_pnl', 'total_trades', 'win_rate', 
                'avg_win', 'avg_loss', 'max_drawdown'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for setup_id, perf in self.results.setup_performance.items():
                writer.writerow({
                    'setup_id': setup_id,
                    'total_pnl': f"{perf.total_pnl:.2f}",
                    'total_trades': perf.total_trades,
                    'win_rate': f"{perf.win_rate:.3f}",
                    'avg_win': f"{perf.avg_win:.2f}",
                    'avg_loss': f"{perf.avg_loss:.2f}",
                    'max_drawdown': f"{perf.max_drawdown:.2f}"
                })
    
    def print_quick_summary(self):
        """Print a quick summary to console"""
        print(f"\n🎯 Quick Summary:")
        print(f"   Total P&L: ${self.results.total_pnl:.2f}")
        print(f"   Trades: {self.results.total_trades}")
        print(f"   Win Rate: {self.results.win_rate:.1%}")
        print(f"   Max DD: ${self.results.max_drawdown:.2f}")
    
    def print_recent_trades(self, num_trades: int = 5):
        """Print recent trades summary"""
        recent_trades = self.results.trade_log[-num_trades:]
        
        print(f"\n📋 Last {len(recent_trades)} Trades:")
        print(f"{'ID':<4} {'Setup':<12} {'Entry':<6} {'Exit':<6} {'Reason':<10} {'P&L':<8}")
        print("-" * 50)
        
        start_idx = max(1, len(self.results.trade_log) - num_trades + 1)
        for i, trade in enumerate(recent_trades, start_idx):
            print(f"{i:<4} {trade.setup_id:<12} {trade.entry_timeindex:<6} {trade.exit_timeindex:<6} "
                  f"{trade.exit_reason:<10} ${trade.pnl:>6.2f}")
    
    def print_regime_performance(self):
        """Print regime-specific performance analysis"""
        if not self.results.regime_performance:
            print("\n⚠️  No regime performance data available")
            return
        
        print(f"\n🌊 Regime Performance Analysis:")
        print(f"{'Regime':<15} {'P&L':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Duration':<12}")
        print("-" * 55)
        
        for regime, perf in self.results.regime_performance.items():
            print(f"{regime:<15} ${perf.total_pnl:>8.2f} {perf.total_trades:>6} "
                  f"{perf.win_rate:>8.1%} {perf.avg_duration:>10.1f}")
    
    def _export_regime_analysis_csv(self, filename: str):
        """Export regime-specific performance analysis to CSV"""
        if not self.results.regime_performance:
            return
        
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'regime', 'total_pnl', 'total_trades', 'win_rate', 
                'avg_duration', 'transition_performance'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for regime, perf in self.results.regime_performance.items():
                writer.writerow({
                    'regime': regime,
                    'total_pnl': f"{perf.total_pnl:.2f}",
                    'total_trades': perf.total_trades,
                    'win_rate': f"{perf.win_rate:.3f}",
                    'avg_duration': f"{perf.avg_duration:.2f}",
                    'transition_performance': f"{perf.transition_performance:.2f}"
                })
    
    def _export_dynamic_adjustments_csv(self, filename: str):
        """Export dynamic parameter adjustments to CSV"""
        if not self.results.dynamic_adjustment_performance:
            return
        
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'adjustment_type', 'avg_pnl_impact', 'total_adjustments',
                'static_vs_dynamic_comparison', 'regime_accuracy'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            adj_perf = self.results.dynamic_adjustment_performance
            
            # Write summary row
            writer.writerow({
                'adjustment_type': 'SUMMARY',
                'avg_pnl_impact': 'N/A',
                'total_adjustments': adj_perf.total_adjustments,
                'static_vs_dynamic_comparison': f"{adj_perf.static_vs_dynamic_comparison:.2f}",
                'regime_accuracy': f"{adj_perf.regime_accuracy:.3f}"
            })
            
            # Write individual adjustment performance
            for adj_type, avg_impact in adj_perf.adjustment_performance.items():
                writer.writerow({
                    'adjustment_type': adj_type,
                    'avg_pnl_impact': f"{avg_impact:.2f}",
                    'total_adjustments': 'N/A',
                    'static_vs_dynamic_comparison': 'N/A',
                    'regime_accuracy': 'N/A'
                })
    
    def _export_symbol_performance_csv(self, filename: str):
        """Export multi-symbol performance analysis to CSV"""
        if not self.results.symbol_performance:
            return
        
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            # Get all symbols for correlation columns
            all_symbols = list(self.results.symbol_performance.keys())
            
            fieldnames = ['symbol', 'total_pnl', 'total_trades', 'win_rate']
            # Add correlation columns
            for symbol in all_symbols:
                fieldnames.append(f'correlation_with_{symbol}')
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for symbol, perf in self.results.symbol_performance.items():
                row = {
                    'symbol': symbol,
                    'total_pnl': f"{perf.total_pnl:.2f}",
                    'total_trades': perf.total_trades,
                    'win_rate': f"{perf.win_rate:.3f}"
                }
                
                # Add correlation data
                for other_symbol in all_symbols:
                    corr_key = f'correlation_with_{other_symbol}'
                    correlation = perf.correlation_with_other_symbols.get(other_symbol, 0.0)
                    row[corr_key] = f"{correlation:.3f}"
                
                writer.writerow(row)
    
    def _export_pattern_analysis_csv(self, filename: str):
        """Export pattern discovery analysis to CSV"""
        filepath = os.path.join(self.report_dir, filename)
        
        # Analyze patterns in the trade data
        patterns = self._discover_trading_patterns()
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'pattern_type', 'pattern_description', 'occurrences', 
                'avg_pnl', 'win_rate', 'confidence_score'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pattern in patterns:
                writer.writerow({
                    'pattern_type': pattern['type'],
                    'pattern_description': pattern['description'],
                    'occurrences': pattern['occurrences'],
                    'avg_pnl': f"{pattern['avg_pnl']:.2f}",
                    'win_rate': f"{pattern['win_rate']:.3f}",
                    'confidence_score': f"{pattern['confidence']:.3f}"
                })
    
    def _export_correlation_analysis_csv(self, filename: str):
        """Export cross-symbol correlation analysis to CSV"""
        filepath = os.path.join(self.report_dir, filename)
        
        # Calculate correlations between symbols
        correlations = self._calculate_cross_symbol_correlations()
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['symbol_1', 'symbol_2', 'price_correlation', 'pnl_correlation', 'trade_timing_correlation']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for correlation in correlations:
                writer.writerow({
                    'symbol_1': correlation['symbol_1'],
                    'symbol_2': correlation['symbol_2'],
                    'price_correlation': f"{correlation['price_correlation']:.3f}",
                    'pnl_correlation': f"{correlation['pnl_correlation']:.3f}",
                    'trade_timing_correlation': f"{correlation['trade_timing_correlation']:.3f}"
                })
    
    def _discover_trading_patterns(self) -> List[Dict]:
        """
        Discover recurring patterns in trading data
        
        Returns:
            List of discovered patterns with statistics
        """
        patterns = []
        
        if not self.results.trade_log:
            return patterns
        
        # Pattern 1: Time-of-day performance
        time_patterns = self._analyze_time_of_day_patterns()
        patterns.extend(time_patterns)
        
        # Pattern 2: Exit reason clustering
        exit_reason_patterns = self._analyze_exit_reason_patterns()
        patterns.extend(exit_reason_patterns)
        
        # Pattern 3: Setup performance streaks
        streak_patterns = self._analyze_performance_streaks()
        patterns.extend(streak_patterns)
        
        # Pattern 4: Duration-based patterns
        duration_patterns = self._analyze_duration_patterns()
        patterns.extend(duration_patterns)
        
        return patterns
    
    def _analyze_time_of_day_patterns(self) -> List[Dict]:
        """Analyze time-of-day trading patterns"""
        patterns = []
        
        # Group trades by hour of day (assuming timeindex represents time)
        hourly_performance = defaultdict(list)
        
        for trade in self.results.trade_log:
            # Convert timeindex to approximate hour (simplified)
            hour = (trade.entry_timeindex // 300) % 24  # Rough approximation
            hourly_performance[hour].append(trade.pnl)
        
        # Find significant time patterns
        for hour, pnls in hourly_performance.items():
            if len(pnls) >= 5:  # Minimum sample size
                avg_pnl = sum(pnls) / len(pnls)
                win_rate = len([p for p in pnls if p > 0]) / len(pnls)
                
                # Consider it a pattern if significantly different from average
                overall_avg = self.results.total_pnl / self.results.total_trades if self.results.total_trades > 0 else 0
                
                if abs(avg_pnl - overall_avg) > abs(overall_avg) * 0.2:  # 20% difference threshold
                    patterns.append({
                        'type': 'TIME_OF_DAY',
                        'description': f'Hour {hour}: {"Strong" if avg_pnl > overall_avg else "Weak"} performance',
                        'occurrences': len(pnls),
                        'avg_pnl': avg_pnl,
                        'win_rate': win_rate,
                        'confidence': min(0.9, len(pnls) / 20.0)  # Confidence based on sample size
                    })
        
        return patterns
    
    def _analyze_exit_reason_patterns(self) -> List[Dict]:
        """Analyze exit reason patterns"""
        patterns = []
        
        # Group by exit reason
        exit_performance = defaultdict(list)
        
        for trade in self.results.trade_log:
            exit_performance[trade.exit_reason].append(trade.pnl)
        
        for reason, pnls in exit_performance.items():
            if len(pnls) >= 3:  # Minimum sample size
                avg_pnl = sum(pnls) / len(pnls)
                win_rate = len([p for p in pnls if p > 0]) / len(pnls)
                
                patterns.append({
                    'type': 'EXIT_REASON',
                    'description': f'{reason} exits: Avg P&L ${avg_pnl:.2f}',
                    'occurrences': len(pnls),
                    'avg_pnl': avg_pnl,
                    'win_rate': win_rate,
                    'confidence': min(0.8, len(pnls) / 10.0)
                })
        
        return patterns
    
    def _analyze_performance_streaks(self) -> List[Dict]:
        """Analyze winning/losing streaks"""
        patterns = []
        
        if len(self.results.trade_log) < 5:
            return patterns
        
        # Find streaks
        current_streak = 0
        current_streak_type = None
        max_win_streak = 0
        max_loss_streak = 0
        
        for trade in self.results.trade_log:
            if trade.pnl > 0:  # Winning trade
                if current_streak_type == 'WIN':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_streak_type = 'WIN'
                max_win_streak = max(max_win_streak, current_streak)
            else:  # Losing trade
                if current_streak_type == 'LOSS':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_streak_type = 'LOSS'
                max_loss_streak = max(max_loss_streak, current_streak)
        
        if max_win_streak >= 3:
            patterns.append({
                'type': 'WINNING_STREAK',
                'description': f'Maximum winning streak: {max_win_streak} trades',
                'occurrences': max_win_streak,
                'avg_pnl': 0.0,  # Not applicable for streaks
                'win_rate': 1.0,
                'confidence': min(0.7, max_win_streak / 10.0)
            })
        
        if max_loss_streak >= 3:
            patterns.append({
                'type': 'LOSING_STREAK',
                'description': f'Maximum losing streak: {max_loss_streak} trades',
                'occurrences': max_loss_streak,
                'avg_pnl': 0.0,  # Not applicable for streaks
                'win_rate': 0.0,
                'confidence': min(0.7, max_loss_streak / 10.0)
            })
        
        return patterns
    
    def _analyze_duration_patterns(self) -> List[Dict]:
        """Analyze trade duration patterns"""
        patterns = []
        
        # Group trades by duration buckets
        duration_buckets = {
            'VERY_SHORT': (0, 60),      # 0-5 minutes
            'SHORT': (60, 300),         # 5-25 minutes  
            'MEDIUM': (300, 900),       # 25-75 minutes
            'LONG': (900, 1800),        # 75-150 minutes
            'VERY_LONG': (1800, float('inf'))  # 150+ minutes
        }
        
        bucket_performance = defaultdict(list)
        
        for trade in self.results.trade_log:
            duration = trade.exit_timeindex - trade.entry_timeindex
            
            for bucket_name, (min_dur, max_dur) in duration_buckets.items():
                if min_dur <= duration < max_dur:
                    bucket_performance[bucket_name].append(trade.pnl)
                    break
        
        for bucket, pnls in bucket_performance.items():
            if len(pnls) >= 3:
                avg_pnl = sum(pnls) / len(pnls)
                win_rate = len([p for p in pnls if p > 0]) / len(pnls)
                
                patterns.append({
                    'type': 'DURATION',
                    'description': f'{bucket} duration trades: Avg P&L ${avg_pnl:.2f}',
                    'occurrences': len(pnls),
                    'avg_pnl': avg_pnl,
                    'win_rate': win_rate,
                    'confidence': min(0.8, len(pnls) / 15.0)
                })
        
        return patterns
    
    def _calculate_cross_symbol_correlations(self) -> List[Dict]:
        """Calculate correlations between different symbols"""
        correlations = []
        
        if not self.results.symbol_performance or len(self.results.symbol_performance) < 2:
            return correlations
        
        symbols = list(self.results.symbol_performance.keys())
        
        # Calculate pairwise correlations
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols[i+1:], i+1):
                
                # Get trades for each symbol
                symbol1_trades = [t for t in self.results.trade_log if getattr(t, 'symbol', '') == symbol1]
                symbol2_trades = [t for t in self.results.trade_log if getattr(t, 'symbol', '') == symbol2]
                
                if len(symbol1_trades) < 3 or len(symbol2_trades) < 3:
                    continue
                
                # Calculate P&L correlation (simplified)
                symbol1_pnls = [t.pnl for t in symbol1_trades]
                symbol2_pnls = [t.pnl for t in symbol2_trades]
                
                pnl_correlation = self._calculate_correlation(symbol1_pnls, symbol2_pnls)
                
                # Calculate timing correlation (how often trades happen at similar times)
                symbol1_times = [t.entry_timeindex for t in symbol1_trades]
                symbol2_times = [t.entry_timeindex for t in symbol2_trades]
                
                timing_correlation = self._calculate_timing_correlation(symbol1_times, symbol2_times)
                
                correlations.append({
                    'symbol_1': symbol1,
                    'symbol_2': symbol2,
                    'price_correlation': 0.0,  # Would need price data to calculate
                    'pnl_correlation': pnl_correlation,
                    'trade_timing_correlation': timing_correlation
                })
        
        return correlations
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = min(len(x), len(y))
        x = x[:n]
        y = y[:n]
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_timing_correlation(self, times1: List[int], times2: List[int]) -> float:
        """Calculate how correlated trade timing is between symbols"""
        if not times1 or not times2:
            return 0.0
        
        # Create time buckets (e.g., 5-minute intervals)
        bucket_size = 300  # 5 minutes in timeindex units
        
        # Count trades in each bucket for each symbol
        max_time = max(max(times1), max(times2))
        min_time = min(min(times1), min(times2))
        
        buckets1 = defaultdict(int)
        buckets2 = defaultdict(int)
        
        for time in times1:
            bucket = (time - min_time) // bucket_size
            buckets1[bucket] += 1
        
        for time in times2:
            bucket = (time - min_time) // bucket_size
            buckets2[bucket] += 1
        
        # Create aligned arrays for correlation calculation
        all_buckets = set(buckets1.keys()) | set(buckets2.keys())
        
        if len(all_buckets) < 2:
            return 0.0
        
        counts1 = [buckets1.get(bucket, 0) for bucket in sorted(all_buckets)]
        counts2 = [buckets2.get(bucket, 0) for bucket in sorted(all_buckets)]
        
        return self._calculate_correlation(counts1, counts2)