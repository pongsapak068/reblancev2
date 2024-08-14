import ccxt.async_support as ccxt
import time
import pandas as pd
import json
import asyncio
# Configuration
cumulative_btc = 0.0
cumulative_eth = 0.0
average_cost_btc = 0.0
average_cost_eth = 0.0
ratio_A = 0.5
ratio_B = 0.5
symbol = "ETH/BTC"
percentage = 0.003 #3%


exchange = ccxt.deribit({
    'enableRateLimit': True,
    'apiKey': '',
    'secret': '',
})


# Configuration variables
symbol = 'ETH/BTC'
ratio_A = 0.5
ratio_B = 0.5

async def get_price():
    price = await exchange.fetch_ticker(symbol=symbol)
    last_price = price['last']
    return last_price

async def holding():
    btc_holding = await exchange.fetch_balance({'currency': 'BTC'})
    btc_holding = float(btc_holding['free']['BTC'])
    eth_holding = await exchange.fetch_balance({'currency':'ETH'})
    eth_holding = float(eth_holding['free']['ETH'])
    return btc_holding, eth_holding

async def my_trade():
    my_trade = await exchange.fetch_my_trades(symbol)
    last_trade = max(my_trade, key=lambda x: x['timestamp'])
    last_trade = last_trade["price"]
    return last_trade

async def amount_last_price(eth_holding, last_trade):
    amount_price = eth_holding * last_trade
    return amount_price 

async def my_open_orders():
    open_orders = await exchange.fetch_open_orders(symbol=symbol)
    limit_orders = [order for order in open_orders if order['type'] == 'limit']
    limit_order_count = len(limit_orders)
    return limit_order_count

async def sell_order(eth_holding, last_trade, amount_price):
    sell_limit_order = last_trade * (1 + percentage)
    amount_sell_limit = eth_holding * sell_limit_order
    amount_rebalance = abs(amount_sell_limit - amount_price)
    rebalance_ratio_A = amount_rebalance * ratio_A
    convert_to_eth_sell = round(rebalance_ratio_A / sell_limit_order, 4)
    trade_sell_limit = await exchange.create_limit_order(symbol=symbol, side='sell', price=sell_limit_order, amount=convert_to_eth_sell)
    return trade_sell_limit

async def buy_order(eth_holding, last_trade, amount_price):
    buy_limit_order = last_trade * (1 - percentage)
    amount_buy_limit = eth_holding * buy_limit_order
    amount_rebalance_buy = abs(amount_buy_limit - amount_price)
    rebalance_ratio_B = amount_rebalance_buy * ratio_B
    convert_to_eth_buy = round(rebalance_ratio_B / buy_limit_order, 4)
    trade_buy_limit = await exchange.create_limit_order(symbol=symbol, side='buy', price=buy_limit_order, amount=convert_to_eth_buy)
    return trade_buy_limit

async def main_loop():
    while True:
        try:
            last_price = await get_price()
            btc_holding, eth_holding = await holding()
            last_trade = await my_trade()
            amount_price = await amount_last_price(eth_holding, last_trade)
            limit_order_count = await my_open_orders()

            if limit_order_count < 2:
                close_order = await exchange.cancel_all_orders(symbol=symbol)
                print(f"Close order success: {close_order}")
                
                # Sell section
                sell = await sell_order(eth_holding, last_trade, amount_price)
                
                # Buy section
                buy = await buy_order(eth_holding, last_trade, amount_price)
                print(f"Create order success")
            else:
                print(f"Price {symbol} : {last_price}")
                print(f"ETH amount in port: {eth_holding} ETH")
                print(f"BTC amount in port: {btc_holding} BTC")
                print(                 )
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(10)

# Run the main loop
asyncio.run(main_loop())
