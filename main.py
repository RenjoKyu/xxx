import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import os

# 1. System Configuration
st.set_page_config(
    page_title="Stock Hunter Pro (US)",
    page_icon="🇺🇸",
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
    st.header("🔐 ยืนยันตัวตน (Authentication)")
    st.info("👋 ยินดีต้อนรับ! กรุณาใส่ Key เพื่อปลดล็อก AI")
    
    st.link_button("👉 ขอ API Key ฟรี (Google)", "https://aistudio.google.com/app/apikey", type="primary")
    
    st.markdown("---")
    
    auth_input = st.text_input(
        "รหัสผ่าน / API Key", 
        type="password", 
        help="ใส่รหัส Admin หรือ API Key ของคุณ"
    )
    
    if auth_input:
        if ADMIN_PASS and auth_input == ADMIN_PASS:
            active_api_key = SERVER_KEY
            user_status = "Admin"
            st.success("✅ Admin Mode: Ready")
        elif auth_input.startswith("AIza"):
            active_api_key = auth_input
            user_status = "User"
            st.success("✅ User Mode: Ready")
        else:
            st.error("❌ รหัสไม่ถูกต้อง")
    else:
        st.warning("👤 Guest Mode: ดูกราฟได้ (AI ล็อกอยู่)")

# --- Core Functions (Fixed for Stability) ---

@st.cache_data(ttl=300) # ลดเวลา Cache ลงเพื่อให้ได้ข้อมูลสดใหม่
def get_stock_data(symbol):
    # บังคับเป็นหุ้น US โดยการตัดช่องว่างและแปลงเป็นตัวใหญ่
    clean_symbol = symbol.strip().upper()
    ticker = yf.Ticker(clean_symbol)
    
    try:
        # ดึงแค่กราฟก่อน (โอกาสพังน้อยสุด)
        df = ticker.history(period="2y", interval="1wk") # ลดช่วงเวลาลงเหลือ 2 ปีเพื่อให้โหลดไว
        
        if df.empty:
            return None, None
            
        # พยายามดึงชื่อบริษัท (ถ้าพัง ให้ใช้ชื่อย่อแทน)
        try:
            name = ticker.info.get('longName', clean_symbol)
        except:
            name = clean_symbol
            
        return df, name
    except Exception as e:
        return None, None

def get_ai_analysis(symbol, key):
    if not key: return None
    try:
        genai.configure(api_key=key)
        # ใช้รุ่น Pro มาตรฐาน (เสถียรกว่า Flash ในบาง Server)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Analyze US Stock: {symbol} for an institutional investor.
        Provide a concise Executive Summary in Thai (Formal Tone).
        
        Structure:
        1. 🏢 **Business Model:** What does it do? (Revenue source)
        2. 🛡️ **Economic Moat:** Competitive Advantage?
        3. ⚠️ **Key Risks:** Main risks right now?
        
        Constraint: Respond in Professional Thai only. No markdown clutter.
        """
        return model.generate_content(prompt).text
    except Exception as e:
        return f"เกิดข้อผิดพลาดที่ AI: {str(e)} (ลองกดปุ่มวิเคราะห์ใหม่อีกครั้ง)"

def calculate_fractals(df):
    levels = []
    # Fractal Logic
    for i in range(2, len(df)-2):
        low = df['Low'].iloc[i]
        if low < df['Low'].iloc[i-1] and \
           low < df['Low'].iloc[i-2] and \
           low < df['Low'].iloc[i+1] and \
           low < df['Low'].iloc[i+2]:
            levels.append(low)
    
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

st.title("Stock Hunter Pro 🇺🇸")
st.markdown("**US Market Focus: Quantitative & AI Analysis**")

with st.expander("⚠️ คำเตือนความเสี่ยง (Disclaimer)", expanded=True):
    st.error("ข้อมูลเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำทางการเงิน การลงทุนมีความเสี่ยง")

st.markdown("---")

# Input Section
col_input, col_btn = st.columns([3, 1])
with col_input:
    # Default เป็น NVDA ตามที่ต้องการ
    symbol = st.text_input("🔍 ชื่อหุ้น US (Ticker)", value="NVDA", help="เช่น NVDA, TSLA, AAPL, MSFT").upper()
with col_btn:
    st.write("")
    st.write("")
    run_analysis = st.button("🚀 วิเคราะห์เลย", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner(f"🇺🇸 กำลังดึงข้อมูล {symbol} จากตลาด US..."):
        df, full_name = get_stock_data(symbol)
        
        if df is None:
            st.error(f"❌ ไม่พบข้อมูลหุ้น '{symbol}'")
            st.info("💡 เช็คตัวสะกด หรือ ลองกดวิเคราะห์ใหม่อีกครั้ง (บางทีเน็ต Server สะดุด)")
            st.stop()
            
        current_price = df['Close'].iloc[-1]
        year_high = df['High'].tail(52).max()
        year_low = df['Low'].tail(52).min()
        
        # 1. Market Overview Card
        with st.container(border=True):
            st.subheader(f"🏢 {full_name} ({symbol})")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Price (USD)", f"${current_price:,.2f}")
            m2.metric("52W High", f"${year_high:,.2f}")
            m3.metric("52W Low", f"${year_low:,.2f}")
            drawdown = ((current_price - year_high) / year_high) * 100
            m4.metric("Drawdown", f"{drawdown:.1f}%", delta_color="inverse")

        st.write("")

        # 2. AI Analysis Section
        if active_api_key:
            with st.expander("🧠 AI Insight (บทวิเคราะห์พื้นฐาน)", expanded=True):
                with st.spinner("🤖 AI กำลังอ่านงบการเงิน..."):
                    analysis_text = get_ai_analysis(symbol, active_api_key)
                    if analysis_text:
                        st.markdown(analysis_text)
                    else:
                        st.warning("AI ไม่ตอบสนอง กรุณาลองใหม่")
        elif user_status == "Guest":
            st.warning("🔒 เข้าสู่ระบบด้านซ้ายเพื่อดูบทวิเคราะห์ AI")

        st.markdown("### 🎯 แนวรับเชิงกลยุทธ์ (Support Zones)")
        
        # 3. Strategic Cards
        fractals = calculate_fractals(df)
        supports = [f for f in fractals if f[0] < current_price]
        supports.sort(key=lambda x: x[0], reverse=True)
        
        if not supports:
            st.info("📈 ราคาทำ New High หรือยังไม่มีฐานที่ชัดเจน")
        else:
            top_3 = supports[:3]
            total_strength = sum(x[1] for x in top_3)
            
            cols = st.columns(len(top_3))
            
            for i, (price, count) in enumerate(top_3):
                weight = (count / total_strength)
                gap_percent = ((current_price - price) / current_price) * 100
                discount_from_high = ((year_high - price) / year_high) * 100
                
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"#### 🏷️ ไม้ที่ {i+1}")
                        
                        st.metric(
                            label="Target Price",
                            value=f"${price:,.2f}",
                            delta=f"Wait -{gap_percent:.1f}%",
                            delta_color="normal"
                        )
                        st.divider()
                        st.markdown(f"**Discount:** -{discount_from_high:.1f}%")
                        st.markdown(f"**Strength:** {count} จุด")
                        st.progress(weight)
