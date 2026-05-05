import json

def get_chat_response(prompt, context, analysis_func=None):
    """
    Generates a professional response using Tables, Visualizations, and Comparisons.
    """
    
    # 1. Default Values
    symbol = context.get('symbol', 'N/A')
    timeframe = context.get('timeframe', 'N/A')
    current_price = context.get('current_price', 'N/A')
    
    # Default Parsed Values
    trend = "N/A"
    volatility = "N/A"
    momentum = "N/A"
    signal_action = "N/A"
    signal_reasoning = "N/A"
    judge_advice = "N/A"
    risk_profile = "N/A"
    
    win_rate_val = 0.0
    wins = 0
    losses = 0
    total_signals = 0

    # 2. Parse AI Result JSON
    ai_raw = context.get('ai')
    if ai_raw:
        try:
            ai_json = json.loads(ai_raw)
            analysis_data = ai_json.get("analysis", {})
            decision_data = ai_json.get("decision", {})
            
            trend = analysis_data.get("trend", "N/A")
            volatility = analysis_data.get("volatility", "N/A")
            momentum = analysis_data.get("momentum", "N/A")
            signal_action = decision_data.get("action", "N/A")
            signal_reasoning = decision_data.get("reasoning", "N/A")
        except Exception:
            pass

    # 3. Parse Judge Result JSON
    judge_raw = context.get('judge')
    if judge_raw:
        try:
            judge_json = json.loads(judge_raw)
            judge_advice = judge_json.get("action_plan", {}).get("primary_advice", "N/A")
            risk_profile = judge_json.get("market_status", {}).get("risk_profile", "N/A")
        except Exception:
            pass

    # 4. Calculate Performance Stats
    signals = context.get('signals', [])
    if signals:
        total_signals = len(signals)
        wins = sum(1 for s in signals if s['outcome'] == 'WIN')
        losses = total_signals - wins
        if total_signals > 0:
            win_rate_val = (wins / total_signals) * 100

    # 5. Helper: Text Progress Bar for Visualization
    def get_progress_bar(percent, length=10):
        filled = int((percent / 100) * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"

    # 6. Normalize Prompt
    prompt_lower = prompt.lower()

    # 7. Response Generation

    # --- Intent: Win Rate / Performance (Visualized) ---
    if "win rate" in prompt_lower or "performance" in prompt_lower or "stats" in prompt_lower:
        bar = get_progress_bar(win_rate_val)
        response = (
            f"### 📊 Performance Report: {symbol}\n\n"
            f"**Timeframe:** {timeframe} | **Total Signals:** {total_signals}\n\n"
            f"**Win Rate Visualization:**\n"
            f"{bar} **{win_rate_val:.1f}%**\n\n"
            f"| Metric | Value |\n"
            f"| :--- | :--- |\n"
            f"| ✅ Wins | **{wins}** |\n"
            f"| ❌ Losses | **{losses}** |\n"
            f"| 📈 Expectancy | Positive (Based on settings) |\n\n"
            f"> _Historical performance based on backtest settings._"
        )

    # --- Intent: Trend / Analysis (Detailed) ---
    elif "trend" in prompt_lower or "analysis" in prompt_lower or "check" in prompt_lower:
        response = (
            f"### 📈 Technical Analysis: {symbol}\n\n"
            f"**Current Price:** `${current_price:,.2f}`\n\n"
            f"#### Market State\n"
            f"| Indicator | Status | Implication |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Trend | **{trend}** | Direction bias |\n"
            f"| Momentum | **{momentum}** | Strength of move |\n"
            f"| Volatility | **{volatility}** | Risk level |\n\n"
            f"#### 🤖 AI Decision\n"
            f"**Action:** **{signal_action}**\n\n"
            f"**Reasoning:** {signal_reasoning}"
        )

    # --- Intent: Comparison (Table Format) ---
    elif "compare" in prompt_lower or "versus" in prompt_lower or "vs" in prompt_lower:
        response = (
            f"### ⚖️ AI vs Judge Comparison\n\n"
            f"| Category | AI Engine 🤖 | Judge Layer 🧐 |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Primary Focus** | Technical Indicators | Risk & History |\n"
            f"| **Action** | {signal_action} | {judge_advice.split('.')[0]}... |\n"
            f"| **Risk View** | {volatility} | {risk_profile} |\n"
            f"| **Confidence** | High (if signals align) | {win_rate_val:.1f}% Win Rate |\n\n"
            f"> **Synthesis:** The AI suggests *{signal_action}*, while the Judge advises *{judge_advice}*."
        )

    # --- Intent: Advice / Decision (Professional Card) ---
    elif "advice" in prompt_lower or "risk" in prompt_lower or "should i" in prompt_lower or "judge" in prompt_lower:
        response = (
            f"### 🧠 Expert Advisory\n\n"
            f"**Asset:** {symbol} ({timeframe})\n\n"
            f"#### 💡 Judge's Decision\n"
            f"```\n{judge_advice}\n```\n\n"
            f"#### 🛡️ Risk Profile\n"
            f"- **Status:** {risk_profile}\n"
            f"- **Historical Win Rate:** {win_rate_val:.1f}%\n\n"
            f"> ⚠️ **Disclaimer:** This is not financial advice. Always manage your risk."
        )

    # --- Intent: Signal (Actionable) ---
    elif "signal" in prompt_lower or "buy" in prompt_lower or "sell" in prompt_lower:
        response = (
            f"### 🎯 Trade Signal Alert\n\n"
            f"| Metric | Detail |\n"
            f"| :--- | :--- |\n"
            f"| **Symbol** | {symbol} |\n"
            f"| **Price** | ${current_price:,.2f} |\n"
            f"| **Signal** | **{signal_action}** |\n"
            f"| **Win Prob.** | {win_rate_val:.1f}% |\n\n"
            f"**Reason:** {signal_reasoning}"
        )

    # --- Intent: General / Default (Full Dashboard Summary) ---
    else:
        bar = get_progress_bar(win_rate_val)
        response = (
            f"### 🪙 Dashboard Summary: {symbol}\n\n"
            f"**Price:** `${current_price:,.2f}` | **Timeframe:** {timeframe}\n\n"
            f"#### 1. Market Overview\n"
            f"- **Trend:** {trend}\n"
            f"- **Momentum:** {momentum}\n"
            f"- **Volatility:** {volatility}\n\n"
            f"#### 2. AI Decision Matrix\n"
            f"| Source | Action | Key Driver |\n"
            f"| :--- | :--- | :--- |\n"
            f"| AI Engine | **{signal_action}** | {signal_reasoning.split('.')[0]} |\n"
            f"| Judge | **{judge_advice.split('.')[0]}** | Risk Management |\n\n"
            f"#### 3. Strategy Performance\n"
            f"Win Rate: {bar} **{win_rate_val:.1f}%** ({wins}W / {losses}L)\n\n"
            f"---\n"
            f"**🚀 Quick Advice:** {judge_advice}"
        )

    return response