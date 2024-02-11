from bech32 import *
from embit import bip39, bip32
import json
import rest
import pandas as pd
import datetime
import time
import bisect
import pandas as pd


options = {'key': '',
           'secret': '',
           'passphrase': '',}
lnm = rest.LNMarketsRest(**options)

class Notify():
    def __init__(self):
        self.date = format(datetime.datetime.now())
        self.upper_zone = 70000
        self.lower_zone = 20000

    def check_zone(self):
        check_zone = []
        while self.lower_zone <= self.upper_zone:
            check_zone.append(self.lower_zone)
            self.lower_zone += 1000
        return check_zone

    def lineNotify(self, message):
        payload = {'message': message}
        return self._lineNotify(payload)

    def _lineNotify(self, payload, file=None):
        import requests
        url = 'https://notify-api.line.me/api/notify'
        token = ''  # แทนที่ด้วย token ของคุณ
        headers = {'Authorization': 'Bearer ' + token}
        return requests.post(url, headers=headers, data=payload, files=file)
    
    def notify_price(self):
        current_price = trading_instance.current_price()
        total_btc = trading_instance.btc_balance()
        total_usd = trading_instance.synthetic_usd_balance()
        check_zone = self.check_zone()
        if current_price in check_zone:
            self.lineNotify(f" \n Price : {current_price} \n Zone Price :{current_price} \n Total BTC : {total_btc} \n Total USD : {total_usd:.2f} ")
        

    



class Trading():
    def __init__(self):
        self.rebalance_percent = 0.2

    def current_price(self):
        current_price = lnm.futures_get_ticker()
        current_price = json.loads(current_price)
        current_price = int(current_price['lastPrice'])
        return current_price
    def btc_balance(self):
        sat_balance = lnm.get_user()
        sat_balance = json.loads(sat_balance)
        sat_balance = sat_balance['balance']
        sat_balance = float(sat_balance)
        btc_balance = sat_balance/10**8
        return btc_balance
    def synthetic_usd_balance(self):
        synthetic_usd_balance = lnm.get_user()
        synthetic_usd_balance = json.loads(synthetic_usd_balance)
        synthetic_usd_balance = synthetic_usd_balance['synthetic_usd_balance']
        synthetic_usd_balance = float(synthetic_usd_balance)
        return synthetic_usd_balance
    def calculate_amount(self):
        amount_btc_usd = self.current_price() * self.btc_balance()
        amount_btc_usd = float(amount_btc_usd)
        return amount_btc_usd
    def rebalance_mark(self):
        rebalance_mark = float((self.calculate_amount() + self.synthetic_usd_balance())/2)
        return rebalance_mark
    def total_balance(self):
        total_balance = self.calculate_amount()+ self.synthetic_usd_balance()
        return total_balance
    def percent_usd(self):
        percent_usd = (self.synthetic_usd_balance()/self.total_balance())*100
        return percent_usd
    def percent_btc(self):
        percent_btc = (self.calculate_amount() / self.total_balance())*100
        return percent_btc
    def calculate_sell_difference(self):
        #Calculate the difference for selling base on amount in USD/BTC and rebalance mark
        sell_difference = self.calculate_amount() - self.rebalance_mark()
        return sell_difference
    def calculate_buy_difference(self):
        #Calculate the difference for buying base on amount in USD/BTC and rebalance makr
        buy_difference = self.rebalance_mark() - self.calculate_amount()
        #Parameters 
            # self.calculate_amount() : Amount in USD/BTC
            # self.rebalance_mark() : Rebalacen mark value
        #Return
            # Value the difference for buying
        return buy_difference
    def calculat_trading(self):
        calculate_sell_difference = self.calculate_sell_difference()
        calculate_buy_difference = self.calculate_buy_difference()
        calculate_amount = self.calculate_amount()
        rebalance_mark = self.rebalance_mark()
        rebalance_percent = self.rebalance_percent
        

        if calculate_amount > rebalance_mark+(rebalance_mark * rebalance_percent/100):
            #flaot 3point 
            calculate_sell_difference = round(float(calculate_sell_difference),3)
            convert = calculate_sell_difference / self.current_price()
            convert_sat = int(convert*10**8)
            sell = lnm.swap({
            'in_asset': 'BTC',
            'out_asset': 'USD',
            'out_amount': calculate_sell_difference})
            sell = json.loads(sell)
            in_amount = float(sell['in_amount'])
            out_amount = float(sell['out_amount'])
            exchange_rat = (sell['exchange_rate'])*10**8
            notity_instance.lineNotify(f"\nTrading Sell: \n In amount:{in_amount} \n Out Amount: {out_amount} \n Exchange Rat: {exchange_rat:.2f}")

        elif calculate_amount < rebalance_mark - (rebalance_mark * rebalance_percent /100):
            calculate_buy_difference = round(float(calculate_buy_difference),3)
            convert = calculate_buy_difference / self.current_price()
            convert_sat = int(convert*10**8)
            buy = lnm.swap({
            'in_asset': 'USD',
            'out_asset': 'BTC',
            'out_amount': convert_sat})
            buy = json.loads(buy)
            in_amount = float(buy['in_amount'])
            out_amount = float(buy['out_amount'])
            exchange_rat = (in_amount /out_amount)*10**8

            notity_instance.lineNotify(f"\nTrading Buy: \n In amount:{in_amount} \n Out Amount: {out_amount} \n Exchange Rat: {exchange_rat:.2f}")
        else:
            current_time =datetime.datetime.now()
            print('[{}] Date Time'.format(current_time))
            print(f"NO TRADE ACTION WAITING FOR VOLATILITY")





if __name__ == "__main__":
    trading_instance = Trading()
    notity_instance = Notify()
    

    while True:
        try:
            calculat_trading = trading_instance.calculat_trading()
            checklist =notity_instance.notify_price()
        except Exception as e:
            print("ERROR",e)
        
        time.sleep(10)



