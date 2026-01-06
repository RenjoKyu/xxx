import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Stock Hunter Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS (Minimalist & Professional + Thai Font)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');

    /* Global Font & Background */
    .stApp {
        font-family: 'Prompt', -apple-system, sans-serif;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 500;
        font-family: 'SF Mono', 'Consolas', monospace; /* Keep numbers mono */
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #888;
        font-family: 'Prompt', sans-serif;
    }

    /* Custom Card for Strategy */
    .strategy-card {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid #333;
        padding: 20px;
        border-radius: 4px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .strategy-card:hover {
        border-color: #555;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .zone-label {
        font-family: 'Prompt', sans-serif;
        font-size: 14px;
        color: #aaa;
        margin-bottom: 8px;
    }
    .price-tag {
        font-family: 'SF Mono', 'Consolas', monospace;
        font-size: 22px;
        font-weight: 500;
        color: #e0e0e0;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Adjust Input styling */
    .stTextInput input {
        font-family: 'SF Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Sidebar
with st.sidebar:
    st.markdown("### การตั้งค่าระบบ")
    symbol_input = st.text_input("ชื่อย่อหุ้น (TICKER)", value="NVDA").upper()
    period_input = st.selectbox("กรอบเวลาคำนวณ", ["1y", "2y", "5y", "10y"], index=2)
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 12px; color: #666; font-family: "Prompt";'>
    ระบบ: FRACTAL GEOMETRY<br>
    สถานะ: พร้อมใช้งาน<br>
    เวอร์ชัน: 2.1.1 (FIXED)
    </div>
    """, unsafe_allow_html=True)
    
    analyze_btn = st.button("เริ่มการวิเคราะห์", type="primary", use_container_width=True)

# -----------------------------------------------------------
# Logic Functions
def get_stock_data(symbol, period):
    ticker = yf.Ticker(symbol)
    try:
        df = ticker.history(period=period, interval="1wk")
        info = ticker.info
        full_name = info.get('longName', symbol)
        currency = info.get('currency', 'USD')
        return df, full_name, currency
    except:
        return None, None, None

def calculate_fractal_levels(df):
    levels = []
    for i in range(2, len(df)-2):
        low_val = df['Low'].iloc[i]
        if low_val < df['Low'].iloc[i-1] and low_val < df['Low'].iloc[i-2] and \
           low_val < df['Low'].iloc[i+1] and low_val < df['Low'].iloc[i+2]:
            levels.append(low_val)
            
    consolidated = []
    if levels:
        levels.sort()
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

def plot_minimal_chart(df, levels):
    fig = go.Figure()

    # Minimalist Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='ราคา',
        increasing_line_color='#ffffff', 
        increasing_fillcolor='rgba(0,0,0,0)', 
        decreasing_line_color='#ff3333',
        decreasing_fillcolor='#ff3333'
    ))

    # Support Lines (Fixed: add_hline instead of add_hlines)
    for i, (price, _) in enumerate(levels[:3]):
        fig.add_hline(
            y=price, 
            line_dash="dot", 
            line_width=1,
            line_color="rgba(255, 255, 255, 0.4)",
            annotation_text=f"ZONE {i+1}",
            annotation_position="bottom right",
            annotation_font_size=10,
            annotation_font_color="rgba(255, 255, 255, 0.6)"
        )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600,
        margin=dict(l=0, r=40, t=20, b=20),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False, showline=True, linecolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#222', side='right') 
    )
    return fig

# -----------------------------------------------------------
# Main Execution

# Header
st.markdown(f"<h3 style='margin-bottom: 0;'>STOCK HUNTER <span style='color:#666; font-weight:300;'>/ PRO TERMINAL</span></h3>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#666; font-size:12px; font-family:monospace;'>DATE: {datetime.now().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)
st.markdown("---")

if analyze_btn or symbol_input:
    with st.spinner("กำลังประมวลผลข้อมูล..."):
        df, full_name, currency = get_stock_data(symbol_input, period_input)

        if df is None or df.empty:
            st.error(f"ไม่พบข้อมูล: {symbol_input}")
        else:
            current_price = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # --- METRICS BAR ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("ราคาล่าสุด", f"{current_price:,.2f}", f"{change_pct:.2f}%")
            c2.metric("สูงสุด 52 สัปดาห์", f"{df['High'].tail(52).max():,.2f}")
            c3.metric("ต่ำสุด 52 สัปดาห์", f"{df['Low'].tail(52).min():,.2f}")
            c4.metric("ความผันผวน (ATR)", f"{(df['High']-df['Low']).tail(14).mean():,.2f}")
            
            st.markdown("---")

            # --- ANALYSIS ---
            raw_levels = calculate_fractal_levels(df)
            waiting_levels = [l for l in raw_levels if l[0] < current_price]
            waiting_levels.sort(key=lambda x: x[0], reverse=True)
            top_3 = waiting_levels[:3]

            col_main, col_side = st.columns([3, 1])

            with col_main:
                st.markdown("**กราฟแสดงโครงสร้างราคา (Price Structure)**")
                if top_3:
                    fig = plot_minimal_chart(df, top_3)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df['Close'])
                    st.info("ราคากำลังทำจุดสูงสุดใหม่ (All Time High) ไม่มีแนวรับด้านล่างในระยะใกล้")
            
            with col_side:
                st.markdown("**โซนสะสมเชิงกลยุทธ์**")
                
                if not top_3:
                    st.markdown("""
                    <div style="padding: 20px; color: #888; font-size: 13px; border: 1px dashed #444; border-radius: 4px; text-align: center;">
                    ไม่พบแนวรับที่มีนัยสำคัญ<br>แนะนำให้รอฐานราคาใหม่
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    total_strength = sum(l[1] for l in top_3)
                    
                    for i, (price, count) in enumerate(top_3):
                        weight = round((count / total_strength) * 100)
                        gap = ((current_price - price) / current_price) * 100
                        
                        # Card UI
                        st.markdown(f"""
                        <div class="strategy-card">
                            <div class="zone-label">ไม้ที่ {i+1} / น้ำหนัก {weight}%</div>
                            <div class="price-tag">${price:,.2f}</div>
                            <div style="margin-top: 10px; font-size: 12px; color: #888; font-family: 'Prompt'; display: flex; justify-content: space-between;">
                                <span>ห่างปัจจุบัน: -{gap:.1f}%</span>
                                <span>ความแข็งแกร่ง: {count}</span>
                            </div>
                            <div style="margin-top: 8px; height: 2px; background: #333; width: 100%;">
                                <div style="height: 100%; background: #e0e0e0; width: {weight}%;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
