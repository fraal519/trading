import pandas as pd
import numpy as np
import yfinance as yf
from IPython.display import display

def read_stock_symbols(filename):
    """
    Reads the CSV file with stock symbols.

    Args:
        filename (str): The filename of the CSV file.

    Returns:
        list: A list of stock symbols.
    """
    df = pd.read_csv(filename)
    return df['Symbol'].tolist()

def get_stock_data(symbol):
    """
    Retrieves historical data for a given stock symbol.

    Args:
        symbol (str): The stock symbol.

    Returns:
        DataFrame: A DataFrame with historical data.
    """
    stock = yf.Ticker(symbol)
    return stock.history(period="1y")

def calculate_sma(data, window):
    """
    Calculates the simple moving average (SMA).

    Args:
        data (DataFrame): A DataFrame with historical data.
        window (int): The window size for the moving average.

    Returns:
        Series: A series with the SMA values.
    """
    return data['Close'].rolling(window=window).mean()

def calculate_ichimoku(data):
    """
    Calculates the Ichimoku components.

    Args:
        data (DataFrame): A DataFrame with historical data.

    Returns:
        None: The function adds the Ichimoku components directly to the DataFrame.
    """
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    data['Tenkan_Sen'] = tenkan_sen
    data['Kijun_Sen'] = kijun_sen

    span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    span_b = ((high_52 + low_52) / 2).shift(26)

    data['Span_A'] = span_a
    data['Span_B'] = span_b

def check_cup_with_handle(data):
    """
    Checks if a "cup with handle" formation is present.

    Args:
        data (DataFrame): A DataFrame with historical data.

    Returns:
        bool: True if a "cup with handle" formation is present, otherwise False.
    """
    cup_found = False
    handle_found = False

    # Parameters for the cup with handle formation
    cup_depth_threshold = 0.33  # 33% decline from the peak
    handle_depth_threshold = 0.12  # 12% decline from the peak
    cup_length_min = 30  # Minimum number of days for the cup formation
    handle_length_min = 5  # Minimum number of days for the handle formation
    handle_length_max = cup_length_min  # Handle should not exceed the cup portion in time

    # Check for a 30% uptrend before the base's construction
    uptrend_threshold = 0.30
    for i in range(len(data) - cup_length_min - handle_length_max):
        pre_cup = data['Close'].iloc[:i]
        if len(pre_cup) > 0 and (pre_cup.max() - pre_cup.min()) / pre_cup.min() >= uptrend_threshold:
            cup = data['Close'].iloc[i:i + cup_length_min]
            max_price = cup.max()
            min_price = cup.min()
            cup_depth = (max_price - min_price) / max_price

            # Check if the cup is at least 1.5 times as long as it is deep
            if cup_depth > cup_depth_threshold and len(cup) / cup_depth >= 1.5:
                cup_found = True

                # Check for the handle formation
                handle = data['Close'].iloc[i + cup_length_min:i + cup_length_min + handle_length_max]
                handle_max_price = handle.max()
                handle_min_price = handle.min()
                handle_depth = (handle_max_price - handle_min_price) / handle_max_price

                # Check if the handle is relatively flat and does not exceed the cup in time or size of decline
                if handle_depth < handle_depth_threshold and handle_min_price > min_price + (max_price - min_price) / 3:
                    handle_found = True

                    # Check if the handle starts with a down day in price
                    if handle.iloc[0] > handle.iloc[1]:
                        # Check if the volume decreases during the handle formation
                        cup_volume = data['Volume'].iloc[i:i + cup_length_min]
                        handle_volume = data['Volume'].iloc[i + cup_length_min:i + cup_length_min + handle_length_max]
                        if cup_volume.max() > handle_volume.max():
                            # Check if the breakout from the handle occurs with above-average volume
                            breakout_volume = data['Volume'].iloc[i + cup_length_min + handle_length_max]
                            avg_volume = data['Volume'].rolling(window=50).mean().iloc[i + cup_length_min + handle_length_max]
                            if breakout_volume > avg_volume:
                                # Additional checks for the handle
                                handle_midpoint = (handle_max_price + handle_min_price) / 2
                                cup_midpoint = (max_price + min_price) / 2
                                if handle_midpoint > cup_midpoint:
                                    return True

    return False

def check_buy_signals(data):
    """
    Checks for buy signals.

    Args:
        data (DataFrame): A DataFrame with historical data.

    Returns:
        list: A list of buy signals.
    """
    signals = []

    # SMA 15 crosses SMA 50 from below
    sma_15 = calculate_sma(data, 15)
    sma_50 = calculate_sma(data, 50)
    if (sma_15.iloc[-4] < sma_50.iloc[-4]) and (sma_15.iloc[-3] > sma_50.iloc[-3]):
        signals.append("SMA 15 crosses SMA 50 from below")

    # Trading volume is 20% higher than the 50-day average (last two trading days)
    avg_volume_50 = data['Volume'].rolling(window=50).mean()
    if data['Volume'].iloc[-2] > 1.2 * avg_volume_50.iloc[-2] or data['Volume'].iloc[-3] > 1.2 * avg_volume_50.iloc[-3]:
        signals.append("Trading volume is 20% higher than the 50-day average (last two trading days)")

    # Ichimoku condition
    calculate_ichimoku(data)
    if (data['Tenkan_Sen'].iloc[-4] < data['Kijun_Sen'].iloc[-4]) and (data['Tenkan_Sen'].iloc[-3] > data['Kijun_Sen'].iloc[-3]):
        if data['Tenkan_Sen'].iloc[-3] > max(data['Span_A'].iloc[-3], data['Span_B'].iloc[-3]) and data['Kijun_Sen'].iloc[-3] > max(data['Span_A'].iloc[-3], data['Span_B'].iloc[-3]):
            signals.append("Strong Ichimoku buy signal: Cross above the cloud")

    # Check for "cup with handle" formation
    if check_cup_with_handle(data):
        signals.append("Cup with handle formation detected")

    return signals

def main():
    """
    Main program that reads the CSV file, checks for buy signals, and outputs the results.

    Args:
        None

    Returns:
        None
    """
    while True:
        filename = input("Please enter the filename of the CSV file: ")
        symbols = read_stock_symbols(filename)

        results = []

        for symbol in symbols:
            print(f"Checking buy signals for {symbol}...")
            data = get_stock_data(symbol)
            signals = check_buy_signals(data)
            for signal in signals:
                results.append({"Symbol": symbol, "Signal": signal})

        if results:
            results_df = pd.DataFrame(results)
            print("\nResults:")
            display(results_df)
        else:
            print("No buy signals found.")

        another_calculation = input("Would you like to perform another calculation? (1 for Yes, 2 for No): ").strip()
        if another_calculation != '1':
            break

if __name__ == "__main__":
    main()
