import alpaca_backtrader_api
import backtrader as bt
from datetime import datetime
import tools.inject_keys as keys


"""
You have 3 options:
 - backtest (IS_BACKTEST=True, IS_LIVE=False)
 - paper trade (IS_BACKTEST=False, IS_LIVE=False)
 - live trade (IS_BACKTEST=False, IS_LIVE=True)
"""
IS_BACKTEST = True
IS_LIVE = False
ALPACA_API_KEY, ALPACA_SECRET_KEY = keys.inject_keys(IS_BACKTEST, IS_LIVE)

SYMBOL1 = 'AAPL'
SYMBOL2 = 'GOOG'
SYMBOLS = ['AAPL', 'GOOG']


class SmaCross1(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    def log(self, txt, dt=None):
        for i in range(len(SYMBOLS)):
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        self.log("placing trade for {}. target size: {}".format(
            trade.getdataname(),
            trade.size), 1637244044)

    def notify_order(self, order):
        print(f"Order notification. status{order.getstatusname()}.")
        print(f"Order info. status{order.info}.")

    def notify_store(self, msg, *args, **kwargs):
        super().notify_store(msg, *args, **kwargs)
        self.log(msg)

    def stop(self):
        print('==================================================')
        print('Starting Value - %.2f' % self.broker.startingcash)
        print('Ending   Value - %.2f' % self.broker.getvalue())
        print('==================================================')

    def __init__(self):
        self.live_bars = False

        self.crossovers = []
        for i in range(len(SYMBOLS)):
            sma1 = bt.ind.SMA(datas[i], period=self.p.pfast)
            sma2 = bt.ind.SMA(datas[i], period=self.p.pslow)
            self.crossovers.append(bt.ind.CrossOver(sma1, sma2))

        # sma1 = bt.ind.SMA(datas1, period=self.p.pfast)
        # sma2 = bt.ind.SMA(datas1, period=self.p.pslow)
        # self.crossover1 = bt.ind.CrossOver(sma1, sma2)

    def notify_data(self, data, status, *args, **kwargs):
        super().notify_data(data, status, *args, **kwargs)
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if data._getstatusname(status) == "LIVE":
            self.live_bars = True

    def next(self):
        if not self.live_bars and not IS_BACKTEST:
            # only run code if we have live bars (today's bars).
            # ignore if we are backtesting
            return
        # if fast crosses slow to the upside
        for i in range(len(SYMBOLS)):

            if not self.positionsbyname[SYMBOLS[i]].size and self.crossovers[i] > 0:
                self.buy(data=datas[i], size=5)  # enter long

            # in the market & cross to the downside
            if self.positionsbyname[SYMBOLS[i]].size and self.crossovers[i] <= 0:
                self.close(data=datas[i])  # close long position

        # if not self.positionsbyname[SYMBOL2].size and self.crossover1 > 0:
        #     self.buy(data=data1, size=5)  # enter long

        
        # # in the market & cross to the downside
        # if self.positionsbyname[SYMBOL2].size and self.crossover1 <= 0:
        #     self.close(data=data1)  # close long position


if __name__ == '__main__':
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross1)

    store = alpaca_backtrader_api.AlpacaStore(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_SECRET_KEY,
        paper=not IS_LIVE,
    )

    DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
    datas = []

    if not IS_BACKTEST:
        broker = store.getbroker()
        cerebro.setbroker(broker)

        for sym in SYMBOLS:
            data = DataFactory(dataname=sym,
                                historical=False,
                                timeframe=bt.TimeFrame.Ticks,
                                backfill_start=False,
                                data_feed='sip')

            cerebro.adddata(data)
            datas.append(data)
        # data1 = DataFactory(dataname=SYMBOL2,
        #                     historical=False,
        #                     timeframe=bt.TimeFrame.Ticks,
        #                     backfill_start=False,
        #                     data_feed='sip')
        # or just alpaca_backtrader_api.AlpacaBroker()
        
    else:
        for sym in SYMBOLS:

            data = DataFactory(dataname=sym,
                                historical=True,
                                fromdate=datetime(2021, 11, 15),
                                timeframe=bt.TimeFrame.Minutes,
                                data_feed='sip')
            cerebro.adddata(data)
            datas.append(data)
            # data1 = DataFactory(dataname=SYMBOL2,
            #                     historical=True,
            #                     fromdate=datetime(2021, 11, 15),
            #                     timeframe=bt.TimeFrame.Minutes,
            #                     data_feed='sip')

    if IS_BACKTEST:
        # backtrader broker set initial simulated cash
        cerebro.broker.setcash(100000.0)

    # print('Starting Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.run()
    print('Final Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.plot()
