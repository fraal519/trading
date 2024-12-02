import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

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
    cup_length_min = 42  # Minimum number of days for the cup formation (7 weeks)
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

def analyze_chart_patterns(symbols):
    """
    Analyzes the chart patterns for a list of stock symbols.

    Args:
        symbols (list): A list of stock symbols.

    Returns:
        list: A list of symbols with a "cup with handle" formation.
    """
    results = []
    for symbol in symbols:
        data = get_stock_data(symbol)
        if check_cup_with_handle(data):
            results.append(symbol)
    return results

def main():
    """
    Main function that reads a CSV file with stock symbols, performs chart pattern analysis, and outputs the results.

    Args:
        None

    Returns:
        None
    """
    filename = input("Please enter the filename of the CSV file: ")
    symbols = read_stock_symbols(filename)
    results = analyze_chart_patterns(symbols)
    
    if results:
        print("Symbols with Cup with Handle formation:")
        for symbol in results:
            print(symbol)
    else:
        print("No Cup with Handle formation detected for any symbol.")

if __name__ == "__main__":
    main()