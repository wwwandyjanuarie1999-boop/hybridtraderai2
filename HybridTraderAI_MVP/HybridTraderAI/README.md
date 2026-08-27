# HybridTraderAI

A free Streamlit-based hybrid market analyser combining technical, fundamental, sentiment and risk inputs.

## Current MVP
- NASDAQ 100, S&P 500, Gold, EUR/USD and USD/ZAR
- EMA20/50/200
- RSI(14)
- ATR(14)
- Volume confirmation
- Manual fundamental bias
- Manual sentiment bias
- Risk penalty
- Hybrid BUY/SELL/WAIT score
- Illustrative ATR-based SL/TP levels
- Browser dashboard

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy free
Push this repository to GitHub, then deploy `app.py` through Streamlit Community Cloud.

## Roadmap
1. Automated economic-calendar inputs
2. News/sentiment engine
3. Multi-timeframe analysis
4. Backtesting engine
5. Trade journal
6. Alerts
7. Machine-learning regime classifier
8. Broker integration only after extensive testing
