import yfinance as yf
import math
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId
import threading

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
    parent.orderType = "STP"
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
    buy_price_options = [
        calculate_buy_price_option1(ticker_symbol),
        calculate_buy_price_option2(ticker_symbol),
        calculate_buy_price_option3(ticker_symbol)
    ]
    buy_price = select_option("Buy Price", buy_price_options)
    
    # Step 3: Calculate the stop loss
    stop_loss_options = [
        calculate_stop_loss_option1(buy_price, ticker_symbol),
        calculate_stop_loss_option2(buy_price, ticker_symbol),
        calculate_stop_loss_option3(buy_price, ticker_symbol)
    ]
    stop_loss = select_option("Stop Loss", stop_loss_options)
    
    # Step 4: Calculate the take profit
    take_profit_options = [
        calculate_take_profit_option1(buy_price, stop_loss[1]),
        calculate_take_profit_option2(buy_price, stop_loss[1]),
        calculate_take_profit_option3(buy_price)
    ]
    take_profit = select_option("Take Profit", take_profit_options)
    
    # Step 5: Calculate the position size/number of shares
    position_size_options = [
        calculate_position_size_option1(buy_price, stop_loss[1], account_balance, position_size, risk_per_trade, total_risk, win_probability),
        calculate_position_size_option2(buy_price, stop_loss[1], account_balance)
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
        bracket = bracketOrder(parentOrderId, "BUY", int(position_size), buy_price, take_profit[1], stop_loss[1])
        
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
    if option_name == "Take Profit":
        return f"Buy Price: {option[0]:.2f}, Take Profit: {option[1]:.2f}, Difference: {(option[1] - option[0]) / option[0] * 100:.2f}%"
    elif option_name == "Position Size":
        return f"Buy Price: {option[0]:.2f}, Position Size: {option[1]:.2f}, Shares: {option[2]:.0f}"
    else:
        return f"Buy Price: {option[0]:.2f}, Stop Loss: {option[1]:.2f}, Difference: {(option[0] - option[1]) / option[0] * 100:.2f}%"

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

def calculate_buy_price_option1(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1d")
    return hist['Close'][0]

def calculate_buy_price_option2(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="5d")
    return hist['Close'].mean()

def calculate_buy_price_option3(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1mo")
    return hist['Close'].mean()

def calculate_stop_loss_option1(buy_price, ticker_symbol):
    return (buy_price, buy_price * 0.95)

def calculate_stop_loss_option2(buy_price, ticker_symbol):
    return (buy_price, buy_price * 0.90)

def calculate_stop_loss_option3(buy_price, ticker_symbol):
    return (buy_price, buy_price * 0.85)

def calculate_take_profit_option1(buy_price, stop_loss):
    return (buy_price, buy_price + (buy_price - stop_loss) * 2)

def calculate_take_profit_option2(buy_price, stop_loss):
    return (buy_price, buy_price + (buy_price - stop_loss) * 3)

def calculate_take_profit_option3(buy_price):
    return (buy_price, buy_price * 1.2)

def calculate_position_size_option1(buy_price, stop_loss, account_balance, position_size, risk_per_trade, total_risk, win_probability):

    """
    Calculates the position size/number of shares using the first option (max loss < 8% of position size).

    Args:
        buy_price (float): The buy price of the stock.
        stop_loss (float): The stop loss price.
        account_balance (float): The account balance in USD.

    Returns:
        A tuple containing the buy price, position size, and the number of shares.
    """
    max_loss = account_balance * 0.08
    position_size_usd = max_loss / (buy_price - stop_loss)
    num_shares = position_size_usd / buy_price
    return (buy_price, position_size_usd, num_shares)

def calculate_position_size_option2(buy_price, stop_loss, account_balance):
    """
    Calculates the position size/number of shares using the second option (max loss < 4% of account balance).

    Args:
        buy_price (float): The buy price of the stock.
        stop_loss (float): The stop loss price.
        account_balance (float): The account balance.

    Returns:
        A tuple containing the buy price, position size, and the number of shares.
    """
    max_loss = account_balance * 0.04
    position_size_usd = max_loss / (buy_price - stop_loss)
    num_shares = position_size_usd / buy_price
    return (buy_price, position_size_usd, num_shares)

# Get user parameters
get_user_parameters()

# Run the stock buy program
stock_buy_program()