import streamlit as st
import pandas as pd
import requests

# ----------------- Config & Title -------------------
st.set_page_config(page_title="ORATS Skew Screener", layout="wide")
st.title("📈 ORATS Volatility Skew Screener")

st.markdown("""
Upload your `low_iv_rank_stocks.csv` file. The app will:
- Use the `ticker` column
- Fetch vol25, vol50, vol75 from ORATS
- Calculate:
    - **Put Skew** = vol75 − vol50  
    - **Call Skew** = vol25 − vol50  
    - **Risk Reversal** = vol25 − vol75  
""")

# ----------------- File Upload -------------------
uploaded_file = st.file_uploader("Upload `low_iv_rank_stocks.csv`", type=["csv"])
run_button = st.button("Run Screener")

# ----------------- Load API Key from Streamlit Secrets -------------------
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
if run_button and uploaded_file:
    df_input = pd.read_csv(uploaded_file)
    if "ticker" not in df_input.columns:
        st.error("CSV must contain a `ticker` column.")
    else:
        tickers = df_input["ticker"].dropna().astype(str).str.upper().tolist()
        st.info(f"Fetching ORATS data for {len(tickers)} tickers...")
        results = [fetch_orats_data(t, token) for t in tickers]
        df = pd.DataFrame(results)

        if "error" in df.columns:
            st.warning("Some tickers failed. Check the error column for details.")
            st.dataframe(df)
        else:
            st.dataframe(df.style.format({col: "{:.4f}" for col in df.columns if "vol" in col or "skew" in col}))
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Download Skew Results", csv, "orats_skew_output.csv", "text/csv")
