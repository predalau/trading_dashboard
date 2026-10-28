"""Paper execution venue: simulated fills against the default paper account."""
from app.execution.base import ExecutionVenue, OrderRequest, OrderResult
from app.models import Order, OrderStatus
from app.services.market_service import MarketService
from app.services.paper_accounting import open_paper_position


class PaperVenue(ExecutionVenue):
    async def place_order(self, db, req: OrderRequest, account) -> OrderResult:
        # Idempotency: a repeat (api_key_id, client_order_id) returns the first order.
        if req.client_order_id:
            existing = (
                db.query(Order)
                .filter(
                    Order.api_key_id == req.api_key_id,
                    Order.client_order_id == req.client_order_id,
                )
                .first()
            )
            if existing:
                return self._to_result(existing, idempotent_replay=True)

        # MARKET orders fill at the last traded price if none was supplied.
        price = req.price
        if price is None:
            price = (await MarketService().get_price(req.symbol))["price"]

        # Reserve margin + open the position (raises InsufficientBalance).
        trade = open_paper_position(
            db,
            account,
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            price=price,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            notes=req.notes,
        )

        order = Order(
            account_id=account.id,
            symbol=req.symbol,
            exchange="BINANCE",
            order_type=req.type,
            side=req.side,
            quantity=req.quantity,
            price=req.price,
            status=OrderStatus.FILLED,
            filled_quantity=req.quantity,
            filled_price=price,
            mode="paper",
            api_key_id=req.api_key_id,
            client_order_id=req.client_order_id,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return self._to_result(order, trade_id=trade.id)

    @staticmethod
    def _to_result(order: Order, trade_id=None, idempotent_replay=False) -> OrderResult:
        status = order.status.value if hasattr(order.status, "value") else str(order.status)
        side = order.side.value if hasattr(order.side, "value") else str(order.side)
        return OrderResult(
            order_id=order.id,
            status=status,
            mode=order.mode,
            symbol=order.symbol,
            side=side,
            quantity=order.quantity,
            filled_price=order.filled_price,
            trade_id=trade_id,
            client_order_id=order.client_order_id,
            idempotent_replay=idempotent_replay,
        )
