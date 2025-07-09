import json

from ..util import googlestocks


class Stocks:
    @staticmethod
    async def stocks_data(symbol: str):
        try:
            exchange = Stocks.get_exchange(symbol)
            if not exchange:
                print(f"[ERROR] exchange not found for {symbol}")
                return (False,) + (None,) * 8

            result = list(googlestocks.search(f"{symbol}:{exchange}"))
            if not result:
                print(f"[ERROR] no results for {symbol}:{exchange}")
                return (False,) + (None,) * 8

            data = result[0]

            trading = data.get("trading", {})

            current_price = trading.get("last", "N/A")
            previous_close = data.get("last_close", "N/A")

            df = googlestocks.history_df(f"{symbol}:{exchange}", 1)
            if len(df) < 2:
                raise Exception("Not enough intraday data")

            open_price = df["last"].iloc[0]
            high_price = df["last"].max()
            low_price = df["last"].min()

            close_today = df["last"].iloc[-1]
            close_yesterday = df["last"].iloc[-2]
            daily_change_dollar = close_today - close_yesterday
            daily_change_percent = (daily_change_dollar / close_yesterday) * 100

            return (
                True,
                symbol,
                current_price,
                previous_close,
                open_price,
                high_price,
                low_price,
                daily_change_dollar,
                daily_change_percent,
            )
        except Exception as e:
            print(f"[ERROR] getting stocks data for {symbol}: {e}")
            return (False,) + (None,) * 8

    async def stock_price(symbol: str):
        try:
            exchange = Stocks.get_exchange(symbol)
            if not exchange:
                print(f"[ERROR] exchange not found for {symbol}")
                return (False,) + (None,) * 8

            result = list(googlestocks.search(f"{symbol}:{exchange}"))
            if not result:
                print(f"[ERROR] no results for {symbol}:{exchange}")
                return (False,) + (None,) * 8

            data = result[0]

            if not data:
                return (False,) + (None,) * 8

            trading = data.get("trading", {})

            current_price = trading.get("last", "N/A")

            return current_price
        except Exception as e:
            return f"An error occurred: {e}"

    @staticmethod
    async def stock_info(symbol: str, amount: float):
        try:
            exchange = Stocks.get_exchange(symbol)
            if not exchange:
                print(f"[ERROR] exchange not found for {symbol}")
                return (False,) + (None,) * 3

            result = list(googlestocks.search(f"{symbol}:{exchange}"))
            if not result:
                print(f"[ERROR] no results for {symbol}:{exchange}")
                return (False,) + (None,) * 3

            data = result[0]
            trading = data.get("trading", {})

            current_price = trading.get("last")
            previous_close = data.get("last_close")

            if not isinstance(current_price, (int, float)) or not isinstance(
                previous_close, (int, float)
            ):
                print(f"[ERROR] Invalid price data for {symbol}")
                return (False,) + (None,) * 3

            shares = (
                amount / current_price
            )  # shares bought with the given dollar amount
            loss = (previous_close - current_price) * shares
            loss_perc = (
                ((previous_close - current_price) / previous_close) * 100
                if previous_close
                else 0
            )

            return (
                shares,
                loss,
                loss_perc,
                current_price,
            )  # return price per share separately
        except Exception as e:
            print(f"[ERROR] stock_info failed for {symbol}: {e}")
            return None, None, None, None

    # Slow and looks empty
    """ 
    async def stocks_list(query: str = ""):
        try:
            if query:
                query = f"{query}"
            results = list(googlestocks.search_list(query))

            stock_list = []
            for item in results[:25]:
                symbol = item.get("code", "N/A")
                description = item.get("name", "N/A")
                stock_list.append(f"{symbol} - {description}")

            return stock_list
        except Exception as e:
            print(f"[ERROR] An error occurred while fetching stocks list: {e}")
            return []
    """

    async def stocks_list(query: str):
        with open("assets/data/ticker_to_cik_mapping.json", "r") as f:
            symbols = json.load(f)

        stock_list = []

        for entry in symbols[:25]:
            try:
                stock_list.append(f"{entry['Ticker']} - {entry['Name']}")
            except KeyError:
                stock_list.append(f"{entry.get('Ticker', 'N/A')} - N/A")

        return stock_list

    @staticmethod
    def get_exchange(symbol):
        try:
            results = list(googlestocks.search(symbol))
            for item in results:
                if item.get("code", "").lower() == symbol.lower():
                    market = item.get("market")
                    return market
            return None
        except Exception as e:
            print(f"[ERROR] {e}")
            return None
