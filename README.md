## Financial Analytics Dashboard – Crypto Markets
### Overview
This project is an AI-Driven Cryptocurrency Investment Recommendation System developed as part of a Master's Thesis for the Master’s Programme “Business Analytics and Big Data Systems” at the Higher School of Economics.
The dashboard bridges the gap between rigid rule-based technical analysis and the nuanced reasoning capabilities of Large Language Models (LLMs). It is designed to assist retail investors by translating complex market data into actionable, human-readable insights.
Key Problem Solved:Retail investors often struggle with the complexity of technical indicators and the "black box" nature of AI trading bots. This system provides a Hybrid Quantitative-Explainable Framework that offers transparent signals validated by a multi-model AI architecture.

### Key Features
1. Trend–Volatility Breakout Strategy
A deterministic rule-based engine that generates trading signals based on:
- Trend Detection: 20-period Simple Moving Average (SMA).
- Volatility Expansion: Bollinger Band Width (BBW).
- Momentum Confirmation: Money Flow Index (MFI).
2. Multi-Model AI Analysis
Unlike single-model systems, this dashboard employs a dual-layer LLM architecture:
- Analyst Model: Interprets raw technical data to generate primary signals (Buy/Sell/No Trade).
- Judge Model: Validates the Analyst's signal against historical performance and current market context to ensure reliability.
3. Integrated Backtesting
Evaluate strategy performance instantly with a built-in backtesting engine that calculates:
- Win Rate %
- Risk/Reward Ratio
- Historical Signal Effectiveness
4. Explainable AI Assistant (Fin AI)
An interactive chatbot that allows users to:
- Ask about current market conditions.
- Learn about the baseline strategy rules.
- Get beginner-friendly explanations of technical metrics.

## Tech Stack
- Frontend: Streamlit (Interactive Dashboard)
- Data Source: Yahoo Finance (yfinance)
- Data Manipulation: Pandas, NumPy
- Visualization: Plotly (TradingView-style charts)
- AI/LLM Integration: Custom modules for LLM reasoning (ai_analysis, judge_llama_analysis)
