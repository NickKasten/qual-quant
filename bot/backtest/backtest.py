import pandas as pd
from backtesting import Backtest, Strategy
from bot.strategy.signals import generate_signals

class SMA_RSI_Strategy(Strategy):
    def init(self):
        self.signals = None

    def next(self):
        if self.signals is None:
            data = pd.DataFrame({
                'date': self.data.index,
                'close': self.data.Close
            })
            self.signals = generate_signals(data)

        if self.signals and self.signals['signal'] == 1:
            self.buy()
        elif self.signals and self.signals['signal'] == -1:
            self.sell()

def run_backtest(data: pd.DataFrame) -> dict:
    """
    Run backtest on the given data using the SMA/RSI strategy.
    """
    bt = Backtest(data, SMA_RSI_Strategy, cash=10000, commission=.002)
    stats = bt.run()
    return stats 