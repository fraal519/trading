import yfinance as yf
import math
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId
import threading
import numpy as np

# Global variables to store the user-provided parameters
account_balance = None
position_size = None
risk_per_trade = None
total_risk = None
win_probability = None

class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self.wrapper)
        self.nextValidOrderId = None
        self.positions = []
        self.openOrders = []

    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId, errorCode, errorString))

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def position(self, account, contract, position, avgCost):
        self.positions.append((account, contract.symbol, position, avgCost))
        print("Position: Account: {}, Symbol: {}, Position: {}, Avg Cost: {}".format(account, contract.symbol, position, avgCost))

    def openOrder(self, orderId, contract, order, orderState):
        self.openOrders.append((orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))
        print("Open Order: OrderId: {}, Symbol: {}, Action: {}, Quantity: {}, Limit Price: {}".format(orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))

def websocket_con(app):
    app.run()

def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract

def bracketOrder(parentOrderId, action, quantity, limitPrice, takeProfitPrice, stopLossPrice):
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = action
    parent.orderType = "STP" if action == "BUY" else "LMT"
    parent.totalQuantity = quantity
    parent.auxPrice = None if parent.orderType == "LMT" else round(limitPrice, 2)
    parent.transmit = False
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False
    
    takeProfit = Order()
    takeProfit.orderId = parentOrderId + 1
    takeProfit.action = "SELL" if action == "BUY" else "BUY"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = round(takeProfitPrice, 2)
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False
    takeProfit.eTradeOnly = False
    takeProfit.firmQuoteOnly = False
    
    stopLoss = Order()
    stopLoss.orderId = parentOrderId + 2
    stopLoss.action = "SELL" if action == "BUY" else "BUY"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = round(stopLossPrice, 2)
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True
    stopLoss.eTradeOnly = False
    stopLoss.firmQuoteOnly = False
    
    return [parent, takeProfit, stopLoss]

def get_user_parameters():
    global account_balance, position_size, risk_per_trade, total_risk, win_probability
    """
    Prompts the user to enter the required parameters for position size calculation.

    Returns:
        tuple: A tuple containing account_balance, position_size, risk_per_trade, total_risk, win_probability
    """
    account_balance = float(input("Enter the account balance in USD: "))
    position_size = float(input("Enter the position size in USD: "))
    risk_per_trade = float(input("Enter the risk per trade in percentage: "))
    total_risk = float(input("Enter the total risk in percentage: "))
    win_probability = float(input("Enter the win probability (as a decimal): "))
    
    return account_balance, position_size, risk_per_trade, total_risk, win_probability

def stock_buy_program():
    """
    A program to assist with stock buying decisions.

    The program consists of the following steps:
    1. Prompt the user to enter the stock ticker symbol.
    2. Calculate the buy price with 3 different variants, and allow the user to select one.
    3. Calculate the stop loss with 3 different variants, and allow the user to select one.
    4. Calculate the take profit with 3 different variants, and allow the user to select one.
    5. Calculate the position size/number of shares with 2 different variants, and allow the user to select one.
    6. Ask the user if they want to place a corresponding bracket order with Interactive Brokers.
    7. Ask the user if they want to perform another calculation.
    """
    
    # Step 1: Get the stock ticker symbol
    ticker_symbol = input("Enter the stock ticker symbol: ")
    
    # Step 2: Calculate the buy price
    stock = yf.Ticker(ticker_symbol)
    current_price = stock.history(period="1d")['Close'].iloc[0]
    prev_day_high = stock.history(period="1d")['High'].iloc[0]
    prev_day_close = stock.history(period="1d")['Close'].iloc[0]
    
    print(f"Current price for {ticker_symbol}: {current_price:.2f}")
    
    buy_price_options = [
        (prev_day_high * 1.005, "STP BUY", (prev_day_high * 1.005 - current_price) / current_price * 100),
        (prev_day_close * 1.01, "STP BUY", (prev_day_close * 1.01 - current_price) / current_price * 100),
        (current_price * 1.005, "BUY LMT", (current_price * 1.005 - current_price) / current_price * 100)
    ]
    buy_price = select_option("Buy Price", buy_price_options)
    
    # Step 3: Calculate the stop loss
    atr = stock.history(period="21d")['Close'].diff().abs().mean()
    sma_21 = stock.history(period="21d")['Close'].mean()
    lowest_low_14d = stock.history(period="14d")['Low'].min()
    
    stop_loss_options = [
        (buy_price[0], buy_price[0] - atr, (buy_price[0] - (buy_price[0] - atr)) / buy_price[0] * 100),
        (buy_price[0], buy_price[0] - sma_21 * 0.975, (buy_price[0] - (buy_price[0] - sma_21 * 0.975)) / buy_price[0] * 100),
        (buy_price[0], lowest_low_14d, (buy_price[0] - lowest_low_14d) / buy_price[0] * 100)
    ]
    stop_loss = select_option("Stop Loss", stop_loss_options)
    
    # Step 4: Calculate the take profit
    take_profit_options = [
        (buy_price[0], buy_price[0] + (buy_price[0] - stop_loss[1]) * 2, (buy_price[0] + (buy_price[0] - stop_loss[1]) * 2 - buy_price[0]) / buy_price[0] * 100),
        (buy_price[0], buy_price[0] + (buy_price[0] - stop_loss[1]) * 3, (buy_price[0] + (buy_price[0] - stop_loss[1]) * 3 - buy_price[0]) / buy_price[0] * 100),
        (buy_price[0], buy_price[0] * 1.2, (buy_price[0] * 1.2 - buy_price[0]) / buy_price[0] * 100)
    ]
    take_profit = select_option("Take Profit", take_profit_options)
    
    # Step 5: Calculate the position size/number of shares
    position_size_options = [
        (buy_price[0], account_balance * 0.08 / (buy_price[0] - stop_loss[1]), account_balance * 0.08 / (buy_price[0] - stop_loss[1]) / buy_price[0]),
        (buy_price[0], account_balance * 0.04 / (buy_price[0] - stop_loss[1]), account_balance * 0.04 / (buy_price[0] - stop_loss[1]) / buy_price[0])
    ]
    selected_position_size = select_option("Position Size", position_size_options)[2]
    
    # Step 6: Ask the user if they want to place a bracket order
    place_bracket_order = int(input("Do you want to place a bracket order with Interactive Brokers? (1 for yes, 2 for no) "))
    if place_bracket_order == 1:
        # Establish connection to Interactive Brokers
        app = TradingApp()
        app.connect("127.0.0.1", 4002, clientId=1)

        # Start a separate daemon thread to execute the websocket connection
        con_thread = threading.Thread(target=websocket_con, args=(app,), daemon=True)
        con_thread.start()
        time.sleep(1)  # some latency added to ensure that the connection is established

        # Wait for next valid order id
        while app.nextValidOrderId is None:
            time.sleep(0.1)

        # Create the contract
        contract = usTechStk(ticker_symbol)
        
        # Get the next valid order ID
        parentOrderId = app.nextValidOrderId
        
        # Create the bracket order
        bracket = bracketOrder(parentOrderId, "BUY", int(selected_position_size), buy_price[0], take_profit[1], stop_loss[1])
        
        # Place the bracket order
        for order in bracket:
            app.placeOrder(order.orderId, contract, order)
            time.sleep(1)  # some latency added to ensure that the order is placed
            app.nextValidOrderId += 1  # increment the order ID
        print("Order successfully placed.")
        
        # Disconnect the client
        app.disconnect()
    
    # Step 7: Ask the user if they want to perform another calculation
    another_calculation = int(input("Do you want to perform another calculation? (1 for yes, 2 for no) "))
    if another_calculation == 1:
        stock_buy_program()

def format_option(option_name, option):
    if option is None:
        return "No data available"
    
    if isinstance(option, (list, tuple)):
        if option_name == "Buy Price":
            return f"Buy Price: {option[0]:.2f}, Order Type: {option[1]}, Difference to Current Price: {option[2]:.2f}%"
        elif option_name == "Take Profit":
            return f"Buy Price: {option[0]:.2f}, Take Profit: {option[1]:.2f}, Difference: {option[2]:.2f}%"
        elif option_name == "Position Size":
            return f"Buy Price: {option[0]:.2f}, Position Size: {option[1]:.2f}, Shares: {option[2]:.0f}"
        else:
            return f"Buy Price: {option[0]:.2f}, Stop Loss: {option[1]:.2f}, Difference: {option[2]:.2f}%"
    else:
        return f"{option_name}: {option:.2f}"

def select_option(option_name, options):
    """
    Prompts the user to select an option from a list of options.

    Args:
        option_name (str): The name of the option being selected.
        options (list): A list of options to choose from.

    Returns:
        The selected option.
    """
    print(f"Select a {option_name} option:")
    for i, option in enumerate(options):
        print(f"{i+1}. {format_option(option_name, option)}")
    
    selected_option = int(input(f"Enter the number of the {option_name} option you want to select: "))
    return options[selected_option - 1]

# Get user parameters
get_user_parameters()

# Run the stock buy program
stock_buy_program()