import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Stock Hunter: US Edition",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS (US Market Style)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    /* Global Settings */
    .stApp {
        font-family: 'Prompt', sans-serif;
        background-color: #0e1117;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: #fff;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Prompt', sans-serif;
        font-size: 14px;
        color: #888;
    }

    /* Strategy Card */
    .strategy-card {
        background: linear-gradient(145deg, #1a1c24, #13151b);
        border: 1px solid #333;
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .strategy-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .zone-badge {
        background-color: #222;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        color: #aaa;
        border: 1px solid #444;
    }
    .price-large {
        font-family: 'JetBrains Mono', monospace;
        font-size: 28px;
        color: #4CAF50;
        font-weight: 600;
    }
    
    /* Input Field */
    .stTextInput input {
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Sidebar (Optimized for US Stocks)
with st.sidebar:
    st.markdown("### 🇺🇸 US MARKET SETTINGS")
    
    # Quick Select for US Stocks
    st.markdown("<small style='color:#888'>หุ้นยอดนิยม (Magnificent 7)</small>", unsafe_allow_html=True)
    col_q1, col_q2, col_q3 = st.columns(3)
    if col_q1.button("NVDA"): st.session_state['symbol'] = "NVDA"
    if col_q2.button("TSLA"): st.session_state['symbol'] = "TSLA"
    if col_q3.button("AAPL"): st.session_state['symbol'] = "AAPL"
    
    col_q4, col_q5, col_q6 = st.columns(3)
    if col_q4.button("MSFT"): st.session_state['symbol'] = "MSFT"
    if col_q5.button("AMZN"): st.session_state['symbol'] = "AMZN"
    if col_q6.button("GOOG"): st.session_state['symbol'] = "GOOG"

    # Input Logic to handle button clicks
    default_sym = st.session_state.get('symbol', 'NVDA')
    symbol_input = st.text_input("ระบุชื่อย่อหุ้น (Ticker)", value=default_sym).upper()
    
    period_input = st.selectbox("ช่วงเวลาข้อมูล (Historical Data)", ["1y", "2y", "5y", "10y"], index=1)
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 12px; color: #666; font-family: "Prompt";'>
    MARKET: NASDAQ / NYSE<br>
    CURRENCY: USD ONLY<br>
    STATUS: ONLINE
    </div>
    """, unsafe_allow_html=True)
    
    analyze_btn = st.button("RUN ANALYSIS", type="primary", use_container_width=True)

# -----------------------------------------------------------
# Logic Functions
def get_us_stock_data(symbol, period):
    ticker = yf.Ticker(symbol)
    try:
        # 1. ดึงข้อมูล History
        df = ticker.history(period=period, interval="1wk")
        
        if df.empty:
            return None, None, "No Data"

        # 2. ดึงข้อมูล Info (เพื่อเช็คสกุลเงิน)
        info = ticker.info
        currency = info.get('currency', 'Unknown')
        
        # 3. กรองเฉพาะหุ้น US (USD)
        if currency != 'USD':
            return None, None, "Not US Stock"

        full_name = info.get('longName', symbol)
        return df, full_name, currency

    except Exception as e:
        return None, None, str(e)

def calculate_fractal_levels(df):
    levels = []
    # Fractal Calculation
    for i in range(2, len(df)-2):
        low_val = df['Low'].iloc[i]
        if low_val < df['Low'].iloc[i-1] and low_val < df['Low'].iloc[i-2] and \
           low_val < df['Low'].iloc[i+1] and low_val < df['Low'].iloc[i+2]:
            levels.append(low_val)
            
    # Consolidation Logic
    consolidated = []
    if levels:
        levels.sort()
        while levels:
            base = levels.pop(0)
            group = [base]
            keep = []
            for x in levels:
                if x <= base * 1.05: # 5% zone width
                    group.append(x)
                else:
                    keep.append(x)
            levels = keep
            # Strength = number of touches
            consolidated.append((sum(group)/len(group), len(group)))
    return consolidated

def plot_us_chart(df, levels):
    fig = go.Figure()

    # Candlestick (Green/Red Classic Style)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='Price (USD)',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ))

    # Support Lines
    for i, (price, _) in enumerate(levels[:3]):
        fig.add_hline(
            y=price, 
            line_dash="dash", 
            line_width=1,
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text=f"BUY ZONE {i+1}",
            annotation_position="bottom right",
            annotation_font_size=11,
            annotation_font_color="white"
        )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=650,
        margin=dict(l=10, r=50, t=30, b=30),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False, linecolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#222', side='right', tickprefix="$") 
    )
    return fig

# -----------------------------------------------------------
# Main Execution

st.markdown(f"<h2 style='margin-bottom: 0;'>WALL STREET HUNTER <span style='color:#4CAF50; font-size:18px;'>US EDITION</span></h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#666; font-size:12px; font-family:monospace;'>DATA SOURCE: YAHOO FINANCE | DATE: {datetime.now().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)
st.markdown("---")

if analyze_btn or symbol_input:
    with st.spinner(f"CONNECTING TO US MARKET: {symbol_input}..."):
        df, full_name, error_msg = get_us_stock_data(symbol_input, period_input)

        if df is None:
            if error_msg == "Not US Stock":
                st.error(f"❌ '{symbol_input}' ไม่ใช่หุ้นในตลาดสหรัฐฯ (USD) ระบบนี้กรองเฉพาะหุ้น US เท่านั้นครับ")
            elif error_msg == "No Data":
                st.error(f"❌ ไม่พบข้อมูล Ticker: '{symbol_input}' กรุณาตรวจสอบตัวสะกด (เช่น NVDA, AAPL)")
            else:
                st.error(f"❌ Error: {error_msg}")
        else:
            current_price = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # --- METRICS (US STYLE) ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LAST PRICE (USD)", f"${current_price:,.2f}", f"{change_pct:.2f}%")
            c2.metric("52W HIGH", f"${df['High'].tail(52).max():,.2f}")
            c3.metric("52W LOW", f"${df['Low'].tail(52).min():,.2f}")
            
            atr_val = (df['High']-df['Low']).tail(14).mean()
            c4.metric("VOLATILITY (ATR)", f"${atr_val:.2f}")
            
            st.markdown("---")

            # --- LOGIC ANALYSIS ---
            raw_levels = calculate_fractal_levels(df)
            waiting_levels = [l for l in raw_levels if l[0] < current_price]
            waiting_levels.sort(key=lambda x: x[0], reverse=True)
            top_3 = waiting_levels[:3]

            col_chart, col_plan = st.columns([2.5, 1])

            with col_chart:
                st.markdown(f"**🇺🇸 PRICE STRUCTURE: {full_name}**")
                if top_3:
                    fig = plot_us_chart(df, top_3)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df['Close'])
                    st.warning("All Time High Mode: หุ้นกำลังทำนิวไฮ ไม่มีแนวรับด้านล่าง")

            with col_plan:
                st.markdown("**🎯 EXECUTION PLAN**")
                
                if not top_3:
                    st.info("Wait for Pullback: ราคาวิ่งแรงเกินไป รอให้สร้างฐานใหม่")
                else:
                    total_strength = sum(l[1] for l in top_3)
                    
                    for i, (price, count) in enumerate(top_3):
                        weight = round((count / total_strength) * 100)
                        gap = ((current_price - price) / current_price) * 100
                        
                        # US Pro Card Design
                        st.markdown(f"""
                        <div class="strategy-card">
                            <div class="strategy-head">
                                <span class="zone-badge">ZONE 0{i+1}</span>
                                <span style="color:#666; font-size:12px;">WEIGHT {weight}%</span>
                            </div>
                            <div class="price-large">${price:,.2f}</div>
                            <div style="margin-top: 15px; border-top: 1px solid #333; padding-top: 10px;">
                                <div style="display:flex; justify-content:space-between; color:#bbb; font-size:13px; font-family:'JetBrains Mono';">
                                    <span>DIP: -{gap:.1f}%</span>
                                    <span>BASE: {count} WKS</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
