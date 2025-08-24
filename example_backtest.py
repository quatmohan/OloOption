"""
Example usage of the options backtesting engine
"""

from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup, HedgedStraddleSetup
from backtesting_engine.reporting import BacktestReporter


def main():
    # Create trading setups
    setup1 = StraddleSetup(
        setup_id="straddle_1",
        target_pct=50.0,  # Target profit of $50
        stop_loss_pct=100.0,  # Stop loss at $100
        entry_timeindex=100,  # Enter at timeindex 1000
        close_timeindex=4200,  # Close at timeindex 4200 (around 3:30 PM)
        strike_selection="premium",  # Use premium-based selection
        scalping_price=0.40  # Minimum premium of 0.40
    )
    
    setup2 = StraddleSetup(
        setup_id="straddle_2", 
        target_pct=75.0,  # Target profit of $75
        stop_loss_pct=150.0,  # Stop loss at $150
        entry_timeindex=200,  # Enter at timeindex 2000
        close_timeindex=4650,  # Close near end of day
        strike_selection="distance",  # Use distance-based selection
        strikes_away=2  # 2 strikes away from spot
    )
    
    # Setup 3: Hedged straddle with premium-based selection
    setup3 = HedgedStraddleSetup(
        setup_id="hedged_straddle_1",
        target_pct=40.0,  # Lower target due to hedge cost
        stop_loss_pct=80.0,  # Lower stop loss due to hedge protection
        entry_timeindex=100,  # Enter at timeindex 1500
        close_timeindex=4400,  # Close at timeindex 4400
        strike_selection="premium",  # Use premium-based selection
        scalping_price=0.35,  # Slightly lower premium requirement
        hedge_strikes_away=5  # Hedge 5 strikes away
    )
    
    # Setup 4: Hedged straddle with distance-based selection
    setup4 = HedgedStraddleSetup(
        setup_id="hedged_straddle_2",
        target_pct=60.0,  # Target profit of $60
        stop_loss_pct=120.0,  # Stop loss at $120
        entry_timeindex=200,  # Enter at timeindex 2500
        close_timeindex=4600,  # Close near end of day
        strike_selection="distance",  # Use distance-based selection
        strikes_away=3,  # 3 strikes away from spot
        hedge_strikes_away=6  # Hedge 6 strikes away
    )
    
    # Create backtest engine
    engine = BacktestEngine(
        data_path="5SecData",
        setups=[setup1, setup2, setup3, setup4],
        daily_max_loss=800.0  # Increased daily max loss for 4 setups
    )
    
    # Run backtest
    symbol = "QQQ"
    start_date = "2025-08-13"
    end_date = "2025-08-22"
    
    results = engine.run_backtest(symbol, start_date, end_date)
    
    # Generate comprehensive reports
    reporter = BacktestReporter(results)
    
    # Print summary to console
    summary = reporter.generate_full_report(symbol, start_date, end_date)
    print(summary)
    
    # Print quick summary and recent trades
    reporter.print_quick_summary()
    reporter.print_recent_trades(num_trades=10)


if __name__ == "__main__":
    main()