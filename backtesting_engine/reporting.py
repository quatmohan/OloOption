"""
Advanced reporting and analytics for backtesting results
"""

import csv
import os
from datetime import datetime
from typing import Dict, List
from .models import BacktestResults, Trade, DailyResults, SetupResults


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
    
    def generate_full_report(self, symbol: str, start_date: str, end_date: str) -> str:
        """Generate comprehensive report and save to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_prefix = f"{symbol}_{start_date}_to_{end_date}_{timestamp}"
        
        # Generate console summary
        summary = self._generate_summary_report(symbol, start_date, end_date)
        
        # Export detailed data to CSV files
        self._export_trades_csv(f"{report_prefix}_trades.csv")
        self._export_daily_results_csv(f"{report_prefix}_daily.csv")
        self._export_setup_performance_csv(f"{report_prefix}_setups.csv")
        
        # Save summary to text file
        summary_file = os.path.join(self.report_dir, f"{report_prefix}_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"\n📊 Reports saved to {self.report_dir}/ directory:")
        print(f"   - {report_prefix}_summary.txt")
        print(f"   - {report_prefix}_trades.csv")
        print(f"   - {report_prefix}_daily.csv")
        print(f"   - {report_prefix}_setups.csv")
        
        return summary
    
    def _generate_summary_report(self, symbol: str, start_date: str, end_date: str) -> str:
        """Generate formatted summary report"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"OPTIONS BACKTESTING REPORT - {symbol}")
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