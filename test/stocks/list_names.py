import json
import os

import yfinance as yf


def get_stocks_with_names():
    # Load list of symbols
    with open("stocks.json", "r") as f:
        symbols = json.load(f)

    # Load existing data if file exists
    path = "stocks_names.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Update only missing symbols
    for symbol in symbols:
        if symbol in existing_data:
            continue
        try:
            stock = yf.Ticker(symbol)
            name = stock.info.get("longName", "")
            existing_data[symbol] = name
            print(f"Fetched: {symbol} - {name}")
        except Exception as e:
            existing_data[symbol] = ""
            print(f"Error fetching {symbol}: {e}")

        # Save after each symbol to ensure progress is saved
        with open(path, "w") as f:
            json.dump(existing_data, f, indent=4)

    print("Done.")


if __name__ == "__main__":
    get_stocks_with_names()
