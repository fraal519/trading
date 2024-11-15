from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
import datetime
import time
import threading
 
port = 4002  # Geänderter Port
 
class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.orderId = None
        self.data = {}
        self.event = threading.Event()
 
    def nextValidId(self, orderId: OrderId):
        self.orderId = orderId
        self.event.set()  # Set event to signal that we have received the next valid ID
   
    def nextId(self):
        if self.orderId is None:
            self.event.wait()  # Wait for the next valid ID to be received
        self.orderId += 1
        return self.orderId
   
    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        pass
        #print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderReject}")
   
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = []
        self.data[reqId].append(bar)
   
    def historicalDataEnd(self, reqId, start, end):
        #print(f"Historical Data Ended for {reqId}. Started at {start}, ending at {end}")
        self.cancelHistoricalData(reqId)
        self.event.set()
 
    def currentTime(self, time):
        pass
        #print(f"Current Time: {time}")
 
def get_last_and_year_ago_close(symbol):
    app = TestApp()
    app.connect("127.0.0.1", port, 1)
    threading.Thread(target=app.run).start()
    time.sleep(1)
 
    # Wait for next valid ID
    app.event.clear()
    app.reqIds(-1)
    app.event.wait(timeout=10)
 
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
 
    current_date = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
    one_year_ago_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m%d %H:%M:%S")
   
    app.reqId = app.nextId()
    app.reqHistoricalData(app.reqId, contract, current_date, "1 D", "1 day", "TRADES", 1, 1, False, [])
    app.event.clear()
    app.event.wait(timeout=60)
   
    if app.reqId in app.data:
        last_close = app.data[app.reqId][-1].close
    else:
        last_close = None
   
    app.reqId = app.nextId()
    app.reqHistoricalData(app.reqId, contract, one_year_ago_date, "1 D", "1 day", "TRADES", 1, 1, False, [])
    app.event.clear()
    app.event.wait(timeout=60)
   
    if app.reqId in app.data:
        year_ago_close = app.data[app.reqId][-1].close
    else:
        year_ago_close = None
   
    app.disconnect()
   
    return last_close, year_ago_close
 
# Beispielverwendung
symbol = input("Bitte das Tickersymbol eingeben: ")
last_close, year_ago_close = get_last_and_year_ago_close(symbol)
print(f"Letzter Schlusskurs für {symbol}: {last_close}")
print(f"Schlusskurs vor einem Jahr für {symbol}: {year_ago_close}")
 
# Zusätzlicher Code von Interactive Brokers
app = TestApp()
app.connect("127.0.0.1", port, 0)
threading.Thread(target=app.run).start()
time.sleep(1)
 
# Beispiel für die Verwendung der nextId-Methode
#for i in range(0, 5):
#    print(app.nextId())
 
# Abfrage der aktuellen Zeit
#app.reqCurrentTime()