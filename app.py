import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="HybridTraderAI", page_icon="📈", layout="wide")

ASSETS = {
    "NASDAQ 100": "^NDX",
    "S&P 500": "^GSPC",
    "Gold": "GC=F",
    "EUR/USD": "EURUSD=X",
    "USD/ZAR": "ZAR=X",
}

@st.cache_data(ttl=300)
def load_data(symbol, period="6mo", interval="1d"):
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def indicators(df):
    x = df.copy()
    x["EMA20"] = x["Close"].ewm(span=20, adjust=False).mean()
    x["EMA50"] = x["Close"].ewm(span=50, adjust=False).mean()
    x["EMA200"] = x["Close"].ewm(span=200, adjust=False).mean()
    delta = x["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - (100 / (1 + rs))
    tr = pd.concat([
        x["High"] - x["Low"],
        (x["High"] - x["Close"].shift()).abs(),
        (x["Low"] - x["Close"].shift()).abs()
    ], axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["VolMA20"] = x["Volume"].rolling(20).mean()
    return x

def technical_score(x):
    r = x.iloc[-1]
    score = 0
    reasons = []
    if r["Close"] > r["EMA20"]:
        score += 20; reasons.append("Price above EMA20")
    else:
        score -= 20; reasons.append("Price below EMA20")
    if r["EMA20"] > r["EMA50"]:
        score += 20; reasons.append("EMA20 above EMA50")
    else:
        score -= 20; reasons.append("EMA20 below EMA50")
    if r["EMA50"] > r["EMA200"]:
        score += 20; reasons.append("EMA50 above EMA200")
    else:
        score -= 20; reasons.append("EMA50 below EMA200")
    if r["RSI"] >= 55 and r["RSI"] <= 70:
        score += 20; reasons.append("RSI supports bullish momentum")
    elif r["RSI"] < 45:
        score -= 20; reasons.append("RSI shows weak momentum")
    else:
        reasons.append("RSI is neutral/extended")
    if pd.notna(r["Volume"]) and pd.notna(r["VolMA20"]) and r["Volume"] > r["VolMA20"]:
        score += 20 if r["Close"] > r["Open"] else -20
        reasons.append("Volume confirms today's direction")
    else:
        reasons.append("Volume confirmation unavailable/weak")
    return score, reasons

def hybrid_signal(tech, fundamental, sentiment, risk):
    # Risk is a penalty, not a directional vote.
    raw = 0.55*tech + 0.30*fundamental + 0.15*sentiment
    adjusted = raw - risk*0.20
    if adjusted >= 35:
        signal = "BUY"
    elif adjusted <= -35:
        signal = "SELL"
    else:
        signal = "WAIT"
    confidence = min(99, max(1, 50 + abs(adjusted)*0.9))
    return adjusted, signal, confidence

st.title("🤖 HybridTraderAI")
st.caption("Hybrid fundamental + technical market analyser — MVP")

with st.sidebar:
    st.header("Market")
    asset = st.selectbox("Instrument", list(ASSETS.keys()))
    period = st.selectbox("History", ["3mo", "6mo", "1y", "2y"], index=1)
    symbol = ASSETS[asset]
    st.divider()
    st.header("Hybrid inputs")
    fundamental = st.slider("Fundamental bias", -100, 100, 0, 5,
                            help="Manual placeholder until economic/news feeds are connected.")
    sentiment = st.slider("Market sentiment", -100, 100, 0, 5)
    risk = st.slider("Risk environment", 0, 100, 25, 5,
                     help="0 = calm, 100 = extreme risk.")

df = load_data(symbol, period)
if df.empty:
    st.error("No market data returned. Try another instrument or period.")
    st.stop()

x = indicators(df)
tech, reasons = technical_score(x)
adjusted, signal, confidence = hybrid_signal(tech, fundamental, sentiment, risk)
last = x.iloc[-1]
price = float(last["Close"])
atr = float(last["ATR"]) if pd.notna(last["ATR"]) else price*0.01

c1, c2, c3, c4 = st.columns(4)
c1.metric("Signal", signal)
c2.metric("Hybrid Score", f"{adjusted:.0f}/100")
c3.metric("Confidence", f"{confidence:.0f}%")
c4.metric("Price", f"{price:,.2f}")

st.subheader("Market chart")
chart = x[["Close", "EMA20", "EMA50", "EMA200"]].dropna()
st.line_chart(chart)

left, right = st.columns(2)
with left:
    st.subheader("Component scores")
    st.progress((tech + 100)/200, text=f"Technical: {tech:+.0f}")
    st.progress((fundamental + 100)/200, text=f"Fundamental: {fundamental:+.0f}")
    st.progress((sentiment + 100)/200, text=f"Sentiment: {sentiment:+.0f}")
    st.progress(risk/100, text=f"Risk penalty: {risk:.0f}")

with right:
    st.subheader("Key indicators")
    st.write(f"RSI(14): **{last['RSI']:.1f}**")
    st.write(f"ATR(14): **{atr:.2f}**")
    st.write(f"EMA20: **{last['EMA20']:.2f}**")
    st.write(f"EMA50: **{last['EMA50']:.2f}**")
    st.write(f"EMA200: **{last['EMA200']:.2f}**")

st.subheader("Why the analyser reached this view")
for r in reasons:
    st.write("•", r)

if signal == "BUY":
    sl = price - 1.5*atr
    tp1 = price + 2.0*atr
    tp2 = price + 3.0*atr
elif signal == "SELL":
    sl = price + 1.5*atr
    tp1 = price - 2.0*atr
    tp2 = price - 3.0*atr
else:
    sl = tp1 = tp2 = np.nan

st.subheader("Risk framework")
if signal != "WAIT":
    a, b, c = st.columns(3)
    a.metric("Illustrative Stop", f"{sl:,.2f}")
    b.metric("TP1", f"{tp1:,.2f}")
    c.metric("TP2", f"{tp2:,.2f}")
    st.warning("These are model levels for research/backtesting, not financial advice or guaranteed trade levels.")
else:
    st.info("WAIT: the combined score is not strong enough for a directional setup.")

st.caption("MVP note: fundamental and sentiment sliders are intentionally manual. The next build can connect economic-calendar/news data and replace them with automated scores.")
