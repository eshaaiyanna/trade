import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame

# Define the path to your CSV file
file_path = 'C:/Users/Admin/Downloads/AAPL.csv'

# Load the CSV file into a DataFrame
data = pd.read_csv(file_path)

# Display the DataFrame
# print(data.head())

# Set Alpaca API credentials and base URL
api_key_id = 'PK9O3AR1MOP7QA3FA0PH'
api_secret_key = '22aU2EpIANoVhuZf9KjVaT9Quh4RFGi0ze3rLInj'
base_url = 'https://paper-api.alpaca.markets'

# Initialize Alpaca API
api = tradeapi.REST(api_key_id, api_secret_key, base_url, api_version='v2')

# Analysis Code
short_window = 50
long_window = 200
data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
data['Long_MA'] = data['Close'].rolling(window=long_window).mean()

# Create signals for Moving Average Crossover Strategy
data['MASignal'] = 0
data.loc[data['Short_MA'] > data['Long_MA'], 'MASignal'] = 1

macd_short_ema = 12
macd_long_ema = 26
macd_signal_ema = 9

data['Short_EMA'] = data['Close'].ewm(span=macd_short_ema, adjust=False).mean()
data['Long_EMA'] = data['Close'].ewm(span=macd_long_ema, adjust=False).mean()
data['MACD_Line'] = data['Short_EMA'] - data['Long_EMA']
data['Signal_Line'] = data['MACD_Line'].ewm(span=macd_signal_ema, adjust=False).mean()

mean_window = 20

data['Mean'] = data['Close'].rolling(window=mean_window).mean()
data['Std'] = data['Close'].rolling(window=mean_window).std()
data['Z-Score'] = (data['Close'] - data['Mean']) / data['Std']
data['Mean_Rev_Buy'] = data['Z-Score'] < -2  # Buy signal
data['Mean_Rev_Sell'] = data['Z-Score'] > 2  # Sell signal

data['MA_Signal'] = 0
data.loc[data['Short_MA'] > data['Long_MA'], 'MA_Signal'] = 1  # Buy
data.loc[data['Short_MA'] < data['Long_MA'], 'MA_Signal'] = -1  # Sell

data['MACD_Signal'] = 0
data.loc[data['MACD_Line'] > data['Signal_Line'], 'MACD_Signal'] = 1  # Buy
data.loc[data['MACD_Line'] < data['Signal_Line'], 'MACD_Signal'] = -1  # Sell

# Initialize Combined_Signal to 0
data['Combined_Signal'] = 0

# Update Combined_Signal to 1 for buy signals
data.loc[
    (data['Mean_Rev_Buy']) | (data['MA_Signal'] == 1) | (data['MACD_Signal'] == 1),
    'Combined_Signal'
] = 1

# Update Combined_Signal to -1 for sell signals
data.loc[
    (data['Mean_Rev_Sell']) | (data['MA_Signal'] == -1) | (data['MACD_Signal'] == -1),
    'Combined_Signal'
] = -1

print(data[['Date', 'Mean_Rev_Buy', 'Mean_Rev_Sell', 'MA_Signal', 'MACD_Signal', 'Combined_Signal']].head(100))

# Example trading decision
def place_order(symbol, qty, side, order_type='limit', price=None):
    try:
        # Define order type and parameters
        if order_type == 'market':
            order = api.submit_order(
                symbol='AAPL',
                qty=1,
                side='buy',
                type='market',
                time_in_force='gtc'  # Good 'til canceled
            )
        elif order_type == '500' and price is not None:
            order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='limit',
                limit_price=price,
                time_in_force='gtc'
            )
        else:
            raise ValueError("Invalid order type or missing price for limit order")

        print(f"Order placed: {side} {qty} shares of {symbol} at {price if price else 'market'}")
    except tradeapi.rest.APIError as e:
        error_message = e.body if hasattr(e, 'body') else str(e)
        print(f"Error placing order: {error_message}")


def execute_trades(data):
    for index, row in data.iterrows():
        try:
            symbol = row.get('symbol', 'AAPL')
            qty = 1
            side = 'buy' if row['Combined_Signal'] == 1 else 'sell' if row['Combined_Signal'] == -1 else None
            if side:
                place_order(symbol=symbol, qty=qty, side=side)
        except Exception as e:
            print(f"Error processing row {index}: {e}")

    print("Trade execution finished.")

# Run the trading logic
execute_trades(data)
