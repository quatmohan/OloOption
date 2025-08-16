"""
Example usage of CE/PE scalping strategies with re-entry
"""

import os
import shutil
from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import CEScalpingSetup, PEScalpingSetup
from backtesting_engine.reporting import BacktestReporter


def clear_reports_directory():
    """Clear the backtest_reports directory before running new backtest"""
    reports_dir = "backtest_reports"
    if os.path.exists(reports_dir):
        shutil.rmtree(reports_dir)
        print(f"🗑️  Cleared {reports_dir} directory")
    os.makedirs(reports_dir, exist_ok=True)


def main():
    # Clear previous reports
    clear_reports_directory()
    
    # Setup 1: CE Scalping with re-entry
    ce_scalping = CEScalpingSetup(
        setup_id="ce_scalping",
        target_pct=25.0,  # Target profit of $25
        stop_loss_pct=50.0,  # Stop loss at $50
        entry_timeindex=1000,  # Initial entry at timeindex 1000
        close_timeindex=4500,  # Close at timeindex 4500
        strike_selection="premium",  # Use premium-based selection
        scalping_price=0.30,  # Minimum premium of 0.30
        max_reentries=3,  # Allow up to 3 re-entries
        reentry_gap=500  # Wait 500 timeindex between entries
    )
    
    # Setup 2: PE Scalping with re-entry
    pe_scalping = PEScalpingSetup(
        setup_id="pe_scalping",
        target_pct=30.0,  # Target profit of $30
        stop_loss_pct=60.0,  # Stop loss at $60
        entry_timeindex=1200,  # Initial entry at timeindex 1200
        close_timeindex=4400,  # Close at timeindex 4400
        strike_selection="distance",  # Use distance-based selection
        strikes_away=1,  # 1 strike away from spot
        max_reentries=2,  # Allow up to 2 re-entries
        reentry_gap=600  # Wait 600 timeindex between entries
    )
    
    # Setup 3: CE Scalping with different parameters
    ce_scalping_2 = CEScalpingSetup(
        setup_id="ce_scalping_aggressive",
        target_pct=20.0,  # Lower target for quicker exits
        stop_loss_pct=40.0,  # Tighter stop loss
        entry_timeindex=1500,  # Later entry
        close_timeindex=4300,
        strike_selection="premium",
        scalping_price=0.25,  # Lower premium requirement
        max_reentries=4,  # More re-entries allowed
        reentry_gap=300  # Shorter gap between entries
    )
    
    # Setup 4: PE Scalping Aggressive
    pe_scalping_2 = PEScalpingSetup(
        setup_id="pe_scalping_aggressive",
        target_pct=18.0,  # Lower target for quicker exits
        stop_loss_pct=35.0,  # Tighter stop loss
        entry_timeindex=1400,  # Entry time
        close_timeindex=4200,
        strike_selection="premium",
        scalping_price=0.25,  # Lower premium requirement
        max_reentries=4,  # More re-entries allowed
        reentry_gap=350  # Shorter gap between entries
    )
    
    # Create backtest engine
    engine = BacktestEngine(
        data_path="5SecData",
        setups=[ce_scalping, pe_scalping, ce_scalping_2, pe_scalping_2],
        daily_max_loss=400.0  # Daily max loss of $400 for 4 setups
    )
    
    # Run backtest
    symbol = "QQQ"
    start_date = "2025-08-13"
    end_date = "2025-08-15"
    
    results = engine.run_backtest(symbol, start_date, end_date)
    
    # Generate comprehensive reports
    reporter = BacktestReporter(results)
    
    # Print summary to console
    summary = reporter.generate_full_report(symbol, start_date, end_date)
    print(summary)
    
    # Print quick summary and recent trades
    reporter.print_quick_summary()
    reporter.print_recent_trades(num_trades=20)


if __name__ == "__main__":
    main()