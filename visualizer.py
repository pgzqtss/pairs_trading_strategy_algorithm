import tkinter as tk
from tkinter import ttk
import plotly.graph_objs as go
from plotly.offline import plot
import webbrowser
import tempfile

from config import SP500Data
from financial_analysis import PairTradingFinancialAnalysis

class StockPairVisualizer:
    # Initialize the visualizer with the SP500Data instance
    def __init__(self, sp500_data: SP500Data):
        self.data_handler = sp500_data
        self.root = tk.Tk()
        self.root.title("Stock Pair Visualizer")

        # Dropdown for selecting stock pairs
        self.pair_var = tk.StringVar()
        self.pair_dropdown = ttk.Combobox(self.root, textvariable=self.pair_var)
        self.pair_dropdown['values'] = [
            f"{pair[0]} & {pair[1]}" for pair in self.data_handler.high_corr_pairs
        ]
        self.pair_dropdown.grid(row=0, column=0, padx=10, pady=10)

        # Entry fields for parameters
        self.window_var = tk.StringVar(value="10")
        self.zscore_threshold_var = tk.StringVar(value="2")
        self.neutral_threshold_var = tk.StringVar(value="1")
        self.margin_init_var = tk.StringVar(value="10000")
        self.margin_ratio_var = tk.StringVar(value="0.25")

        ttk.Label(self.root, text="Window:").grid(row=1, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.window_var).grid(row=1, column=1)

        ttk.Label(self.root, text="Z-Score Threshold:").grid(row=2, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.zscore_threshold_var).grid(row=2, column=1)

        ttk.Label(self.root, text="Neutral Threshold:").grid(row=3, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.neutral_threshold_var).grid(row=3, column=1)

        ttk.Label(self.root, text="Initial Margin:").grid(row=4, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.margin_init_var).grid(row=4, column=1)

        ttk.Label(self.root, text="Margin Ratio:").grid(row=5, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.margin_ratio_var).grid(row=5, column=1)

        # Button to plot
        self.plot_button = tk.Button(
            self.root, text="Run Analysis", command=self.run_analysis
        )
        self.plot_button.grid(row=6, column=0, columnspan=2, pady=10)

    # Function to plot the selected stock pair with results
    def plot_selected_pair(self, result):
        selected = self.pair_var.get()
        if not selected:
            return
        stock1, stock2 = selected.split(" & ")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.data_handler.data_1d.index,
            y=self.data_handler.data_1d[stock1],
            name=stock1, yaxis="y1"
        ))
        fig.add_trace(go.Scatter(
            x=self.data_handler.data_1d.index,
            y=self.data_handler.data_1d[stock2],
            name=stock2, yaxis="y2"
        ))

        # Mark trading signals ----------------------------------
        df_signals = result["df_signal_summary"]

        # Separate long and short signals
        long_signals = df_signals[df_signals["signal"] == 1]
        short_signals = df_signals[df_signals["signal"] == -1]

        # Add a single trace for Long signals
        if not long_signals.empty:
            fig.add_trace(go.Scatter(
                x=long_signals["time_start"],
                y=long_signals["stock1_start_price"],
                mode="markers",
                marker=dict(symbol="star", size=12, color="green"),
                name="Long"
            ))

        # Add a single trace for Short signals
        if not short_signals.empty:
            fig.add_trace(go.Scatter(
                x=short_signals["time_start"],
                y=short_signals["stock1_start_price"],
                mode="markers",
                marker=dict(symbol="circle", size=10, color="red"),
                name="Short"
            ))
        
        # Build multi-line result text
        result_text = (
            f"Window: {result['window']}<br>"
            f"Z-Score Threshold: {result['zscore_threshold']}<br>"
            f"Neutral Threshold: {result['neutral_threshold']}<br>"
            f"Initial Margin: {result['margin_init']:.2f}<br>"
            f"Margin Ratio: {result['margin_ratio']:.2f}<br>"
            f"<b>Final Margin: {result['final_margin']:.2f}</b>"
        )

        # Add annotation near the last point of stock1
        fig.add_annotation(
            x=self.data_handler.data_1d.index[-1],
            y=self.data_handler.data_1d[stock1].iloc[-1],
            text=result_text,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="bottom",
            bordercolor="black",
            borderwidth=1,
            bgcolor="white",
            opacity=0.9
        )

        # Layout with extra padding
        fig.update_layout(
            yaxis=dict(title=stock1, tickfont=dict(color="blue")),
            yaxis2=dict(title=stock2, tickfont=dict(color="red"),
                        overlaying="y", side="right"),
            title=dict(
                text="Stock Prices Over Time with Analysis Results",
                x=0.5,
                xanchor="center"
            ),
            xaxis_title="Date",
            margin=dict(t=100, r=200)  # more space for annotation
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            plot(fig, filename=tmpfile.name, auto_open=False)
            webbrowser.open(f"file://{tmpfile.name}")

            
    # Function to run the pair trading analysis
    def run_analysis(self):
        
        selected = self.pair_var.get()
        if not selected:
            print("Please select a stock pair.")
            return

        stock1, stock2 = selected.split(" & ")
        window = int(self.window_var.get())
        zscore_threshold = float(self.zscore_threshold_var.get())
        neutral_threshold = float(self.neutral_threshold_var.get())
        margin_init = float(self.margin_init_var.get())
        margin_ratio = float(self.margin_ratio_var.get())

        # Fetch data for the selected pair
        df = self.data_handler.data_1d[[stock1, stock2]]

        # Run the analysis
        analysis = PairTradingFinancialAnalysis(
            pair=(stock1, stock2),
            df_whole=df,
            window=window,
            zscore_threshold=zscore_threshold,
            margin_init=margin_init,
            margin_ratio=margin_ratio,
            neutral_threshold=neutral_threshold
        )
        result = analysis.run_analysis()

        # Add extra parameters from user input into the result dict
        result["neutral_threshold"] = neutral_threshold
        result["margin_init"] = margin_init
        result["margin_ratio"] = margin_ratio

        # Plot the selected pair with results
        self.plot_selected_pair(result)
        
    # Run the Tkinter main loop
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    sp500_data = SP500Data()
    sp500_data.run_pipeline()

    visualizer = StockPairVisualizer(sp500_data)
    visualizer.run()
