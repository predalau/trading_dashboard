from sqlalchemy.orm import Session
from app.models import Trade, Order, PaperTradingAccount


class TradingService:
    """Service for handling trading operations"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_portfolio_value(self, account_id: int) -> dict:
        """Calculate portfolio value including unrealized P&L"""
        account = self.db.query(PaperTradingAccount).filter(
            PaperTradingAccount.id == account_id
        ).first()

        if not account:
            return None

        open_trades = self.db.query(Trade).filter(
            Trade.account_id == account_id,
            Trade.is_open == True
        ).all()

        # TODO: Get current prices from market service
        unrealized_pl = 0
        for trade in open_trades:
            # Will be updated when market prices are integrated
            pass

        closed_trades = self.db.query(Trade).filter(
            Trade.account_id == account_id,
            Trade.is_open == False
        ).all()

        realized_pl = sum(t.profit_loss or 0 for t in closed_trades)

        return {
            "account_id": account_id,
            "cash_balance": account.available_balance,
            "unrealized_pl": unrealized_pl,
            "realized_pl": realized_pl,
            "total_value": account.available_balance + unrealized_pl,
            "initial_balance": account.initial_balance,
            "return_percentage": ((account.available_balance + unrealized_pl - account.initial_balance) / account.initial_balance) * 100
        }

    def get_trade_statistics(self, account_id: int) -> dict:
        """Calculate trading statistics"""
        trades = self.db.query(Trade).filter(
            Trade.account_id == account_id,
            Trade.is_open == False
        ).all()

        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "avg_loss": 0,
                "profit_factor": 0
            }

        total_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        total_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))

        winning_trades = [t for t in trades if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss and t.profit_loss < 0]

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(trades)) * 100 if trades else 0,
            "avg_profit": total_profit / len(winning_trades) if winning_trades else 0,
            "avg_loss": total_loss / len(losing_trades) if losing_trades else 0,
            "profit_factor": total_profit / total_loss if total_loss > 0 else 0,
            "total_realized_pl": total_profit - total_loss
        }
