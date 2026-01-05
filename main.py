import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import os

# 1. System Configuration
st.set_page_config(
    page_title="Stock Hunter Pro",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Environment Variables
SERVER_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD")

# --- Authentication Logic ---
active_api_key = None
user_status = "Guest"

with st.sidebar:
    st.header("Authentication")
    
    # Direct Link Button (Text Only)
    st.link_button("Get API Key (Google AI Studio)", "https://aistudio.google.com/app/apikey", type="secondary")
    
    st.markdown("---")
    
    # Input Field
    auth_input = st.text_input(
        "Access Key / API Key", 
        type="password", 
        help="Enter Admin Password or your Gemini API Key."
    )
    
    if auth_input:
        if ADMIN_PASS and auth_input == ADMIN_PASS:
            active_api_key = SERVER_KEY
            user_status = "Admin"
            st.success("Status: Admin Mode Active")
        elif auth_input.startswith("AIza"):
            active_api_key = auth_input
            user_status = "User"
            st.success("Status: Personal Key Connected")
        else:
            st.error("Error: Invalid Credentials")
    else:
        st.info("Status: Guest Mode")
        st.caption("Chart visualization is available. Authentication required for AI analysis.")

# --- Core Functions ---

@st.cache_data(ttl=3600)
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol.upper())
    try:
        df = ticker.history(period="5y", interval="1wk")
        if df.empty: return None, None
        return df, ticker.info
    except:
        return None, None

def get_ai_analysis(symbol, key):
    if not key: return None
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt: Explicitly requesting NO emojis and professional tone
        prompt = f"""
        Analyze {symbol} as an institutional investment strategist.
        Provide a formal executive summary in Thai language.
        
        Structure:
        1. Business Overview (Nature of business and revenue model)
        2. Economic Moat (Competitive advantages)
        3. Key Risk Factors (Macro and micro risks)
        
        Constraints:
        - Use formal, professional Thai language suitable for financial reports.
        - DO NOT use emojis or informal slang.
        - Keep it concise and direct.
        """
        return model.generate_content(prompt).text
    except Exception as e:
        return f"System Error: {str(e)}"

def calculate_fractals(df):
    levels = []
    # Fractal Logic (5 Bars)
    for i in range(2, len(df)-2):
        low = df['Low'].iloc[i]
        if low < df['Low'].iloc[i-1] and \
           low < df['Low'].iloc[i-2] and \
           low < df['Low'].iloc[i+1] and \
           low < df['Low'].iloc[i+2]:
            levels.append(low)
    
    # Consolidation
    levels.sort()
    consolidated = []
    if levels:
        while levels:
            base = levels.pop(0)
            group = [base]
            keep = []
            for x in levels:
                if x <= base * 1.05:
                    group.append(x)
                else:
                    keep.append(x)
            levels = keep
            consolidated.append((sum(group)/len(group), len(group)))
    return consolidated

# --- User Interface ---

st.title("Stock Hunter Pro")
st.markdown("Quantitative Support & Resistance Analysis System")
st.markdown("---")

# Input Section
col_input, col_action = st.columns([4, 1])
with col_input:
    symbol = st.text_input("Ticker Symbol", value="NVDA", help="e.g., AAPL, TSLA, PTT.BK").upper()
with col_action:
    st.write("") 
    st.write("")
    run_analysis = st.button("Run Analysis", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner("Processing Market Data..."):
        df, info = get_stock_data(symbol)
        
        if df is None:
            st.error(f"Error: Data not found for symbol '{symbol}'. Please verify the ticker.")
            st.stop()
            
        current_price = df['Close'].iloc[-1]
        year_high = df['High'].tail(52).max()
        year_low = df['Low'].tail(52).min()
        
        # 1. Market Overview
        st.subheader(f"Market Overview: {symbol}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${current_price:,.2f}")
        m2.metric("52-Week High", f"${year_high:,.2f}")
        m3.metric("52-Week Low", f"${year_low:,.2f}")
        m4.metric("Volatility (ATR Proxy)", f"{(year_high-year_low)/year_low*100:.1f}%")
        
        # Price Chart
        st.line_chart(df['Close'], color="#00FF00", height=350)

        st.markdown("---")

        # 2. Fundamental Analysis (AI)
        if active_api_key:
            st.subheader("Fundamental Analysis (Executive Summary)")
            with st.spinner("Generating Report..."):
                analysis_text = get_ai_analysis(symbol, active_api_key)
                st.info(analysis_text)
        elif user_status == "Guest":
            st.warning("Guest Mode: Fundamental analysis is disabled. Please authenticate via the sidebar to unlock.")

        st.markdown("---")

        # 3. Quantitative Strategy
        st.subheader("Strategic Support Levels (Fractal Model)")
        
        fractals = calculate_fractals(df)
        supports = [f for f in fractals if f[0] < current_price]
        supports.sort(key=lambda x: x[0], reverse=True)
        
        if not supports:
            st.write("Status: Price at All-Time High / No significant support structure detected.")
        else:
            top_3 = supports[:3]
            total_strength = sum(x[1] for x in top_3)
            
            data = []
            for i, (price, count) in enumerate(top_3):
                weight = (count / total_strength)
                gap = (current_price - price) / current_price
                data.append({
                    "Level": f"Support {i+1}",
                    "Target Price ($)": f"{price:,.2f}",
                    "Gap from Current": f"-{gap:.1%}",
                    "Discount from High": f"-{(year_high-price)/year_high:.1%}",
                    "Technical Strength": f"{count}",
                    "Rec. Allocation": f"{weight:.0%}"
                })
            
            # Display as Clean Table
            st.dataframe(
                pd.DataFrame(data).set_index("Level"),
                use_container_width=True
            )
            
            st.caption("Note: Recommended allocation is derived from historical price density.")
