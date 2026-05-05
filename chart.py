import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_tradingview_style(df, title, bb_data=None, mfi_data=None, show_bb_width=False, signals=None):
    """
    Creates a TradingView-style chart (Light Mode) with 3 panes:
    1. Price + Bollinger Bands
    2. Bollinger Band Width (Range 0-10)
    3. Money Flow Index
    
    New: Added 'signals' param to plot BUY/SELL labels.
    """
    
    # --- FIX: Prevent crash if dataframe is empty ---
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            xaxis_title="Time",
            yaxis_title="Price",
            template="none",
            height=600,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=0, r=50, t=40, b=0),
            annotations=[
                dict(
                    text="No Data Available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="#787B86")
                )
            ]
        )
        return fig
    # ----------------------------------------------

    # Determine number of rows
    rows = 1
    if bb_data is not None:
        rows += 1 if show_bb_width else 0
    if mfi_data is not None:
        rows += 1

    # Layout heights
    if rows == 3:
        row_heights = [0.5, 0.25, 0.25]
    elif rows == 2:
        row_heights = [0.7, 0.3]
    else:
        row_heights = [1.0]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=row_heights
    )

    # --- TRADINGVIEW LIGHT THEME COLORS ---
    # Candles
    tv_candle_up = "#089981"   # TV Green
    tv_candle_down = "#F23645" # TV Red
    
    # Background & Grid
    tv_bg_color = "#FFFFFF"    # White
    tv_grid_color = "#F0F3FA"  # Very Light Gray/Blue
    tv_text_color = "#131722"  # Dark Blue/Black
    tv_border_color = "#E0E3EB" # Light Gray

    # --- ROW 1: CANDLESTICKS & BOLLINGER BANDS ---
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            increasing_line_color=tv_candle_up, increasing_fillcolor=tv_candle_up,
            decreasing_line_color=tv_candle_down, decreasing_fillcolor=tv_candle_down,
            line_width=1.0, name="Price", hoverinfo="skip"
        ),
        row=1, col=1
    )

    if bb_data:
        fig.add_trace(go.Scatter(x=df.index, y=bb_data['basis'], mode="lines", line=dict(color="#2962FF", width=1), name="BB Basis", hovertemplate="%{y:.2f}<extra>BB Basis</extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bb_data['upper'], mode="lines", line=dict(color="#F23645", width=1), name="BB Upper", hovertemplate="%{y:.2f}<extra>BB Upper</extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bb_data['lower'], mode="lines", line=dict(color="#089981", width=1), fill="tonexty", fillcolor="rgba(33, 150, 243, 0.1)", name="BB Lower", hovertemplate="%{y:.2f}<extra>BB Lower</extra>"), row=1, col=1)

    # --- PLOT SIGNALS (BUY/SELL TEXT) ---
    if signals:
        # Separate BUY and SELL signals
        buy_signals = [s for s in signals if "BUY" in s['signal']]
        sell_signals = [s for s in signals if "SELL" in s['signal']]

        # Plot BUY Signals
        if buy_signals:
            fig.add_trace(go.Scatter(
                x=[s['timestamp'] for s in buy_signals],
                y=[s['entry_price'] * 0.995 for s in buy_signals], # Place slightly below entry price
                mode="text",
                text=["BUY"] * len(buy_signals),
                textfont=dict(color=tv_candle_up, size=12, family="Arial Black"),
                textposition="bottom center",
                hoverinfo="skip",
                showlegend=False
            ), row=1, col=1)

        # Plot SELL Signals
        if sell_signals:
            fig.add_trace(go.Scatter(
                x=[s['timestamp'] for s in sell_signals],
                y=[s['entry_price'] * 1.005 for s in sell_signals], # Place slightly above entry price
                mode="text",
                text=["SELL"] * len(sell_signals),
                textfont=dict(color=tv_candle_down, size=12, family="Arial Black"),
                textposition="top center",
                hoverinfo="skip",
                showlegend=False
            ), row=1, col=1)

    # --- ROW 2: BOLLINGER BAND WIDTH ---
    current_row = 2
    if bb_data is not None and show_bb_width:
        fig.add_trace(
            go.Scatter(
                x=df.index, 
                y=bb_data['width'],
                mode="lines", 
                line=dict(color="#2962FF", width=2),
                name="Bollinger BandWidth",
                hovertemplate="%{y:.4f}<extra>BBW</extra>"
            ),
            row=current_row, col=1
        )
        current_row += 1

    # --- ROW 3: MONEY FLOW INDEX ---
    if mfi_data is not None:
        fig.add_trace(go.Scatter(x=df.index, y=mfi_data, mode="lines", line=dict(color="#7E57C2", width=2), name="MF", hovertemplate="%{y:.2f}<extra>MFI</extra>"), row=current_row, col=1)
        
        # Hlines
        fig.add_hline(y=80, line_color="#787B86", line_width=1, row=current_row, col=1)
        fig.add_hline(y=20, line_color="#787B86", line_width=1, row=current_row, col=1)
        fig.add_hline(y=50, line_color="rgba(120, 123, 134, 0.5)", line_width=1, row=current_row, col=1)
        
        # Background Fill
        fig.add_shape(type="rect", x0=df.index[0], x1=df.index[-1], y0=20, y1=80, fillcolor="rgba(126, 87, 194, 0.1)", line=dict(width=0), layer="below", row=current_row, col=1)

    # --- LAYOUT ---
    fig.update_layout(
        title=dict(text=title, font=dict(color=tv_text_color, size=18)),
        template="none", height=900 if rows == 3 else 850 if rows == 2 else 750,
        showlegend=True, xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=50, t=40, b=0),
        plot_bgcolor=tv_bg_color, paper_bgcolor=tv_bg_color,
        font=dict(color=tv_text_color, family='Roboto, Arial, sans-serif'),
        hovermode="x unified", spikedistance=-1,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255, 255, 255, 0.9)")
    )

    fig.update_xaxes(gridcolor=tv_grid_color, showgrid=True, zeroline=False, linecolor=tv_border_color, linewidth=1, tickformat="%d %b", tickfont=dict(size=11, color=tv_text_color), fixedrange=False, showspikes=True, spikemode="across", spikesnap="cursor")
    fig.update_yaxes(row=1, col=1, gridcolor=tv_grid_color, showgrid=True, zeroline=False, side="right", linecolor=tv_border_color, linewidth=1, tickformat=",.2f", tickfont=dict(size=11, color=tv_text_color), fixedrange=False, showspikes=True, spikemode="across")

    # --- UPDATE Y AXES FOR INDICATORS ---
    
    # Bollinger Band Width Axis
    if rows >= 2 and bb_data is not None and show_bb_width:
        fig.update_yaxes(
            row=2, col=1, 
            gridcolor=tv_grid_color, 
            showgrid=False, 
            zeroline=False, 
            side="right", 
            linecolor=tv_border_color, 
            linewidth=1, 
            range=[0, 10],
            tickfont=dict(size=11, color=tv_text_color), 
            fixedrange=False, 
            title=dict(text="Bollinger BandWidth", font=dict(size=10, color="#2962FF"))
        )

    # MFI Axis
    mfi_row_num = 3
    if rows == 2 and mfi_data is not None: mfi_row_num = 2
    if rows == 3 and mfi_data is not None: mfi_row_num = 3
    
    if mfi_data is not None:
        fig.update_yaxes(
            row=mfi_row_num, col=1, 
            gridcolor=tv_grid_color, 
            showgrid=False, 
            zeroline=False, 
            side="right", 
            linecolor=tv_border_color, 
            linewidth=1, 
            range=[0, 100], 
            tickfont=dict(size=11, color=tv_text_color), 
            fixedrange=False, 
            title=dict(text="Money Flow Index", font=dict(size=10, color="#7E57C2"))
        )

    if len(df) > 0:
        fig.update_layout(xaxis=dict(range=[df.index[-1] - pd.Timedelta(days=14), df.index[-1]]))
    return fig