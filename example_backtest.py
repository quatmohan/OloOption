"""
Example usage of the options backtesting engine
"""

from backtesting_engine.backtest_engine import BacktestEngine
from backtesting_engine.strategies import StraddleSetup


def main():
    # Create trading setups
    setup1 = StraddleSetup(
        setup_id="straddle_1",
        target_pct=50.0,  # Target profit of $50
        stop_loss_pct=100.0,  # Stop loss at $100
        entry_timeindex=1000,  # Enter at timeindex 1000
        close_timeindex=4200,  # Close at timeindex 4200 (around 3:30 PM)
        strike_selection="premium",  # Use premium-based selection
        scalping_price=0.40  # Minimum premium of 0.40
    )
    
    setup2 = StraddleSetup(
        setup_id="straddle_2", 
        target_pct=75.0,  # Target profit of $75
        stop_loss_pct=150.0,  # Stop loss at $150
        entry_timeindex=2000,  # Enter at timeindex 2000
        close_timeindex=4650,  # Close near end of day
        strike_selection="distance",  # Use distance-based selection
        strikes_away=2  # 2 strikes away from spot
    )
    
    # Create backtest engine
    engine = BacktestEngine(
        data_path="5SecData",
        setups=[setup1, setup2],
        daily_max_loss=500.0  # Daily max loss of $500
    )
    
    # Run backtest
    results = engine.run_backtest(
        symbol="QQQ",
        start_date="2025-08-13",
        end_date="2025-08-15"
    )
    
    # Print results
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Total P&L: ${results.total_pnl:.2f}")
    print(f"Total Trades: {results.total_trades}")
    print(f"Win Rate: {results.win_rate:.1%}")
    print(f"Max Drawdown: ${results.max_drawdown:.2f}")
    
    print(f"\nDaily Results:")
    for daily in results.daily_results:
        print(f"  {daily.date}: P&L=${daily.daily_pnl:.2f}, Trades={daily.trades_count}")
    
    print(f"\nSetup Performance:")
    for setup_id, perf in results.setup_performance.items():
        print(f"  {setup_id}:")
        print(f"    P&L: ${perf.total_pnl:.2f}")
        print(f"    Trades: {perf.total_trades}")
        print(f"    Win Rate: {perf.win_rate:.1%}")
        if perf.avg_win > 0:
            print(f"    Avg Win: ${perf.avg_win:.2f}")
        if perf.avg_loss < 0:
            print(f"    Avg Loss: ${perf.avg_loss:.2f}")
    
    print(f"\nDetailed Trade Log:")
    for i, trade in enumerate(results.trade_log, 1):
        print(f"\nTrade {i} - {trade.setup_id}:")
        print(f"  Entry Time: {trade.entry_timeindex}, Exit Time: {trade.exit_timeindex}")
        print(f"  Exit Reason: {trade.exit_reason}")
        print(f"  Strikes: {trade.strikes}")
        print(f"  Entry Prices: {trade.entry_prices}")
        print(f"  Exit Prices: {trade.exit_prices}")
        print(f"  P&L: ${trade.pnl:.2f}")
        
        # Show individual option P&L breakdown
        for option_key in trade.entry_prices:
            entry_price = trade.entry_prices[option_key]
            exit_price = trade.exit_prices[option_key]
            option_pnl = (entry_price - exit_price) * trade.quantity * 100  # Assuming SELL positions
            print(f"    {option_key}: Entry=${entry_price:.3f}, Exit=${exit_price:.3f}, P&L=${option_pnl:.2f}")


if __name__ == "__main__":
    main()