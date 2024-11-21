from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
import threading
import time


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.orderId = None
        self.connected_event = threading.Event()  # Signal für Verbindungsbereitstellung
    
    def nextValidId(self, orderId: int):
        self.orderId = orderId
        self.connected_event.set()  # Signal, dass nextValidId empfangen wurde
    
    def nextId(self):
        self.orderId += 1
        return self.orderId
    
    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        print(f"Error - reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderReject}")

    def tickPrice(self, reqId, tickType, price, attrib):
        print(f"reqId: {reqId}, tickType: {TickTypeEnum.to_str(tickType)}, price: {price}, attrib: {attrib}")

    def tickSize(self, reqId, tickType, size):
        print(f"TickSize - reqId: {reqId}, tickType: {TickTypeEnum.to_str(tickType)}, size: {size}")


def main():
    app = TestApp()
    port = 4002
    app.connect("127.0.0.1", port, clientId=1)

    # Starten des Hintergrundthreads
    thread = threading.Thread(target=app.run)
    thread.start()

    # Warten auf Verbindung
    if not app.connected_event.wait(timeout=10):
        print("Verbindung konnte nicht hergestellt werden.")
        app.disconnect()
        return

    # Vertrag konfigurieren
    mycontract = Contract()
    mycontract.symbol = "AAPL"
    mycontract.secType = "STK"
    mycontract.exchange = "SMART"
    mycontract.currency = "USD"

    # Marktdaten anfordern
    app.reqMarketDataType(3)  # Realtime-Daten
    app.reqMktData(app.nextId(), mycontract, "", False, False, [])

    # Laufzeit für Abfrage
    time.sleep(10)

    # Verbindung sauber beenden
    app.disconnect()
    thread.join()
    print("Programm beendet.")


if __name__ == "__main__":
    main()