import os
import pandas as pd
from ollama import Client

# --- TEMPORARY DIRECT KEY CONFIGURATION ---
API_KEY = "5d0c06475d7249758e28655c5310b2f9.b5EzA_bumpw5S5KypdE4kp5G"

# Initialize the cloud client
# FIX: Changed host to api.ollama.com to match judge_llama_analysis.py
client = Client(
    host="https://api.ollama.com",
    headers={'Authorization': 'Bearer ' + API_KEY}
)

def analyze_chart_with_ai(df, bb_data, mfi_data, coin_name="Cryptocurrency", timeframe="1h"):
    """
    Analyzes chart data using 'gpt-oss:20b-cloud' via Ollama Cloud.
    Implements the specific BB/BBW/MFI strategy.
    """
    
    # --- ROBUSTNESS FIX: Handle Dictionary Inputs ---
    if isinstance(df, dict):
        df = pd.DataFrame.from_dict(df)
    
    if isinstance(bb_data, dict):
        bb_data = pd.DataFrame(bb_data)
        
    if isinstance(mfi_data, dict):
        try:
            mfi_data = pd.Series(mfi_data)
        except:
            mfi_data = pd.DataFrame(mfi_data)
    elif isinstance(mfi_data, list):
        mfi_data = pd.Series(mfi_data)

    # 1. PREPARE DATA CONTEXT
    recent_data = df.tail(30).copy()
    
    # Slice bb_data and mfi_data
    recent_bb_data = bb_data.tail(30).copy()
    recent_mfi_data = mfi_data.tail(30).copy()
    
    # Calculate Middle Band
    bb_middle_series = df['Close'].rolling(window=20).mean()
    recent_bb_middle = bb_middle_series.tail(30)
    
    context_data = "Date, Open, High, Low, Close, BB_Upper, BB_Middle, BB_Lower, BB_Width, MFI\n"
    
    for i in range(len(recent_data)):
        date = recent_data.index[i].strftime('%Y-%m-%d %H:%M')
        row = recent_data.iloc[i]
        
        bb_u = recent_bb_data['upper'].iloc[i]
        bb_l = recent_bb_data['lower'].iloc[i]
        bb_m = recent_bb_middle.iloc[i]
        bbw = recent_bb_data['width'].iloc[i]
        mfi = recent_mfi_data.iloc[i]
        
        context_data += (
            f"{date}, {row['Open']:.2f}, {row['High']:.2f}, {row['Low']:.2f}, "
            f"{row['Close']:.2f}, {bb_u:.2f}, {bb_m:.2f}, {bb_l:.2f}, "
            f"{bbw:.4f}, {mfi:.2f}\n"
        )

    # --- PROFESSIONAL SYSTEM PROMPT (JSON OUTPUT) ---
    system_prompt = f"""
    Act as a Senior Quantitative Analyst. Your task is to analyze the provided market data for {coin_name} on the {timeframe} timeframe.
    
    Analyze the following:
    1. **Trend**: Determine if the 20 SMA is trending Up, Down, or Sideways.
    2. **Volatility**: Assess Bollinger Band Width (BBW) state (Expanding, Contracting, Squeeze).
    3. **Momentum**: Analyze MFI relative to the 50 centerline.
    4. **Signal**: Determine if a Buy Long or Sell Short setup is confirmed based on the rules:
       - Buy: Price > 20 SMA + 2 Green Candles + BBW Rising + MFI > 50.
       - Sell: Price < 20 SMA + 2 Red Candles + BBW Rising + MFI < 50.
    
    **CRITICAL**: You must return your response ONLY as a valid JSON object with the following structure. Do not add markdown formatting (like ```json).
    
    {{
      "coin": "{coin_name}",
      "timeframe": "{timeframe}",
      "analysis": {{
        "trend": "UPTREND | DOWNTREND | SIDEWAYS",
        "volatility": "EXPANDING | CONTRACTING | SQUEEZE",
        "momentum": "BULLISH | BEARISH | NEUTRAL",
        "signal_strength": "STRONG | MODERATE | WEAK"
      }},
      "decision": {{
        "action": "BUY LONG | SELL SHORT | NO TRADE",
        "entry_zone": "Estimated price zone or 'N/A'",
        "reasoning": "A concise 1-sentence professional explanation referencing the specific indicator logic."
      }}
    }}
    """

    try:
        # Call the cloud model: gpt-oss:20b-cloud
        response = client.chat(
            model='gpt-oss:20b-cloud',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Analyze this chart data:\n{context_data}"}
            ],
            stream=False
        )
        return response['message']['content']
        
    except Exception as e:
        # Return error in JSON format so app.py doesn't crash
        return f"{{\"error\": \"AI Connection Error: {str(e)}\"}}"