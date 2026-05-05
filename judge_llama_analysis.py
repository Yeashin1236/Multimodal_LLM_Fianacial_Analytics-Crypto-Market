from ollama import Client

# --- API KEY ---
API_KEY = "5d0c06475d7249758e28655c5310b2f9.b5EzA_bumpw5S5KypdE4kp5G"

client = Client(
    host="https://api.ollama.com",
    headers={'Authorization': 'Bearer ' + API_KEY}
)

def judge_llama_analysis(
    backtest_history_list,
    latest_ai_analysis_text,
    coin_name="Cryptocurrency",
    timeframe="1h"
):
    """
    Uses 'qwen3-coder:480b-cloud' to synthesize results.
    """
    
    # 1. Format Backtest Data
    history_string = ""
    if not backtest_history_list:
        history_string = "No backtest history available."
    else:
        for item in backtest_history_list:
            # FIX: Changed 'close_price' to 'entry_price' to match app.py dictionary keys
            history_string += f"{item['timestamp']} | {item['signal']} | {item['entry_price']:.2f}\n"

    system_prompt = """
You are a Market Intelligence Layer. You receive raw signals and synthesize them into a final market state.
Output MUST be valid JSON only.
"""

    user_prompt = f"""
Coin: {coin_name}
Timeframe: {timeframe}

Raw Signal Data:
{latest_ai_analysis_text}

Historical Signals:
{history_string}

Task:
1. Determine Market State (Trending Up/Down or Ranging).
2. Determine Bias (Bullish/Bearish/Neutral).
3. Determine Signal Frequency (High/Medium/Low based on volatility).
4. Give a concise Advice sentence.

Return STRICT JSON:
{{
  "market_status": {{
    "structure": "Trending Up | Trending Down | Ranging",
    "risk_profile": "LOW | MEDIUM | HIGH"
  }},
  "strategy_bias": {{
    "direction": "Bullish | Bearish | Neutral",
    "confidence_score": "0-100",
    "key_driver": "Main market driver."
  }},
  "action_plan": {{
    "primary_advice": "Actionable advice."
  }}
}}
"""

    try:
        response = client.chat(
            model="qwen3-coder:480b-cloud",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False
        )
        return response["message"]["content"]

    except Exception as e:
        return f"{{\"error\": \"Judge Error: {str(e)}\"}}"