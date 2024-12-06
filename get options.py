import warnings
warnings.filterwarnings('ignore')

from optionlab import run_strategy
import yfinance as yf
import pandas as pd
from IPython.display import display

def find_put_options(symbol):
    # Laden der Optionsdaten für das angegebene Symbol
    stock = yf.Ticker(symbol)
    options = stock.options
    
    # Datenrahmen zur Speicherung der Ergebnisse
    results = pd.DataFrame(columns=['Expiration Date', 'Strike', 'Last Price', 'Delta', 'Days to Expiration'])
    
    # Abrufen der historischen Daten für die letzten fünf Tage
    history = stock.history(period='5d')
    
    # Sicherstellen, dass genügend Daten vorhanden sind
    if len(history) < 2:
        print(f"Nicht genügend historische Daten für {symbol} verfügbar.")
        return results, None, None
    
    # Aktueller Aktienkurs (Schlusskurs des letzten Handelstages)
    stock_price = history['Close'].iloc[-1]
    
    # Schlusskurs des Vortages
    previous_close = history['Close'].iloc[-2]
    
    # Historische Volatilität
    volatility = stock.history(period='1y')['Close'].pct_change().std() * (252 ** 0.5)
    
    # Ausgabe des Schlusskurses des Vortages und der berechneten Volatilität
    print(f"Schlusskurs des Vortages für {symbol}: {previous_close:.2f}")
    print(f"Volatilität für {symbol}: {volatility:.2%}")
    
    # Risikofreier Zinssatz (angenommen 0.045)
    interest_rate = 0.045
    
    # Iteration über alle verfügbaren Optionsverfallsdaten
    for expiration in options:
        # Abrufen der Put-Optionen für das aktuelle Verfallsdatum
        opt = stock.option_chain(expiration)
        puts = opt.puts
        
        # Berechnen der Restlaufzeit in Tagen
        puts['expirationDate'] = pd.to_datetime(expiration)
        puts['daysToExpiration'] = (puts['expirationDate'] - pd.Timestamp.now()).dt.days
        puts['T'] = puts['daysToExpiration'] / 365
        
        # Berechnen der Delta-Werte und Filtern der Put-Optionen
        filtered_puts = []
        for index, row in puts.iterrows():
            strategy = [
                {"type": "stock", "n": 100, "action": "buy"},
                {
                    "type": "put",
                    "strike": row['strike'],
                    "premium": row['lastPrice'],
                    "n": 100,
                    "action": "sell",
                },
            ]
            
            start_date = pd.Timestamp.now()
            target_date = pd.to_datetime(expiration)
            
            if start_date >= target_date:
                continue  # Überspringen, wenn das Startdatum nicht vor dem Zieldatum liegt
            
            out = run_strategy(
                {
                    "stock_price": stock_price,
                    "volatility": volatility,
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "target_date": target_date.strftime('%Y-%m-%d'),
                    "interest_rate": interest_rate,
                    "min_stock": stock_price - 600.0,
                    "max_stock": stock_price + 600.0,
                    "strategy": strategy,
                }
            )
            
            # Verwenden des zweiten Wertes des Deltas
            delta = out.model_dump(exclude={"data", "inputs"}, exclude_none=True).get('delta', [0, 0])[1]
            if row['lastPrice'] > 0.5 and row['daysToExpiration'] <= 10 and delta <= 0.3:
                filtered_puts.append([expiration, row['strike'], row['lastPrice'], delta, row['daysToExpiration']])
        
        # Hinzufügen der gefilterten Optionen zu den Ergebnissen, falls vorhanden
        if filtered_puts:
            filtered_puts_df = pd.DataFrame(filtered_puts, columns=['Expiration Date', 'Strike', 'Last Price', 'Delta', 'Days to Expiration'])
            if not filtered_puts_df.empty:
                results = pd.concat([results, filtered_puts_df.dropna(how='all')], ignore_index=True)
    
    # Rückgabe der Ergebnisse, der Volatilität und des Schlusskurses des Vortages
    return results, volatility, previous_close

def main():
    # Eingabe des Pfads zur CSV-Datei
    csv_file = input("Bitte geben Sie den Pfad zur CSV-Datei ein: ").strip()
    
    # Einlesen der CSV-Datei
    symbols_df = pd.read_csv(csv_file)
    
    # Überprüfung, ob die Spalte 'Symbol' vorhanden ist
    if 'Symbol' not in symbols_df.columns:
        print("Die CSV-Datei muss eine Spalte 'Symbol' enthalten.")
        return
    
    # Iteration über jedes Aktiensymbol in der CSV-Datei
    for symbol in symbols_df['Symbol']:
        print(f"Ermittlung für Symbol: {symbol}")
        
        # Suche nach Put-Optionen und Ausgabe der Volatilität und des Schlusskurses des Vortages
        put_options, volatility, previous_close = find_put_options(symbol)
        
        # Ausgabe der Ergebnisse als Tabelle
        if not put_options.empty:
            display(put_options)
        else:
            print(f"Keine Put-Optionen gefunden, die die Kriterien für Symbol {symbol} erfüllen.")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()