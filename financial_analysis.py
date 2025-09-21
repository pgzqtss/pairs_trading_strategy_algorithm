import pandas as pd
import numpy as np

class PairTradingFinancialAnalysis:
    def __init__(self, pair, df_whole, window=10, zscore_threshold=2, 
                 margin_init=10000, margin_ratio=0.25, neutral_threshold=1):
        self.stock1, self.stock2 = pair
        self.df_pair = df_whole[[self.stock1, self.stock2]].copy()
        self.window = window
        self.zscore_threshold = zscore_threshold
        self.neutral_threshold = neutral_threshold
        self.margin_init = margin_init
        self.margin_ratio = margin_ratio
        self.margin = margin_init

        self.df_signal_summary = pd.DataFrame()
        self.df_margin = pd.DataFrame()

    def compute_zscore(self):
        ratio = np.log(self.df_pair[self.stock1] / self.df_pair[self.stock2])
        ma = ratio.rolling(window=self.window, min_periods=1).mean().shift(1)
        msd = ratio.rolling(window=self.window, min_periods=1).std().shift(1)
        zscore = (ratio - ma) / msd
        self.df_pair["ratio"] = ratio
        self.df_pair["zscore"] = zscore

    def generate_signals(self):
        z = self.df_pair["zscore"]
        self.df_pair['signal'] = np.select(
            [(z > self.zscore_threshold) & (z < 5),
             (z < -self.zscore_threshold) & (z > -5),
             (z > -self.neutral_threshold) & (z < self.neutral_threshold)],
            [-1, 1, 0], default=np.nan
        )
        self.df_pair['signal'] = self.df_pair['signal'].ffill().fillna(0)

    def summarize_signals(self):
        df = self.df_pair.copy()
        df["signal_group"] = df["signal"].diff().ne(0).cumsum()
        df["time"] = df.index

        self.df_signal_summary = (
            df.groupby("signal_group")
              .agg({
                  "signal": "first",
                  "time": "first",
                  self.stock1: "first",
                  self.stock2: "first"
              })
              .reset_index(drop=True)
        )
        self.df_signal_summary.columns = ["signal", "time_start", "stock1_start_price", "stock2_start_price"]

        # Add end time and prices
        self.df_signal_summary["time_end"] = self.df_signal_summary["time_start"].shift(-1)
        self.df_signal_summary["stock1_final_price"] = self.df_signal_summary["stock1_start_price"].shift(-1)
        self.df_signal_summary["stock2_final_price"] = self.df_signal_summary["stock2_start_price"].shift(-1)

        last_idx = self.df_signal_summary.index[-1]
        self.df_signal_summary.loc[last_idx, "time_end"] = df.index[-1]
        self.df_signal_summary.loc[last_idx, "stock1_final_price"] = df[self.stock1].iloc[-1]
        self.df_signal_summary.loc[last_idx, "stock2_final_price"] = df[self.stock2].iloc[-1]

        # Print each trading signal
        for _, row in self.df_signal_summary.iterrows():
            if row["signal"] == 1:
                print(f"Time: {row['time_start']} - Long {self.stock1}, Short {self.stock2}")
            elif row["signal"] == -1:
                print(f"Time: {row['time_start']} - Short {self.stock1}, Long {self.stock2}")
            elif row["signal"] == 0:
                print(f"Time: {row['time_start']} - Neutral (No position)")


    def calculate_margin(self):
        summary = self.df_signal_summary.copy()
        summary = summary[summary['signal'].isin([1, -1])].reset_index(drop=True)
        margin = self.margin_init
        buying_power = margin / self.margin_ratio
        margins = []

        for _, row in summary.iterrows():
            stock1_units = int((0.5 * buying_power) // row["stock1_start_price"])
            stock2_units = int((0.5 * buying_power) // row["stock2_start_price"])

            # Simplified commission
            commission = 0.001 * (row["stock1_start_price"] * stock1_units + row["stock2_start_price"] * stock2_units)

            if row["signal"] == 1:  # Long stock1, short stock2
                pnl = ((row["stock1_final_price"] - row["stock1_start_price"]) * stock1_units -
                       (row["stock2_final_price"] - row["stock2_start_price"]) * stock2_units)
            else:  # Short stock1, long stock2
                pnl = ((row["stock2_final_price"] - row["stock2_start_price"]) * stock2_units -
                       (row["stock1_final_price"] - row["stock1_start_price"]) * stock1_units)

            margin += pnl - commission
            margins.append(margin)
            buying_power = margin / self.margin_ratio

        summary["margin"] = margins
        self.df_margin = summary
        self.margin = margin

    def run_analysis(self):
        self.compute_zscore()
        self.generate_signals()
        self.summarize_signals()
        self.calculate_margin()
        return {
            "pair": (self.stock1, self.stock2),
            "window": self.window,
            "zscore_threshold": self.zscore_threshold,
            "final_margin": self.margin,
            "df_signal_summary": self.df_signal_summary
        }


def main():
    # Example data for testing
    data = {
        "AAPL": [150, 152, 151, 153, 155, 154, 156, 157, 158, 159],
        "MSFT": [250, 252, 251, 253, 255, 254, 256, 257, 258, 259]
    }
    df = pd.DataFrame(data)

    # Define the pair and parameters
    pair = ("AAPL", "MSFT")
    window = 5
    zscore_threshold = 2
    margin_init = 10000
    margin_ratio = 0.25
    neutral_threshold = 1

    # Initialize and run the analysis
    analysis = PairTradingFinancialAnalysis(
        pair, df, window, zscore_threshold, margin_init, margin_ratio, neutral_threshold
    )
    result = analysis.run_analysis()

    # Print the results
    print("Pair Trading Analysis Summary:")
    print(f"Pair: {result['pair']}")
    print(f"Window: {result['window']}")
    print(f"Z-Score Threshold: {result['zscore_threshold']}")
    print(f"Final Margin: {result['final_margin']:.2f}")

if __name__ == "__main__":
    main()