import httpx
import asyncio
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class MarketService:
    """Service for fetching market data from various exchanges"""

    BINANCE_BASE_URL = "https://api.binance.com/api/v3"
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    async def get_price(self, symbol: str, exchange: str = "BINANCE") -> dict:
        """Get current price for a symbol"""
        if exchange.upper() == "BINANCE":
            return await self._get_binance_price(symbol)
        elif exchange.upper() == "SOLANA":
            return await self._get_solana_price(symbol)
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _get_binance_price(self, symbol: str) -> dict:
        """Get price from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                # Get ticker data
                response = await client.get(
                    f"{self.BINANCE_BASE_URL}/ticker/24hr",
                    params={"symbol": symbol}
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "symbol": symbol,
                    "price": float(data["lastPrice"]),
                    "volume_24h": float(data["volume"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                    "change_24h_percent": float(data["priceChangePercent"])
                }
        except Exception as e:
            raise Exception(f"Failed to get Binance price: {str(e)}")

    async def _get_solana_price(self, symbol: str) -> dict:
        """Get price from Solana (Jupiter or other sources)"""
        # TODO: Implement Solana price fetching
        # This would typically use Jupiter API or similar
        raise NotImplementedError("Solana price fetching not yet implemented")

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        exchange: str = "BINANCE"
    ) -> List[dict]:
        """Get candlestick data"""
        if exchange.upper() == "BINANCE":
            return await self._get_binance_klines(symbol, interval, limit)
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _get_binance_klines(self, symbol: str, interval: str, limit: int) -> List[dict]:
        """Get klines from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BINANCE_BASE_URL}/klines",
                    params={
                        "symbol": symbol,
                        "interval": interval,
                        "limit": limit
                    }
                )
                response.raise_for_status()
                klines = response.json()

                # Format klines data
                formatted_klines = []
                for kline in klines:
                    formatted_klines.append({
                        "time": kline[0] // 1000,  # Convert to seconds
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[7])
                    })
                return formatted_klines
        except Exception as e:
            raise Exception(f"Failed to get Binance klines: {str(e)}")

    async def get_24h_stats(self, symbol: str, exchange: str = "BINANCE") -> dict:
        """Get 24h statistics"""
        if exchange.upper() == "BINANCE":
            return await self._get_binance_24h_stats(symbol)
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _get_binance_24h_stats(self, symbol: str) -> dict:
        """Get 24h stats from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BINANCE_BASE_URL}/ticker/24hr",
                    params={"symbol": symbol}
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "symbol": symbol,
                    "price": float(data["lastPrice"]),
                    "price_change": float(data["priceChange"]),
                    "price_change_percent": float(data["priceChangePercent"]),
                    "high": float(data["highPrice"]),
                    "low": float(data["lowPrice"]),
                    "volume": float(data["volume"]),
                    "quote_volume": float(data.get("quoteVolume", data.get("quoteAssetVolume", 0))),
                    "open_time": data["openTime"],
                    "close_time": data["closeTime"]
                }
        except Exception as e:
            raise Exception(f"Failed to get Binance 24h stats: {str(e)}")

    async def get_symbols(self, exchange: str = "BINANCE") -> List[str]:
        """Get list of supported symbols on an exchange"""
        if exchange.upper() == "BINANCE":
            return await self._get_binance_symbols()
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _get_binance_symbols(self) -> List[str]:
        """Get supported symbols from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BINANCE_BASE_URL}/exchangeInfo")
                response.raise_for_status()
                data = response.json()

                symbols = [symbol["symbol"] for symbol in data["symbols"]]
                return symbols
        except Exception as e:
            raise Exception(f"Failed to get Binance symbols: {str(e)}")
