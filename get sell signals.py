from ib_insync import IB, Contract
import pandas as pd
from IPython.display import display

# Verbindung zur TWS herstellen
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# Portfolio-Daten abrufen
def fetch_portfolio_data():
    portfolio = ib.portfolio()
    portfolio_data = []
    for position in portfolio:
        data = {
            "Aktie": position.contract.symbol,
            "SecType": position.contract.secType,
            "Exchange": position.contract.exchange,
            "Währung": position.contract.currency,
            "Menge": position.position,
            "Marktpreis": position.marketPrice,
            "Marktwert": position.marketValue,
            "Kaufpreis": position.averageCost,
            "Unrealisierter Gewinn/Verlust": position.unrealizedPNL,
            "Realisierter Gewinn/Verlust": position.realizedPNL,
            "Konto": position.account
        }
        portfolio_data.append(data)
    return portfolio_data

# Portfolio abrufen und in ein vollständiges DataFrame umwandeln
portfolio_list = fetch_portfolio_data()
portfolio_df = pd.DataFrame(portfolio_list)

# Nur Aktien (SecType = STK) berücksichtigen
stock_df = portfolio_df[portfolio_df["SecType"] == "STK"].copy()

# Alle Portfolio-Daten für Aktien anzeigen
print("Portfolio-Daten für Aktien (SecType = STK):")
display(stock_df)
print("-" * 50)

# Verkaufssignale prüfen
def calculate_sma(symbol, contract):
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr='30 D',
        barSizeSetting='1 day',
        whatToShow='MIDPOINT',
        useRTH=True
    )
    if bars:
        df = pd.DataFrame(bars)
        df['SMA_10'] = df['close'].rolling(window=10).mean()
        return df.iloc[-1]['SMA_10'], df.iloc[-1]['close']
    else:
        return None, None

def check_sell_signals(row):
    signals = []
    # Beispiel-Kriterium 1: Kurs 25% höher als durchschnittlicher Kaufpreis
    if row["Marktpreis"] > row["Kaufpreis"] * 1.25:
        signals.append("Kurs 25% über Kaufpreis")
    # Beispiel-Kriterium 2: Kurs 7% niedriger als durchschnittlicher Kaufpreis
    if row["Marktpreis"] < row["Kaufpreis"] * 0.93:
        signals.append("Kurs 7% unter Kaufpreis")
    # Kriterium 3: Kurs durchbricht 10-Tages-SMA von oben
    symbol = row["Aktie"]
    contract = Contract(symbol=symbol, secType="STK", exchange="SMART", currency=row["Währung"])
    sma_10, latest_price = calculate_sma(symbol, contract)
    if sma_10 and latest_price and latest_price < sma_10 and row["Marktpreis"] > sma_10:
        signals.append("Kurs durchbricht 10-Tages-SMA von oben")
    return ", ".join(signals) if signals else "Keine"

# Verkaufssignale hinzufügen
stock_df["Verkaufssignal"] = stock_df.apply(check_sell_signals, axis=1)

# Relevante Spalten für Verkaufssignale-Tabelle auswählen
columns = ["Aktie", "Menge", "Marktpreis", "Kaufpreis", "Unrealisierter Gewinn/Verlust", "Verkaufssignal"]
result_table = stock_df[columns]

# Tabelle mit Verkaufssignalen anzeigen
print("Kompakte Tabelle mit Verkaufssignalen (nur Aktien):")
display(result_table)

# Verbindung trennen
ib.disconnect()