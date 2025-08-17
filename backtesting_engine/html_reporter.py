"""
HTML report generator for backtesting results
"""

import os
from datetime import datetime
from typing import Dict, List
from .models import BacktestResults, Trade, DailyResults, SetupResults


class HTMLReporter:
    """Generate comprehensive HTML reports for backtest results"""
    
    def __init__(self, results: BacktestResults):
        self.results = results
        self.report_dir = "backtest_reports"
    
    def generate_html_report(self, symbol: str, start_date: str, end_date: str) -> str:
        """Generate comprehensive HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"{symbol}_{start_date}_to_{end_date}_{timestamp}_report.html"
        html_filepath = os.path.join(self.report_dir, html_filename)
        
        html_content = self._generate_html_content(symbol, start_date, end_date)
        
        with open(html_filepath, 'w') as f:
            f.write(html_content)
        
        print(f"📊 HTML Report generated: {html_filename}")
        return html_filepath
    
    def _generate_html_content(self, symbol: str, start_date: str, end_date: str) -> str:
        """Generate the complete HTML content"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Options Backtesting Report - {symbol}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {self._generate_header(symbol, start_date, end_date)}
        {self._generate_summary_section()}
        {self._generate_daily_performance_section()}
        {self._generate_setup_performance_section()}
        {self._generate_trades_table()}
        {self._generate_charts_section()}
        {self._generate_statistics_section()}
    </div>
    
    <script>
        {self._generate_javascript()}
    </script>
</body>
</html>
"""
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .section-header h2 {
            color: #495057;
            font-size: 1.5em;
        }
        
        .section-content {
            padding: 20px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        
        .metric-label {
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .positive {
            color: #28a745 !important;
            border-left-color: #28a745 !important;
        }
        
        .negative {
            color: #dc3545 !important;
            border-left-color: #dc3545 !important;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        th, td {
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        td:nth-child(7) {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.4;
        }
        
        .profit {
            color: #28a745;
            font-weight: bold;
        }
        
        .loss {
            color: #dc3545;
            font-weight: bold;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid #dee2e6;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            border-bottom-color: #007bff;
            color: #007bff;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .badge-success {
            background-color: #d4edda;
            color: #155724;
        }
        
        .badge-danger {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .badge-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .badge-info {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        """
    
    def _generate_header(self, symbol: str, start_date: str, end_date: str) -> str:
        """Generate the header section"""
        return f"""
        <div class="header">
            <h1>📊 Options Backtesting Report</h1>
            <p>{symbol} • {start_date} to {end_date} • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
    
    def _generate_summary_section(self) -> str:
        """Generate the summary metrics section"""
        total_pnl_class = "positive" if self.results.total_pnl >= 0 else "negative"
        win_rate_class = "positive" if self.results.win_rate >= 0.6 else "negative"
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>📈 Overall Performance</h2>
            </div>
            <div class="section-content">
                <div class="metrics-grid">
                    <div class="metric-card {total_pnl_class}">
                        <div class="metric-value">${self.results.total_pnl:,.2f}</div>
                        <div class="metric-label">Total P&L</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{self.results.total_trades:,}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric-card {win_rate_class}">
                        <div class="metric-value">{self.results.win_rate:.1%}</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card negative">
                        <div class="metric-value">${self.results.max_drawdown:,.2f}</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${self.results.total_pnl/self.results.total_trades if self.results.total_trades > 0 else 0:,.2f}</div>
                        <div class="metric-label">Avg Trade</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(self.results.daily_results)}</div>
                        <div class="metric-label">Trading Days</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_daily_performance_section(self) -> str:
        """Generate the daily performance section"""
        daily_rows = ""
        for daily in self.results.daily_results:
            pnl_class = "profit" if daily.daily_pnl >= 0 else "loss"
            daily_rows += f"""
            <tr>
                <td>{daily.date}</td>
                <td class="{pnl_class}">${daily.daily_pnl:,.2f}</td>
                <td>{daily.trades_count}</td>
                <td>{daily.positions_forced_closed_at_job_end}</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>📅 Daily Performance</h2>
            </div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>P&L</th>
                            <th>Trades</th>
                            <th>Forced Closes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {daily_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _generate_setup_performance_section(self) -> str:
        """Generate the setup performance section"""
        setup_rows = ""
        for setup_id, perf in self.results.setup_performance.items():
            pnl_class = "profit" if perf.total_pnl >= 0 else "loss"
            win_rate_class = "profit" if perf.win_rate >= 0.6 else "loss"
            
            setup_rows += f"""
            <tr>
                <td><strong>{setup_id}</strong></td>
                <td class="{pnl_class}">${perf.total_pnl:,.2f}</td>
                <td>{perf.total_trades}</td>
                <td class="{win_rate_class}">{perf.win_rate:.1%}</td>
                <td class="profit">${perf.avg_win:,.2f}</td>
                <td class="loss">${perf.avg_loss:,.2f}</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>🎯 Setup Performance</h2>
            </div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Setup ID</th>
                            <th>Total P&L</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>Avg Win</th>
                            <th>Avg Loss</th>
                        </tr>
                    </thead>
                    <tbody>
                        {setup_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _generate_trades_table(self) -> str:
        """Generate the detailed trades table"""
        trade_rows = ""
        for i, trade in enumerate(self.results.trade_log, 1):
            pnl_class = "profit" if trade.pnl >= 0 else "loss"
            
            # Get exit reason badge
            reason_badge = self._get_exit_reason_badge(trade.exit_reason)
            
            # Parse strikes and prices for display
            ce_strike = trade.strikes.get('CE_SELL', trade.strikes.get('CE', 'N/A'))
            pe_strike = trade.strikes.get('PE_SELL', trade.strikes.get('PE', 'N/A'))
            ce_hedge = trade.strikes.get('CE_BUY', 'N/A')
            pe_hedge = trade.strikes.get('PE_BUY', 'N/A')
            
            # Get entry and exit prices
            ce_entry_price = ce_exit_price = pe_entry_price = pe_exit_price = 0.0
            ce_hedge_entry = ce_hedge_exit = pe_hedge_entry = pe_hedge_exit = 0.0
            
            # Parse prices from trade data
            for key, price in trade.entry_prices.items():
                if 'CE' in key and ('SELL' in key or len(key.split('_')) == 2):
                    ce_entry_price = price
                    ce_exit_price = trade.exit_prices.get(key, 0)
                elif 'PE' in key and ('SELL' in key or len(key.split('_')) == 2):
                    pe_entry_price = price
                    pe_exit_price = trade.exit_prices.get(key, 0)
                elif 'CE' in key and 'BUY' in key:
                    ce_hedge_entry = price
                    ce_hedge_exit = trade.exit_prices.get(key, 0)
                elif 'PE' in key and 'BUY' in key:
                    pe_hedge_entry = price
                    pe_hedge_exit = trade.exit_prices.get(key, 0)
            
            # Build main position info
            main_positions = []
            if ce_strike != 'N/A':
                main_positions.append(f"CE {ce_strike}: ${ce_entry_price:.3f}→${ce_exit_price:.3f}")
            if pe_strike != 'N/A':
                main_positions.append(f"PE {pe_strike}: ${pe_entry_price:.3f}→${pe_exit_price:.3f}")
            
            # Build hedge info
            hedge_positions = []
            if ce_hedge != 'N/A':
                hedge_positions.append(f"CE {ce_hedge}: ${ce_hedge_entry:.3f}→${ce_hedge_exit:.3f}")
            if pe_hedge != 'N/A':
                hedge_positions.append(f"PE {pe_hedge}: ${pe_hedge_entry:.3f}→${pe_hedge_exit:.3f}")
            
            positions_info = "<br>".join(main_positions)
            if hedge_positions:
                positions_info += f"<br><small style='color: #6c757d;'>Hedge: {', '.join(hedge_positions)}</small>"
            
            trade_rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{trade.setup_id}</strong></td>
                <td>{trade.date}</td>
                <td>{trade.entry_timeindex}</td>
                <td>{trade.exit_timeindex}</td>
                <td>{trade.exit_timeindex - trade.entry_timeindex}</td>
                <td>{positions_info}</td>
                <td class="{pnl_class}">${trade.pnl:,.2f}</td>
                <td>{reason_badge}</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>📋 Detailed Trades</h2>
            </div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Setup</th>
                            <th>Date</th>
                            <th>Entry Time</th>
                            <th>Exit Time</th>
                            <th>Duration</th>
                            <th>Positions (Entry→Exit)</th>
                            <th>P&L</th>
                            <th>Exit Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trade_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _get_exit_reason_badge(self, reason: str) -> str:
        """Get badge HTML for exit reason"""
        badge_map = {
            'TARGET': 'badge-success',
            'STOP_LOSS': 'badge-danger',
            'TIME_BASED': 'badge-warning',
            'JOB_END': 'badge-info',
            'DAILY_LIMIT': 'badge-danger'
        }
        badge_class = badge_map.get(reason, 'badge-info')
        return f'<span class="badge {badge_class}">{reason}</span>'
    
    def _generate_charts_section(self) -> str:
        """Generate the charts section"""
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>📊 Performance Charts</h2>
            </div>
            <div class="section-content">
                <div class="tabs">
                    <div class="tab active" onclick="showTab('equity-curve')">Equity Curve</div>
                    <div class="tab" onclick="showTab('daily-pnl')">Daily P&L</div>
                    <div class="tab" onclick="showTab('setup-comparison')">Setup Comparison</div>
                </div>
                
                <div id="equity-curve" class="tab-content active">
                    <div class="chart-container">
                        <canvas id="equityChart"></canvas>
                    </div>
                </div>
                
                <div id="daily-pnl" class="tab-content">
                    <div class="chart-container">
                        <canvas id="dailyChart"></canvas>
                    </div>
                </div>
                
                <div id="setup-comparison" class="tab-content">
                    <div class="chart-container">
                        <canvas id="setupChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_statistics_section(self) -> str:
        """Generate the statistics section"""
        winning_trades = [t for t in self.results.trade_log if t.pnl > 0]
        losing_trades = [t for t in self.results.trade_log if t.pnl < 0]
        
        # Exit reason analysis
        exit_reasons = {}
        for trade in self.results.trade_log:
            exit_reasons[trade.exit_reason] = exit_reasons.get(trade.exit_reason, 0) + 1
        
        reason_rows = ""
        for reason, count in sorted(exit_reasons.items()):
            pct = count / self.results.total_trades * 100 if self.results.total_trades > 0 else 0
            reason_rows += f"""
            <tr>
                <td>{self._get_exit_reason_badge(reason)}</td>
                <td>{count}</td>
                <td>{pct:.1f}%</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>📈 Trade Statistics</h2>
            </div>
            <div class="section-content">
                <div class="metrics-grid">
                    <div class="metric-card positive">
                        <div class="metric-value">{len(winning_trades)}</div>
                        <div class="metric-label">Winning Trades</div>
                    </div>
                    <div class="metric-card negative">
                        <div class="metric-value">{len(losing_trades)}</div>
                        <div class="metric-label">Losing Trades</div>
                    </div>
                    <div class="metric-card positive">
                        <div class="metric-value">${sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0:,.2f}</div>
                        <div class="metric-label">Avg Win</div>
                    </div>
                    <div class="metric-card negative">
                        <div class="metric-value">${sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0:,.2f}</div>
                        <div class="metric-label">Avg Loss</div>
                    </div>
                </div>
                
                <h3>Exit Reason Analysis</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Exit Reason</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reason_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for charts and interactivity"""
        # Prepare data for charts
        daily_dates = [d.date for d in self.results.daily_results]
        daily_pnls = [d.daily_pnl for d in self.results.daily_results]
        
        # Calculate cumulative P&L for equity curve
        cumulative_pnl = []
        running_total = 0
        for trade in self.results.trade_log:
            running_total += trade.pnl
            cumulative_pnl.append(running_total)
        
        setup_names = list(self.results.setup_performance.keys())
        setup_pnls = [self.results.setup_performance[name].total_pnl for name in setup_names]
        
        return f"""
        // Tab functionality
        function showTab(tabId) {{
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabId).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        // Chart data
        const dailyDates = {daily_dates};
        const dailyPnls = {daily_pnls};
        const cumulativePnl = {cumulative_pnl};
        const setupNames = {setup_names};
        const setupPnls = {setup_pnls};
        
        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeCharts();
        }});
        
        function initializeCharts() {{
            // Equity Curve Chart
            const equityCtx = document.getElementById('equityChart').getContext('2d');
            new Chart(equityCtx, {{
                type: 'line',
                data: {{
                    labels: Array.from({{length: cumulativePnl.length}}, (_, i) => i + 1),
                    datasets: [{{
                        label: 'Cumulative P&L',
                        data: cumulativePnl,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'P&L ($)'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Trade Number'
                            }}
                        }}
                    }}
                }}
            }});
            
            // Daily P&L Chart
            const dailyCtx = document.getElementById('dailyChart').getContext('2d');
            new Chart(dailyCtx, {{
                type: 'bar',
                data: {{
                    labels: dailyDates,
                    datasets: [{{
                        label: 'Daily P&L',
                        data: dailyPnls,
                        backgroundColor: dailyPnls.map(pnl => pnl >= 0 ? 'rgba(40, 167, 69, 0.8)' : 'rgba(220, 53, 69, 0.8)'),
                        borderColor: dailyPnls.map(pnl => pnl >= 0 ? 'rgb(40, 167, 69)' : 'rgb(220, 53, 69)'),
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'P&L ($)'
                            }}
                        }}
                    }}
                }}
            }});
            
            // Setup Comparison Chart
            const setupCtx = document.getElementById('setupChart').getContext('2d');
            new Chart(setupCtx, {{
                type: 'bar',
                data: {{
                    labels: setupNames,
                    datasets: [{{
                        label: 'Setup P&L',
                        data: setupPnls,
                        backgroundColor: setupPnls.map(pnl => pnl >= 0 ? 'rgba(40, 167, 69, 0.8)' : 'rgba(220, 53, 69, 0.8)'),
                        borderColor: setupPnls.map(pnl => pnl >= 0 ? 'rgb(40, 167, 69)' : 'rgb(220, 53, 69)'),
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'P&L ($)'
                            }}
                        }}
                    }}
                }}
            }});
        }}
        """