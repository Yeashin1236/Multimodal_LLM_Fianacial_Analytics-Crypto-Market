import streamlit as st
import pandas as pd
import json
import time
import numpy as np
import yfinance as yf

# --- IMPORT LOCAL MODULES ---
import data
import chart
import technical_analysis
import ai_analysis
import judge_llama_analysis
import chatbot

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Financial Analytics Dashboard – Crypto Markets", layout="wide")

# ----------------- SYNC LOGIC (MUST BE AT TOP) -----------------
if 'pending_symbol' in st.session_state:
    st.session_state['symbol'] = st.session_state['pending_symbol']
    del st.session_state['pending_symbol']

if 'pending_timeframe' in st.session_state:
    st.session_state['timeframe'] = st.session_state['pending_timeframe']
    del st.session_state['pending_timeframe']

# ----------------- SESSION STATE INIT -----------------
if 'symbol' not in st.session_state:
    st.session_state['symbol'] = "BTC-USD"
if 'timeframe' not in st.session_state:
    st.session_state['timeframe'] = "1h"
if 'show_bb' not in st.session_state:
    st.session_state['show_bb'] = True
if 'show_bb_width' not in st.session_state:
    st.session_state['show_bb_width'] = True
if 'show_mfi' not in st.session_state:
    st.session_state['show_mfi'] = True

# --- UPDATED DEFAULTS TO 1:1 RATIO ---
if 'tp_pct' not in st.session_state:
    st.session_state['tp_pct'] = 1.0
if 'sl_pct' not in st.session_state:
    st.session_state['sl_pct'] = 1.0
    
if 'ai_result' not in st.session_state:
    st.session_state['ai_result'] = None
if 'judge_result' not in st.session_state:
    st.session_state['judge_result'] = None
if 'signal_history' not in st.session_state:
    st.session_state['signal_history'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'last_activity_time' not in st.session_state:
    st.session_state['last_activity_time'] = time.time()

# ----------------- AUTO-CLEAR LOGIC (5 Minutes) -----------------
current_time = time.time()
if current_time - st.session_state['last_activity_time'] > 60:
    st.session_state['messages'] = []
    st.session_state['last_activity_time'] = current_time

if not st.session_state['messages']:
    st.session_state['messages'] = [{'role': 'assistant', 'content': "Hi, I am Fin AI, How can I help you?"}]

st.title("Financial Analytics Dashboard – Crypto Markets")

# ----------------- SIGNAL SCANNER & BACKTEST LOGIC -----------------
def get_real_signal_history(df, bb_data, mfi_data, tp_pct, sl_pct, limit=20):
    signals = []
    if df.empty or bb_data is None or mfi_data is None:
        return signals
    analysis_df = pd.DataFrame(index=df.index)
    analysis_df['Close'] = df['Close']
    analysis_df['Open'] = df['Open']
    analysis_df['High'] = df['High']
    analysis_df['Low'] = df['Low']
    analysis_df['SMA_20'] = df['Close'].rolling(window=20).mean()
    analysis_df['BB_Width'] = bb_data['width']
    analysis_df['MFI'] = mfi_data
    analysis_df.dropna(inplace=True)
    
    if analysis_df.empty:
        return []
        
    price_data = analysis_df[['Open', 'High', 'Low', 'Close']].values
    len_data = len(analysis_df)
    
    for i in range(1, len_data - 1): 
        curr = analysis_df.iloc[i]
        prev = analysis_df.iloc[i-1]
        price_above_sma = curr['Close'] > curr['SMA_20']
        price_below_sma = curr['Close'] < curr['SMA_20']
        is_green = curr['Close'] > curr['Open']
        is_red = curr['Close'] < curr['Open']
        bb_expanding = curr['BB_Width'] > prev['BB_Width']
        mfi_bullish = curr['MFI'] > 50
        mfi_bearish = curr['MFI'] < 50
        signal_type = None
        
        if price_above_sma and is_green and bb_expanding and mfi_bullish:
            signal_type = "BUY LONG"
        elif price_below_sma and is_red and bb_expanding and mfi_bearish:
            signal_type = "SELL SHORT"
            
        if signal_type:
            entry_price = curr['Close']
            outcome = "PENDING"
            exit_price = 0.0
            look_ahead_limit = min(i + 100, len_data - 1)
            
            for j in range(i + 1, look_ahead_limit + 1):
                future_high = price_data[j, 1]
                future_low = price_data[j, 2]
                
                if signal_type == "BUY LONG":
                    target_price = entry_price * (1 + tp_pct / 100)
                    stop_price = entry_price * (1 - sl_pct / 100)
                    if future_high >= target_price:
                        outcome = "WIN"; exit_price = target_price; break
                    if future_low <= stop_price:
                        outcome = "LOSS"; exit_price = stop_price; break
                elif signal_type == "SELL SHORT":
                    target_price = entry_price * (1 - tp_pct / 100)
                    stop_price = entry_price * (1 + sl_pct / 100)
                    if future_low <= target_price:
                        outcome = "WIN"; exit_price = target_price; break
                    if future_high >= stop_price:
                        outcome = "LOSS"; exit_price = stop_price; break
            
            if outcome in ["WIN", "LOSS"]:
                signals.append({
                    "timestamp": curr.name.strftime('%Y-%m-%d %H:%M'),
                    "entry_price": float(entry_price),
                    "signal": signal_type,
                    "outcome": outcome,
                    "exit_price": float(exit_price)
                })
    return signals[::-1][:limit]

# ----------------- INDEPENDENT BACKEND ENGINE -----------------
def run_backend_analysis(symbol, timeframe, tp, sl):
    yf_interval = timeframe.lower().replace("1d", "1d")
    
    df = data.fetch_data(symbol, yf_interval)
    if df.empty: return None
    
    bb_data = technical_analysis.get_bollinger_bands(df, length=20, std_dev=2.0, ma_type="SMA")
    mfi_data = technical_analysis.get_mfi(df, period=20)
    
    real_signals = get_real_signal_history(df, bb_data, mfi_data, tp, sl, limit=365)
    
    current_analysis = ai_analysis.analyze_chart_with_ai(
        df, bb_data, mfi_data, coin_name=symbol, timeframe=timeframe
    )
    
    judge_result = judge_llama_analysis.judge_llama_analysis(
        backtest_history_list=real_signals, 
        latest_ai_analysis_text=current_analysis,
        coin_name=symbol,
        timeframe=timeframe
    )
    
    st.session_state['ai_result'] = current_analysis
    st.session_state['judge_result'] = judge_result
    st.session_state['signal_history'] = real_signals
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "ai": current_analysis,
        "judge": judge_result,
        "signals": real_signals,
        "current_price": float(df.iloc[-1]['Close'])
    }

# ----------------- SIDEBAR -----------------
with st.sidebar:
    
    st.markdown("""
    <div style="background-color:#F0F2F6; padding:10px; border-radius:10px; margin-bottom:10px;">
        <h3 style="color:#1E1E1E; margin:0px; text-align:center;">AI Assistant</h3>
    </div>
    """, unsafe_allow_html=True)
    
    quick_prompt = None

    with st.expander("Quick Professional Queries"):
        # --- PREDETERMINED QUESTIONS ---
        
        if st.button("What are the baseline strategies or rules?", use_container_width=True):
            quick_prompt = "What are the baseline strategies or rules?"
            
        if st.button("Does the system allow users to modify the strategy?", use_container_width=True):
            quick_prompt = "Does the system allow users to modify the strategy?"
            
        if st.button("Beginner’s Guide: What do these metrics mean?", use_container_width=True):
            quick_prompt = "What do these metrics mean?"
            
        # --- NEW QUESTIONS ADDED ---
        if st.button("What kind of business problems does this solve?", use_container_width=True):
            quick_prompt = "What kind of business problems does it solve?"
            
        if st.button("Is this project aligned with business analytics?", use_container_width=True):
            quick_prompt = "Is this project aligned with business analytics?"

    chat_container = st.container(height=300)
    with chat_container:
        for message in st.session_state['messages']:
            with st.chat_message(message['role']):
                st.markdown(message['content'])

    prompt = quick_prompt
    
    if not prompt:
        prompt = st.chat_input("Type your question...")

    if prompt:
        st.session_state['last_activity_time'] = time.time()
        st.session_state['messages'].append({'role': 'user', 'content': prompt})
        
        # --- HARDCODED Q&A LOGIC ---
        prompt_lower = prompt.lower()
        response_text = None
        
        # Question 1: Baseline Strategy
        if "baseline strategy" in prompt_lower or "strategy rules" in prompt_lower:
            response_text = """
**What are the Baseline Strategy or Rules?**

The baseline trading strategy implemented in the system is a rule-based technical analysis framework that combines trend, volatility, and momentum indicators to generate directional signals. The logic is fully deterministic and defined as follows:

**Core Indicators Used**
* **Simple Moving Average (SMA 20)** → Trend direction
* **Bollinger Band Width** → Volatility expansion
* **Money Flow Index (MFI 20)** → Momentum & volume strength

**Signal Generation Rules**

**Buy (Long) Signal**
A BUY LONG signal is generated when all of the following conditions are satisfied:
1. Price is above SMA (20) → indicates bullish trend
2. Current candle is bullish (Close > Open)
3. Bollinger Band Width is expanding → volatility breakout
4. MFI > 50 → bullish momentum confirmation

**Sell (Short) Signal**
A SELL SHORT signal is generated when:
1. Price is below SMA (20) → bearish trend
2. Current candle is bearish (Close < Open)
3. Bollinger Band Width is expanding
4. MFI < 50 → bearish momentum confirmation

**Trade Execution Logic**
* **Entry Price:** Closing price of the signal candle
* **Exit Conditions:**
    * Take Profit (TP) → defined as a % gain from entry
    * Stop Loss (SL) → defined as a % loss from entry

The system scans forward (up to 100 candles) to determine whether:
* TP is hit → WIN
* SL is hit → LOSS

**Performance Evaluation**
* Signals are backtested over historical data
* Key metrics: Total signals, Win rate, Wins vs losses, Risk/Reward ratio
"""

        # Question 2: Modify Strategy
        elif "modify strategy" in prompt_lower or "modify the strategy" in prompt_lower:
            response_text = """
**Does the System Allow Users to Modify the Strategy?**

Yes — the system supports partial user-driven customization, primarily focused on risk management and visualization, while keeping the core signal logic fixed.

**User-Controlled Parameters**

**1. Risk Management Controls**
Users can dynamically adjust:
* Take Profit (%)
* Stop Loss (%)

These directly impact:
* Trade outcomes (win/loss)
* Risk/Reward ratio
* Backtest performance metrics

**2. Indicator Visibility Controls**
Users can toggle:
* Bollinger Bands
* Bollinger Band Width
* Money Flow Index (MFI)

This allows flexible chart interpretation without altering logic.

**3. Asset & Timeframe Selection**
Users can modify:
* Cryptocurrency (BTC, ETH, SOL, etc.)
* Timeframe (15m, 1h, 4h, 1D)

This changes:
* Market context
* Signal frequency
* Strategy sensitivity

**Current Limitation**
While users can adjust inputs, the core strategy rules (entry conditions) are:
* Predefined
* Not editable via UI
"""
        
        # Question 3: Beginner's Guide
        elif "metrics mean" in prompt_lower or "beginner's guide" in prompt_lower:
            response_text = """
**Beginner's Guide: What do these metrics mean?**

Here is a simple explanation of the terms used in the Multi-Model Analysis tables:

**Analysis Model (Left Table):**
* **Trend**: The general direction of the price.
    * *Uptrend* = Prices are generally rising (Good for Buying).
    * *Downtrend* = Prices are generally falling (Good for Selling).
* **Volatility**: How fast and how much the price is moving.
    * *Expanding* = Big price swings happening (High energy).
    * *Contracting* = Market is quiet/calm.
* **Momentum**: The strength behind the price movement.
    * *Bullish* = Buyers are in control.
    * *Bearish* = Sellers are in control.
* **Signal**: The recommended action based on technical rules.
    * *NO TRADE* = Conditions are not met, it is safer to wait.

**Validation Model (Right Table):**
* **Market Structure**: The overall "health" or pattern of the market.
* **Risk Profile**: How risky the current market conditions are.
    * *High Risk* = Prices might move unpredictably.
* **Win Rate**: Based on historical data, the percentage of times this strategy would have made money.
* **Risk/Reward**: Compares potential profit to potential loss.
    * *1:1.00* means you risk $1 to potentially make $1.
"""
        
        # Question 4: Business Problems Solved (NEW)
        elif "business problem" in prompt_lower or "problems it solve" in prompt_lower:
            response_text = """
**What kind of business problems does it solve?**

According to the research context, this system addresses three critical limitations in current cryptocurrency trading systems for retail investors:

**1. The Interpretability Gap**
*   **Problem:** Many retail platforms rely heavily on raw technical indicators. Non-expert traders often struggle to interpret complex parameters or synthesize conflicting data.
*   **Solution:** This system uses LLMs to translate rigid numerical signals into human-readable explanations, lowering the barrier to entry for non-experts.

**2. "Black Box" AI Trust Issues**
*   **Problem:** Existing AI-driven financial systems often act as "black boxes," offering predictions without transparency. Users cannot verify the logic behind the AI's decision.
*   **Solution:** The system implements a "Hybrid Quantitative-Explainable Framework." It integrates deterministic trading logic with AI interpretation, ensuring the signals are grounded in proven technical analysis rules rather than just opaque AI predictions.

**3. Lack of Validation Mechanisms**
*   **Problem:** Most tools provide direct outputs based on single-model inferences, lacking a "checks-and-balances" system. This can lead to overconfidence in false signals.
*   **Solution:** The system introduces a dual-layer architecture (Analyst Model + Judge Model). The "Judge" validates the signal reliability against historical performance before presenting it to the user, reducing the risk of erroneous advice.
"""

        # Question 5: Business Analytics Alignment (NEW)
        elif "business analytics" in prompt_lower or "align with business" in prompt_lower:
            response_text = """
**Is this project aligned with business analytics?**

Yes, this project is fully aligned with the core principles of **Business Analytics and Big Data Systems**.

**1. Design Science Research (DSR) Approach**
The project follows the DSR methodology, a standard framework in Information Systems research. It focuses on solving identified organizational problems (retail investor decision-making) by creating innovative IT artifacts (the AI-driven dashboard).

**2. Mixed-Method Data Processing**
Business Analytics involves turning data into insights. This project uses a **"Quant-to-Qual" transformation pipeline**:
*   **Quantitative Input:** Processing vast amounts of high-frequency market data (Price, Volume).
*   **Qualitative Output:** Using AI to generate strategic business insights (Buy/Sell recommendations with reasoning).

**3. Decision Support System (DSS)**
Unlike basic reporting tools, this is a prescriptive analytics system. It doesn't just show what happened (Descriptive) or what will happen (Predictive); it recommends specific actions (Prescriptive) and provides the rationale, which is the hallmark of advanced business analytics.

**4. Value Creation**
The goal is to enhance "Individual Investment Decisions," turning raw big data into actionable value for the end-user, bridging the gap between technical complexity and business utility.
"""

        # If hardcoded response found, add it and rerun
        if response_text:
            st.session_state['messages'].append({'role': 'assistant', 'content': response_text})
            st.rerun()
        
        # --- EXISTING DYNAMIC LOGIC ---
        else:
            with st.spinner("Analyzing..."):
                detected_symbol = None
                detected_timeframe = None
                
                coin_map = {"bitcoin": "BTC-USD", "btc": "BTC-USD", "ethereum": "ETH-USD", "eth": "ETH-USD",
                            "solana": "SOL-USD", "sol": "SOL-USD", "bnb": "BNB-USD", "binance": "BNB-USD",
                            "xrp": "XRP-USD", "ripple": "XRP-USD"}
                prompt_lower = prompt.lower()
                for name, ticker in coin_map.items():
                    if name in prompt_lower:
                        detected_symbol = ticker
                        break
                
                valid_tfs = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1D"}
                for tf_key, tf_val in valid_tfs.items():
                    if tf_key in prompt_lower:
                        detected_timeframe = tf_val
                        break
                
                if detected_symbol:
                    st.session_state['pending_symbol'] = detected_symbol
                
                if detected_timeframe:
                    st.session_state['pending_timeframe'] = detected_timeframe
                    
                current_sym = detected_symbol if detected_symbol else st.session_state['symbol']
                current_tf = detected_timeframe if detected_timeframe else st.session_state['timeframe']
                current_tp = st.session_state['tp_pct']
                current_sl = st.session_state['sl_pct']
                
                context = run_backend_analysis(current_sym, current_tf, current_tp, current_sl)
                
                if context:
                    response_text = chatbot.get_chat_response(prompt, context)
                    simple_message = {'role': 'assistant', 'content': response_text}
                    st.session_state['messages'].append(simple_message)
                else:
                    st.session_state['messages'].append({'role': 'assistant', 'content': "Error fetching data."})
            
            st.rerun()

    st.markdown("---")
    with st.expander("Indicator Framework", expanded=False):
        st.header("Fianancial Asset Analytics Toolkit")
        st.selectbox("Select Cryptocurrency", ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"], key='symbol')
        st.radio("Select Timeframe", ["15m", "1h", "4h", "1D"], horizontal=True, key='timeframe')
        
        st.markdown("---")
        st.header("Technical Analysis Indicators")
        st.checkbox("Bollinger Bands (BB)", key='show_bb')
        st.checkbox("Bollinger Band Width (BBW)", key='show_bb_width')
        st.checkbox("Money Flow Index (MFI)", key='show_mfi')

        st.markdown("---")
        st.header("Strategy Backtesting Parameters")
        st.caption("Used to calculate Win/Loss ratio")
        
        st.number_input("Take Profit (%)", value=1.0, min_value=0.1, step=0.1, key='tp_pct')
        st.number_input("Stop Loss (%)", value=1.0, min_value=0.1, step=0.1, key='sl_pct')

        st.markdown("") 
        if st.button("Analyze Now", type="primary", use_container_width=True):
            with st.spinner("Running Analysis..."):
                run_backend_analysis(st.session_state['symbol'], st.session_state['timeframe'], st.session_state['tp_pct'], st.session_state['sl_pct'])
                st.rerun()

# ----------------- LOAD DATA FOR MAIN DASHBOARD -----------------
current_symbol = st.session_state['symbol']
current_timeframe = st.session_state['timeframe']
yf_interval = current_timeframe.replace("1D", "1d").lower() 

df_chart = data.fetch_data(current_symbol, yf_interval)
df_daily = data.fetch_data(current_symbol, "1d")

# ----------------- CURRENT PRICE -----------------
if not df_daily.empty and len(df_daily) >= 2:
    last = df_daily.iloc[-1]
    prev = df_daily.iloc[-2]
    price_change = last["Close"] - prev["Close"]
    percent_change = (price_change / prev["Close"]) * 100
    volume_b = last["Volume"] / 1_000_000_000
    st.metric(label=f"{current_symbol} Current Price", value=f"{last['Close']:,.2f}", delta=f"{percent_change:+.2f}%")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Open (24h)", f"{last['Open']:,.2f}")
    col2.metric("Close (24h)", f"{last['Close']:,.2f}")
    col3.metric("High (24h)", f"{last['High']:,.2f}")
    col4.metric("Low (24h)", f"{last['Low']:,.2f}")
    col5.metric("Volume (B)", f"{volume_b:,.2f}")

st.markdown("---")

# ----------------- INDICATORS -----------------
bb_data = None
mfi_data = None

if not df_chart.empty:
    if st.session_state['show_bb']:
        bb_data = technical_analysis.get_bollinger_bands(df_chart, length=20, std_dev=2.0, ma_type="SMA")
    if st.session_state['show_mfi']:
        mfi_data = technical_analysis.get_mfi(df_chart, period=20)

    fig = chart.plot_tradingview_style(
        df_chart, 
        f"{current_symbol} - {current_timeframe}", 
        bb_data=bb_data, 
        mfi_data=mfi_data, 
        show_bb_width=st.session_state['show_bb_width'],
        signals=st.session_state.get('signal_history', []) 
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
else:
    st.warning("No chart data available. Please check your network connection.")

# ----------------- AI TECHNICAL ANALYSIS -----------------
st.markdown("---")
st.markdown("## Multi-Model Analysis")

if st.session_state['ai_result']:
    try:
        ai_json = json.loads(st.session_state['ai_result'])
        judge_json = json.loads(st.session_state['judge_result'])

        col_ai, col_judge = st.columns(2)

        with col_ai:
            st.markdown("### Analysis Model")
            trend = ai_json.get("analysis", {}).get("trend", "N/A")
            volatility = ai_json.get("analysis", {}).get("volatility", "N/A")
            momentum = ai_json.get("analysis", {}).get("momentum", "N/A")
            action = ai_json.get("decision", {}).get("action", "N/A")
            reasoning = ai_json.get("decision", {}).get("reasoning", "N/A")
            
            if ai_json.get("error"):
                st.error(f"AI Error: {ai_json['error']}")
                reasoning = ai_json['error']

            df_ai = pd.DataFrame({
                "Metric": ["Trend", "Volatility", "Momentum", "Signal", "Reason"],
                "Value": [trend, volatility, momentum, action, reasoning]
            })
            st.table(df_ai)

        with col_judge:
            st.markdown("### Validation Model")
            structure = judge_json.get("market_status", {}).get("structure", "N/A")
            risk = judge_json.get("market_status", {}).get("risk_profile", "N/A")
            advice = judge_json.get("action_plan", {}).get("primary_advice", "N/A")

            history_data = st.session_state.get("signal_history", [])
            if history_data:
                df_hist = pd.DataFrame(history_data)
                wins = len(df_hist[df_hist['outcome'] == 'WIN'])
                losses = len(df_hist[df_hist['outcome'] == 'LOSS'])
                win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
            else:
                win_rate = 0
                df_hist = pd.DataFrame()

            tp = st.session_state.get("tp_pct", 1.0)
            sl = st.session_state.get("sl_pct", 1.0)
            rrr = tp / sl if sl != 0 else 0

            df_judge = pd.DataFrame({
                "Metric": ["Market Structure", "Risk Profile", "Win Rate", "Risk/Reward", "Guidance"],
                "Value": [structure, risk, f"{win_rate:.1f}%", f"1:{rrr:.2f}", advice]
            })
            st.table(df_judge)
            
        st.markdown("### Trading Outcomes & Performance Metrics")
        
        if history_data:
            total_signals = len(df_hist)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Signals", total_signals)
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Wins", wins)
            m4.metric("Losses", losses)
            
            st.markdown("#### Signal Effectiveness Report")
            st.dataframe(df_hist[['timestamp', 'signal', 'entry_price', 'outcome']], hide_index=True, use_container_width=True)
        else:
            st.info("No closed signals found.")

    except Exception as e:
        st.error(f"Error parsing AI results: {e}")
else:
    st.info("Click 'Analyze Now' in the sidebar settings to generate analysis.")