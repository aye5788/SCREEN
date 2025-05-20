import streamlit as st
import pandas as pd
import requests

# ----------------- Config & Title -------------------
st.set_page_config(page_title="ORATS Volatility Skew Screener", layout="wide")
st.title("📈 ORATS Volatility Skew Screener")

st.markdown("""
This app uses `low_iv_rank_stocks.csv` directly from the repo.  
It fetches `vol25`, `vol50`, `vol75` from ORATS and calculates:

- **Put Skew** = vol75 − vol50  
- **Call Skew** = vol25 − vol50  
- **Risk Reversal** = vol25 − vol75
""")

run_button = st.button("Run Screener")

# ----------------- Load API Key -------------------
token = st.secrets["orats"]["token"]

# ----------------- Fetch ORATS Data -------------------
@st.cache_data(show_spinner=False)
def fetch_orats_data(ticker, token):
    url = f"https://api.orats.io/datav2/cores?ticker={ticker}&token={token}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()[0]
        vol25, vol50, vol75 = data["vol25"], data["vol50"], data["vol75"]
        return {
            "ticker": ticker,
            "vol25": vol25,
            "vol50": vol50,
            "vol75": vol75,
            "put_skew": vol75 - vol50,
            "call_skew": vol25 - vol50,
            "risk_reversal": vol25 - vol75
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

# ----------------- Main Logic -------------------
if run_button:
    try:
        df_input = pd.read_csv("low_iv_rank_stocks.csv")
    except Exception as e:
        st.error(f"🚫 Could not load low_iv_rank_stocks.csv — {e}")
        st.stop()

    if "ticker" not in df_input.columns:
        st.error("CSV must have a `ticker` column.")
    else:
        tickers = df_input["ticker"].dropna().astype(str).str.upper().tolist()
        st.info(f"Fetching ORATS data for {len(tickers)} tickers...")
        results = [fetch_orats_data(t, token) for t in tickers]
        df = pd.DataFrame(results)

        if "error" in df.columns:
            st.warning("Some tickers failed. Check the error column.")
            st.dataframe(df)
        else:
            st.dataframe(df.style.format({col: "{:.4f}" for col in df.columns if "vol" in col or "skew" in col}))
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Download CSV", csv, "orats_skew_results.csv", "text/csv")

