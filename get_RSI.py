from stock_indicators import indicators

# This method is NOT a part of the library.
quotes = get_historical_quotes("SPY")

# calculate RSI(14)
results = indicators.get_rsi(quotes, 14)
print(results)