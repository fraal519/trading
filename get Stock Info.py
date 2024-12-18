import yfinance as yf
import pandas as pd
from IPython.display import display

def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1y")
    return data

def calculate_indicators(data):
    data['SMA5'] = data['Close'].rolling(window=5).mean()
    data['SMA10'] = data['Close'].rolling(window=10).mean()
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA100'] = data['Close'].rolling(window=100).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    data['ATR21'] = data['High'].rolling(window=21).max() - data['Low'].rolling(window=21).min()
    
    data['BB_middle'] = data['Close'].rolling(window=20).mean()
    data['BB_std'] = data['Close'].rolling(window=20).std()
    data['BB_upper'] = data['BB_middle'] + (2 * data['BB_std'])
    data['BB_lower'] = data['BB_middle'] - (2 * data['BB_std'])
    
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

def calculate_metrics(symbol):
    data = get_stock_data(symbol)
    data = calculate_indicators(data)
    
    high_low_range = data['High'].iloc[-2] - data['Low'].iloc[-2]
    high_low_range_pct = (high_low_range / data['Low'].iloc[-2]) * 100
    
    lowest_low_10 = calculate_lowest_low(data, 10)
    highest_high_10 = calculate_highest_high(data, 10)
    low_high_range_10 = highest_high_10 - lowest_low_10
    low_high_range_10_pct = (low_high_range_10 / lowest_low_10) * 100

    results = {
        'Open Kurs vom Vortag': data['Open'].iloc[-2],
        'High Kurs vom Vortag': data['High'].iloc[-2],
        'Low Kurs vom Vortag': data['Low'].iloc[-2],
        'Close Kurs vom Vortag': data['Close'].iloc[-2],
        'Spanne zwischen High und Low (absolut)': high_low_range,
        'Spanne zwischen High und Low (in %)': f"{high_low_range_pct:.2f}%",
        'Entwicklung Schlusskurs gegenüber 5 Tagen': f"{calculate_percentage_change(data, 5):.2f}%",
        'Entwicklung Schlusskurs gegenüber 10 Tagen': f"{calculate_percentage_change(data, 10):.2f}%",
        'Entwicklung Schlusskurs gegenüber 20 Tagen': f"{calculate_percentage_change(data, 20):.2f}%",
        'Entwicklung Schlusskurs gegenüber 60 Tagen': f"{calculate_percentage_change(data, 60):.2f}%",
        'ATR(21)': f"{data['ATR21'].iloc[-1]:.2f}",
        'Trend': calculate_trend(data),
        'Abstand zu SMA(5)': f"{calculate_distance_to_sma(data, 'SMA5'):.2f}%",
        'Abstand zu SMA(10)': f"{calculate_distance_to_sma(data, 'SMA10'):.2f}%",
        'Abstand zu SMA(20)': f"{calculate_distance_to_sma(data, 'SMA20'):.2f}%",
        'Abstand zu SMA(50)': f"{calculate_distance_to_sma(data, 'SMA50'):.2f}%",
        'Abstand zu SMA(100)': f"{calculate_distance_to_sma(data, 'SMA100'):.2f}%",
        'Abstand zu SMA(200)': f"{calculate_distance_to_sma(data, 'SMA200'):.2f}%",
        'Abstand zum oberen Bollinger Band': f"{(data['Close'].iloc[-1] - data['BB_upper'].iloc[-1]) / data['BB_upper'].iloc[-1] * 100:.2f}%",
        'Abstand zum unteren Bollinger Band': f"{(data['Close'].iloc[-1] - data['BB_lower'].iloc[-1]) / data['BB_lower'].iloc[-1] * 100:.2f}%",
        'Lowest Low der letzten 10 Tage': lowest_low_10,
        'Highest High der letzten 10 Tage': highest_high_10,
        'Spanne zwischen Lowest Low und Highest High der letzten 10 Tage (absolut)': low_high_range_10,
        'Spanne zwischen Lowest Low und Highest High der letzten 10 Tage (in %)': f"{low_high_range_10_pct:.2f}%"
    }
    
    return results

def main():
    choice = input("Möchten Sie eine einzelne Aktie (1) oder eine CSV-Datei mit mehreren Aktien (2) verwenden? (1/2): ")
    
    if choice == '1':
        symbol = input("Geben Sie das Aktiensymbol ein: ")
        results = calculate_metrics(symbol)
        results_df = pd.DataFrame(results, index=[symbol]).T
        display(results_df)
    elif choice == '2':
        file_path = input("Geben Sie den Pfad zur CSV-Datei ein: ")
        symbols_df = pd.read_csv(file_path)
        all_results = {}
        
        for symbol in symbols_df['Symbol']:
            all_results[symbol] = calculate_metrics(symbol)
        
        results_df = pd.DataFrame(all_results)
        display(results_df)
    else:
        print("Ungültige Auswahl. Bitte wählen Sie 1 oder 2.")
        return

if __name__ == "__main__":
    while True:
        main()
        choice = input("Möchten Sie eine weitere Berechnung durchführen? (1: Ja, 2: Nein): ")
        if choice != '1':
            break