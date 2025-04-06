import json

import yfinance as yf
from pyrate_limiter import Duration, Limiter, RequestRate
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket

import config


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


session = CachedLimiterSession(
    limiter=Limiter(RequestRate(10, Duration.SECOND * 3)),
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("cache/yfinance.sqlite"),
    expire_after=config.REQ_CACHE_EXP,
)


if config.DEBUG:
    yf.enable_debug_mode()


class Stocks:
    async def stocks_data(symbol):
        try:
            stock = yf.Ticker(symbol, session=session)
            stock_info = stock.info
            success = False
            if stock_info:
                success = True

                # Get stock information
                symbol = stock_info.get("symbol", "N/A")
                current_price = stock_info.get("currentPrice", "N/A")
                previous_close = stock_info.get("regularMarketPreviousClose", "N/A")
                open_price = stock_info.get("regularMarketOpen", "N/A")
                high_price = stock_info.get("regularMarketDayHigh", "N/A")
                low_price = stock_info.get("regularMarketDayLow", "N/A")

                # Get historical data (e.g., last two days)
                data = stock.history(period="2d")

                # Calculate daily change in dollar
                close_today = data["Close"].iloc[-1]
                close_yesterday = data["Close"].iloc[-2]
                daily_change_dollar = close_today - close_yesterday

                # Calculate daily change in percentage
                daily_change_percent = (daily_change_dollar / close_yesterday) * 100

                return (
                    success,
                    symbol,
                    current_price,
                    previous_close,
                    open_price,
                    high_price,
                    low_price,
                    daily_change_dollar,
                    daily_change_percent,
                )
            return (
                success,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

        except Exception as e:
            return f"An error occurred: {e}"

    async def stock_price(symbol):
        try:
            stock = yf.Ticker(symbol, session=session)
            return stock.info.get("currentPrice", "N/A")
        except Exception as e:
            return f"An error occurred: {e}"

    async def stock_info(symbol, amount):
        try:
            stock = yf.Ticker(symbol, session=session)
            stock_info = stock.info
            current_price = stock_info.get("currentPrice", None)
            if current_price is None:
                return f"Error: Could not retrieve current price for symbol '{symbol}'."

            # Calculate the number of shares that can be purchased
            shares = amount / current_price

            purchase_price = stock_info.get("previousClose", current_price)

            # Calculate loss and percentage loss
            loss = (purchase_price - current_price) * shares
            loss_perc = (
                ((purchase_price - current_price) / purchase_price) * 100
                if purchase_price
                else 0
            )
            return shares, loss, loss_perc, current_price
        except Exception as e:
            return f"An error occurred: {e}"

    def stocks_names():
        with open("assets/data/stocks.json", "r") as f:
            symbols = json.load(f)

        stock_info_list = []

        for symbol in symbols[:25]:
            try:
                stock = yf.Ticker(symbol, session=session)
                name = stock.info.get("longName", "N/A")
                stock_info_list.append(f"{symbol} - {name}")
            except Exception as e:
                stock_info_list.append(f"{symbol} - Error: {e}")

        return stock_info_list

    async def stocks_list():
        with open("assets/data/ticker_to_cik_mapping.json", "r") as f:
            symbols = json.load(f)

        stock_list = []

        for entry in symbols[:25]:
            try:
                stock_list.append(f"{entry['Ticker']} - {entry['Name']}")
            except KeyError:
                stock_list.append(f"{entry.get('Ticker', 'N/A')} - N/A")

        return stock_list
