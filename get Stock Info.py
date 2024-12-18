import yfinance as yf
import pandas_ta as ta
import pandas as pd
from IPython.display import display

def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1y")
    return data

def calculate_indicators(data):
    data['SMA5'] = ta.sma(data['Close'], length=5)
    data['SMA10'] = ta.sma(data['Close'], length=10)
    data['SMA20'] = ta.sma(data['Close'], length=20)
    data['SMA50'] = ta.sma(data['Close'], length=50)
    data['SMA100'] = ta.sma(data['Close'], length=100)
    data['SMA200'] = ta.sma(data['Close'], length=200)
    data['ATR21'] = ta.atr(data['High'], data['Low'], data['Close'], length=21)
    
    bb = ta.bbands(data['Close'], length=20)
    data['BB_upper'] = bb['BBU_20_2.0']
    data['BB_middle'] = bb['BBM_20_2.0']
    data['BB_lower'] = bb['BBL_20_2.0']
    
    return data

def calculate_percentage_change(data, days):
    return (data['Close'].iloc[-1] - data['Close'].iloc[-days-1]) / data['Close'].iloc[-days-1] * 100

def calculate_distance_to_sma(data, sma_column):
    return (data['Close'].iloc[-1] - data[sma_column].iloc[-1]) / data[sma_column].iloc[-1] * 100

def calculate_trend(data):
    if data['Close'].iloc[-1] > data['Close'].iloc[-2]:
        return "steigend"
    else:
        return "fallend"

def calculate_lowest_low(data, days):
    return data['Low'].iloc[-days:].min()

def calculate_highest_high(data, days):
    return data['High'].iloc[-days:].max()

def main(symbol):
    data = get_stock_data(symbol)
    data = calculate_indicators(data)
    
    high_low_range = data['High'].iloc[-2] - data['Low'].iloc[-2]
    high_low_range_pct = (high_low_range / data['Low'].iloc[-2]) * 100
    
    lowest_low_10 = calculate_lowest_low(data, 10)
    highest_high_10 = calculate_highest_high(data, 10)
    low_high_range_10 = highest_high_10 - lowest_low_10
    low_high_range_10_pct = (low_high_range_10 / lowest_low_10) * 100

    results = {
        'Kennzahl': [
            'Open Kurs vom Vortag', 'High Kurs vom Vortag', 'Low Kurs vom Vortag', 'Close Kurs vom Vortag',
            'Spanne zwischen High und Low (absolut)', 'Spanne zwischen High und Low (in %)',
            'Entwicklung Schlusskurs gegenüber 5 Tagen', 'Entwicklung Schlusskurs gegenüber 10 Tagen',
            'Entwicklung Schlusskurs gegenüber 20 Tagen', 'Entwicklung Schlusskurs gegenüber 60 Tagen',
            'ATR(21)', 'Trend', 'Abstand zu SMA(5)', 'Abstand zu SMA(10)', 'Abstand zu SMA(20)',
            'Abstand zu SMA(50)', 'Abstand zu SMA(100)', 'Abstand zu SMA(200)',
            'Abstand zum oberen Bollinger Band', 'Abstand zum unteren Bollinger Band',
            'Lowest Low der letzten 10 Tage', 'Highest High der letzten 10 Tage',
            'Spanne zwischen Lowest Low und Highest High der letzten 10 Tage (absolut)',
            'Spanne zwischen Lowest Low und Highest High der letzten 10 Tage (in %)'
        ],
        'Wert': [
            data['Open'].iloc[-2], data['High'].iloc[-2], data['Low'].iloc[-2], data['Close'].iloc[-2],
            high_low_range, f"{high_low_range_pct:.2f}%",
            f"{calculate_percentage_change(data, 5):.2f}%", f"{calculate_percentage_change(data, 10):.2f}%",
            f"{calculate_percentage_change(data, 20):.2f}%", f"{calculate_percentage_change(data, 60):.2f}%",
            f"{data['ATR21'].iloc[-1]:.2f}", calculate_trend(data), f"{calculate_distance_to_sma(data, 'SMA5'):.2f}%",
            f"{calculate_distance_to_sma(data, 'SMA10'):.2f}%", f"{calculate_distance_to_sma(data, 'SMA20'):.2f}%",
            f"{calculate_distance_to_sma(data, 'SMA50'):.2f}%", f"{calculate_distance_to_sma(data, 'SMA100'):.2f}%",
            f"{calculate_distance_to_sma(data, 'SMA200'):.2f}%", 
            f"{(data['Close'].iloc[-1] - data['BB_upper'].iloc[-1]) / data['BB_upper'].iloc[-1] * 100:.2f}%",
            f"{(data['Close'].iloc[-1] - data['BB_lower'].iloc[-1]) / data['BB_lower'].iloc[-1] * 100:.2f}%",
            lowest_low_10, highest_high_10, low_high_range_10, f"{low_high_range_10_pct:.2f}%"
        ]
    }
    
    results_df = pd.DataFrame(results)
    display(results_df)

if __name__ == "__main__":
    while True:
        symbol = input("Geben Sie das Aktiensymbol ein: ")
        main(symbol)
        choice = input("Möchten Sie eine weitere Berechnung durchführen? (1: Ja, 2: Nein): ")
        if choice != '1':
            break