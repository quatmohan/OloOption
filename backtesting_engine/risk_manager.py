"""
Risk management and daily limits
"""

from typing import Optional


class RiskManager:
    """Implements risk controls and daily limits"""
    
    def __init__(self, daily_max_loss: float):
        self.daily_max_loss = abs(daily_max_loss)  # Ensure positive value
        self.daily_pnl = 0.0
    
    def check_daily_limit(self, current_pnl: float) -> bool:
        """Check if daily limit is breached"""
        return current_pnl <= -self.daily_max_loss
    
    def should_close_all_positions(self, total_pnl: float) -> bool:
        """Check if all positions should be closed due to daily limit"""
        return self.check_daily_limit(total_pnl)
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L tracking"""
        self.daily_pnl = pnl
    
    def reset_daily_tracking(self):
        """Reset daily tracking for new trading day"""
        self.daily_pnl = 0.0
    
    def get_remaining_risk_capacity(self) -> float:
        """Get remaining risk capacity for the day"""
        return max(0, self.daily_max_loss + self.daily_pnl)