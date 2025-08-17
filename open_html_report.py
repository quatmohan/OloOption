"""
Simple script to open the latest HTML report in browser
"""

import os
import webbrowser
import glob

def open_latest_html_report():
    """Open the most recent HTML report in the default browser"""
    reports_dir = "backtest_reports"
    
    if not os.path.exists(reports_dir):
        print("❌ No backtest_reports directory found. Run a backtest first.")
        return
    
    # Find all HTML reports
    html_files = glob.glob(os.path.join(reports_dir, "*_report.html"))
    
    if not html_files:
        print("❌ No HTML reports found. Run a backtest first.")
        return
    
    # Get the most recent HTML report
    latest_report = max(html_files, key=os.path.getctime)
    
    print(f"🌐 Opening HTML report: {os.path.basename(latest_report)}")
    
    # Open in default browser
    webbrowser.open(f"file://{os.path.abspath(latest_report)}")
    
    print("✅ HTML report opened in your default browser!")

if __name__ == "__main__":
    open_latest_html_report()