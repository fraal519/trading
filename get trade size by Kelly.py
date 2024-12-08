import math

def kelly_criterion(depot_size, risk_per_trade, stop_loss_price, take_profit_price, entry_price, num_positions, p):
    """
    Berechnet die optimale Positionsgröße für eine Aktienorder anhand des Kelly-Kriteriums.
    
    :param depot_size: Depotgröße in USD
    :param risk_per_trade: Risiko pro Trade (in Prozent des Depots)
    :param stop_loss_price: Kurs für den Stop-Loss
    :param take_profit_price: Kurs für den Take-Profit
    :param entry_price: Kaufpreis der Aktie
    :param num_positions: Anzahl der offenen Positionen im Depot
    :param p: Wahrscheinlichkeit eines Gewinns (z. B. 0.66 für 66%)
    :return: Optimale Positionsgröße in Anzahl der Aktien
    """
    # Risiko und Belohnung berechnen
    risk = entry_price - stop_loss_price  # Risiko pro Aktie (Preisabweichung zum Stop-Loss)
    reward = take_profit_price - entry_price  # Belohnung pro Aktie (Preisabweichung zum Take-Profit)
    
    # Das Verhältnis der Belohnung zum Risiko (b)
    b = reward / risk
    
    # Die Wahrscheinlichkeit des Verlusts (q)
    q = 1 - p  # Wahrscheinlichkeit eines Verlusts
    
    # Kelly-Formel: f* = (bp - q) / b
    kelly_fraction = (b * p - q) / b
    
    # Gesamtwert des Risikos pro Trade (in USD)
    risk_amount = depot_size * (risk_per_trade / 100)
    
    # Positionsgröße berechnen: Anzahl der Aktien
    position_size = risk_amount / (risk * num_positions)  # Risiko pro Position bei der Anzahl der Positionen im Depot
    
    return position_size


def get_user_input():
    """
    Fragt den Benutzer nach den benötigten Parametern und berechnet die optimale Positionsgröße.
    """
    # Initiale Benutzereingaben zu Depot und Risiko
    depot_size = float(input("Depotgröße in USD: "))
    risk_per_trade = float(input("Risiko pro Trade in Prozent (z.B. 1 für 1%): "))
    num_positions = int(input("Anzahl der offenen Positionen im Depot: "))
    
    # Gewinnwahrscheinlichkeit als Dezimalzahl abfragen (z.B. 0.66 für 66%)
    p = float(input("Geben Sie die Gewinnwahrscheinlichkeit als Dezimalzahl ein (z.B. 0.66 für 66%): "))
    
    return depot_size, risk_per_trade, num_positions, p


def calculate_for_stock(depot_size, risk_per_trade, num_positions, p):
    """
    Berechnet die optimale Positionsgröße für eine Aktie und gibt das Ergebnis aus.
    """
    # Eingabe für Kaufpreis, Stop-Loss und Take-Profit
    entry_price = float(input("Kaufpreis der Aktie: "))
    stop_loss_price = float(input("Stop-Loss Kurs: "))
    take_profit_price = float(input("Take-Profit Kurs: "))
    
    # Berechnung der optimalen Positionsgröße
    position_size = kelly_criterion(depot_size, risk_per_trade, stop_loss_price, take_profit_price, entry_price, num_positions, p)
    
    # Positionsgröße auf ganze Zahlen abrunden
    position_size = math.floor(position_size)
    
    # Berechnung des Kaufwerts (Kaufpreis * Positionsgröße)
    total_investment = position_size * entry_price
    
    # Berechnung des maximal erlaubten Kaufwerts pro Position
    max_investment_per_position = depot_size / num_positions
    
    # Wenn der Kaufwert der Position größer als der maximal erlaubte Wert ist, die Positionsgröße anpassen
    if total_investment > max_investment_per_position:
        position_size = math.floor(max_investment_per_position / entry_price)
        total_investment = position_size * entry_price  # Neuen Kaufwert berechnen
    
    # Ausgabe der optimalen Positionsgröße und des Kaufwerts
    print(f"Optimale Positionsgröße: {position_size} Aktien")
    print(f"Kaufwert der Position: ${total_investment:.2f}")
    print(f"Maximal erlaubter Kaufwert pro Position: ${max_investment_per_position:.2f}")
    

def main():
    """
    Führt den gesamten Berechnungsprozess durch, inklusive mehrfacher Berechnungen für verschiedene Aktien.
    """
    # Fragt die Benutzereingaben für Depot und Risiko ab
    depot_size, risk_per_trade, num_positions, p = get_user_input()
    
    while True:
        # Berechnet die optimale Positionsgröße für eine Aktie
        calculate_for_stock(depot_size, risk_per_trade, num_positions, p)
        
        # Abfrage, ob eine weitere Berechnung durchgeführt werden soll
        another_calculation = input("Möchten Sie eine weitere Berechnung für eine andere Aktie durchführen? (j/n): ").strip().lower()
        
        if another_calculation != 'j':
            print("Berechnungen beendet.")
            break  # Verlasse die Schleife und beende das Programm


# Die Funktion ausführen
main()