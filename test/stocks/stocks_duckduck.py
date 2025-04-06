import json

import aiohttp
from requests import Session
from requests_cache import CacheMixin, SQLiteCache

import config


class CachedLimiterSession(CacheMixin, Session):
    pass


cached_session = CachedLimiterSession(
    backend=SQLiteCache("cache/stocks.sqlite"),
    expire_after=config.REQ_CACHE_EXP,
)

base_url = "https://duckduckgo.com/stocks.js"

vqd = "4-308701970170996122105198695279320671531"

headers = {
    "Host": "duckduckgo.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://duckduckgo.com/",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": 1,
    "Sec-GPC": 1,
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
}


class Stocks:
    @staticmethod
    async def stocks_data(symbol):
        try:
            params = {
                "action": "quote",
                "symbol": symbol,
                "query": "Usd stock",
                "vqd": vqd,
            }
            async with aiohttp.ClientSession() as aio_session:
                async with aio_session.get(
                    base_url, params=params, headers=headers
                ) as response:
                    stock_info = await response.json()
                    print(stock_info)

            # Extract stock information
            symbol = stock_info.get("symbol", "N/A")
            current_price = stock_info.get("latestPrice", "N/A")
            previous_close = stock_info.get("previousClose", "N/A")
            open_price = stock_info.get("regularMarketOpen", "N/A")
            high_price = stock_info.get("regularMarketDayHigh", "N/A")
            low_price = stock_info.get("regularMarketDayLow", "N/A")

            params = {
                "action": "historical",
                "symbol": symbol,
                "range": "5d",
                "query": "Usd stock",
                "vqd": vqd,
            }

            async with aiohttp.ClientSession() as aio_session:
                async with aio_session.get(
                    base_url, params=params, headers=headers
                ) as response:
                    stock_history = await response.json()
                    print(stock_history)

            # The below block assumes Pandas-like structure, adjust based on actual format
            # close_today = stock_history["Close"][-1]
            # close_yesterday = stock_history["Close"][-2]
            # daily_change_dollar = close_today - close_yesterday
            # daily_change_percent = (daily_change_dollar / close_yesterday) * 100

            return {
                symbol,
                current_price,
                previous_close,
                open_price,
                high_price,
                low_price,
                None,
                None,
                # "daily_change_dollar": daily_change_dollar,
                # "daily_change_percent": daily_change_percent
            }

        except Exception as e:
            return f"An error occurred: {e}"

    @staticmethod
    async def stock_price(symbol):
        try:
            stock = yf.Ticker(symbol, session=cached_session)
            return stock.info.get("currentPrice", "N/A")
        except Exception as e:
            return f"An error occurred: {e}"

    @staticmethod
    async def stock_info(symbol, amount):
        try:

            params = {
                "action": "quote",
                "symbol": symbol,
                "range": "5d",
                "query": "Usd stock",
                "vqd": vqd,
            }

            async with aiohttp.ClientSession() as aio_session:
                async with aio_session.get(
                    base_url, params=params, headers=headers
                ) as response:
                    stock_info = await response.json()

            current_price = stock_info.get("latestPrice", None)
            if current_price is None:
                return f"Error: Could not retrieve current price for symbol '{symbol}'."

            shares = amount / current_price
            purchase_price = stock_info.get("previousClose", current_price)

            loss = (purchase_price - current_price) * shares
            loss_perc = (
                ((purchase_price - current_price) / purchase_price) * 100
                if purchase_price
                else 0
            )
            return shares, loss, loss_perc, current_price
        except Exception as e:
            return f"An error occurred: {e}"

    @staticmethod
    async def stocks_names():
        with open("assets/data/stocks.json", "r") as f:
            symbols = json.load(f)

        stock_info_list = []

        for symbol in symbols[:25]:
            try:
                params = {
                    "action": "quote",
                    "symbol": symbol,
                    "range": "5d",
                    "query": "Usd stock",
                    "vqd": vqd,
                }

                async with aiohttp.ClientSession() as aio_session:
                    async with aio_session.get(
                        base_url, params=params, headers=headers
                    ) as response:
                        stock_info = await response.json()

                name = stock_info.get("companyName", "N/A")
                stock_info_list.append(f"{symbol} - {name}")
            except Exception as e:
                stock_info_list.append(f"{symbol} - Error: {e}")

        return stock_info_list

    @staticmethod
    async def stocks_list():
        with open("assets/data/stocks_names.json", "r") as f:
            symbols = json.load(f)

        stock_list = []

        for symbol, name in list(symbols.items())[:25]:
            try:
                stock_list.append(f"{symbol} - {name}")
            except Exception as e:
                stock_list.append(f"{symbol} - N/A: {e}")

        return stock_list
