import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import os

# 1. System Configuration
# ตั้งค่าให้ Sidebar กางออกเสมอ (initial_sidebar_state="expanded")
st.set_page_config(
    page_title="Stock Hunter Pro",
    page_icon="🎯",
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
    st.header("🔐 การยืนยันตัวตน (Authentication)")
    
    # แจ้งเตือนเล็กๆ ให้รู้ว่าต้องทำอะไร
    st.info("👋 ยินดีต้อนรับ! กรุณายืนยันตัวตนที่นี่เพื่อใช้งานเต็มรูปแบบ")
    
    st.link_button("👉 ขอ API Key (Google AI Studio)", "https://aistudio.google.com/app/apikey", type="primary")
    
    st.markdown("---")
    
    auth_input = st.text_input(
        "รหัสผ่าน / API Key", 
        type="password", 
        help="กรอกรหัส Admin หรือ Gemini API Key ของท่าน"
    )
    
    if auth_input:
        if ADMIN_PASS and auth_input == ADMIN_PASS:
            active_api_key = SERVER_KEY
            user_status = "Admin"
            st.success("✅ สถานะ: ผู้ดูแลระบบ (Admin)")
        elif auth_input.startswith("AIza"):
            active_api_key = auth_input
            user_status = "User"
            st.success("✅ สถานะ: เชื่อมต่อ API ส่วนตัว")
        else:
            st.error("❌ รหัสไม่ถูกต้อง")
    else:
        st.warning("👤 สถานะ: Guest (จำกัดการใช้งาน)")
        st.caption("กราฟดูฟรี! แต่ต้อง Login เพื่อใช้ AI")

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
        
        prompt = f"""
        วิเคราะห์หุ้น {symbol} ในมุมมองนักลงทุนสถาบัน (Institutional Investor)
        สรุป Executive Summary สั้นๆ กระชับ เป็นภาษาไทยทางการ:
        
        1. 🏢 **Business Model:** ทำอะไร รายได้มาจากไหน
        2. 🛡️ **Economic Moat:** จุดแข็งที่คู่แข่งสู้ยาก
        3. ⚠️ **Risk Factors:** ความเสี่ยงที่ต้องระวังที่สุด
        
        Note: ตอบเป็นข้อๆ ชัดเจน ภาษาทางการ น่าเชื่อถือ
        """
        return model.generate_content(prompt).text
    except Exception as e:
        return f"ระบบ AI ขัดข้อง: {str(e)}"

def calculate_fractals(df):
    levels = []
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

st.title("Stock Hunter Pro 🎯")
st.markdown("**ระบบวิเคราะห์กลยุทธ์การลงทุน (Quantitative & AI Analysis)**")

# --- ⚠️ LEGAL DISCLAIMER (ส่วนสำคัญเพื่อความปลอดภัยทางกฎหมาย) ---
with st.expander("⚠️ คำเตือนและข้อตกลงการใช้งาน (Legal Disclaimer) - โปรดอ่าน", expanded=True):
    st.error("""
    **คำเตือนความเสี่ยง (Risk Disclosure):**
    1. **ไม่ใช่คำแนะนำทางการเงิน:** ข้อมูล บทวิเคราะห์ และกราฟทั้งหมดในระบบนี้ เป็นเพียงการคำนวณทางสถิติและข้อมูลจาก AI เพื่อการศึกษาเท่านั้น **ไม่ใช่** การชี้ชวนให้ซื้อขายหลักทรัพย์
    2. **ความเสี่ยงของ AI:** บทวิเคราะห์จาก AI (Gemini) อาจมีความคลาดเคลื่อน หรือเป็นข้อมูลเก่า (Hallucination) ผู้ใช้งานควรตรวจสอบข้อเท็จจริงจากแหล่งอื่นประกอบเสมอ
    3. **รับผิดชอบตัวเอง:** การลงทุนมีความเสี่ยง ผู้ใช้งานต้องรับผิดชอบผลการขาดทุนด้วยตนเอง ทางผู้พัฒนาไม่มีส่วนรับผิดชอบต่อความเสียหายใดๆ ที่เกิดขึ้น
    """)
# -------------------------------------------------------------

st.markdown("---")

# Input Section
col_input, col_btn = st.columns([3, 1])
with col_input:
    symbol = st.text_input("🔍 พิมพ์ชื่อหุ้น (Ticker)", value="NVDA", help="เช่น AAPL, TSLA, PTT.BK").upper()
with col_btn:
    st.write("")
    st.write("")
    run_analysis = st.button("🚀 เริ่มวิเคราะห์", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner("⏳ กำลังประมวลผล Big Data..."):
        df, info = get_stock_data(symbol)
        
        if df is None:
            st.error(f"❌ ไม่พบข้อมูลหุ้น '{symbol}' โปรดตรวจสอบชื่อย่อ")
            st.stop()
            
        current_price = df['Close'].iloc[-1]
        year_high = df['High'].tail(52).max()
        year_low = df['Low'].tail(52).min()
        full_name = info.get('longName', symbol)
        
        # 1. Market Overview Card
        with st.container(border=True):
            st.subheader(f"🏢 {full_name} ({symbol})")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("ราคาปัจจุบัน", f"${current_price:,.2f}")
            m2.metric("High 52W", f"${year_high:,.2f}")
            m3.metric("Low 52W", f"${year_low:,.2f}")
            drawdown = ((current_price - year_high) / year_high) * 100
            m4.metric("Drawdown", f"{drawdown:.1f}%", delta_color="inverse")

        st.write("")

        # 2. AI Analysis Section
        if active_api_key:
            with st.expander("🧠 บทวิเคราะห์พื้นฐาน (AI Insight)", expanded=True):
                with st.spinner("🤖 AI กำลังอ่านงบและวิเคราะห์..."):
                    analysis_text = get_ai_analysis(symbol, active_api_key)
                    st.markdown(analysis_text)
        elif user_status == "Guest":
            st.warning("🔒 **Guest Mode:** ฟีเจอร์ AI ถูกล็อก (กรุณายืนยันตัวตนที่เมนูซ้ายมือ)")

        st.markdown("### 🎯 แผนกลยุทธ์แนวรับ (Strategic Entry Zones)")
        st.caption("วิเคราะห์จากพฤติกรรมราคาในอดีต (Fractal Behavior)")

        # 3. Strategic Cards
        fractals = calculate_fractals(df)
        supports = [f for f in fractals if f[0] < current_price]
        supports.sort(key=lambda x: x[0], reverse=True)
        
        if not supports:
            st.info("📈 ราคาทำ All-Time High หรือยังไม่พบฐานแนวรับที่แข็งแกร่ง")
        else:
            top_3 = supports[:3]
            total_strength = sum(x[1] for x in top_3)
            
            # Layout แบบ 3 คอลัมน์ (Cards)
            cols = st.columns(len(top_3))
            
            for i, (price, count) in enumerate(top_3):
                weight = (count / total_strength)
                gap_percent = ((current_price - price) / current_price) * 100
                discount_from_high = ((year_high - price) / year_high) * 100
                
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"#### 🏷️ ไม้ที่ {i+1}")
                        
                        st.metric(
                            label="ราคาเข้าซื้อ (Target)",
                            value=f"${price:,.2f}",
                            delta=f"รออีก -{gap_percent:.1f}%",
                            delta_color="normal"
                        )
                        
                        st.divider()
                        
                        st.markdown(f"**📉 ส่วนลดจากยอดดอย:** -{discount_from_high:.1f}%")
                        st.markdown(f"**💪 ความแข็งแกร่ง:** {count} จุด")
                        st.markdown(f"**⚖️ น้ำหนักแนะนำ: {int(weight*100)}%**")
                        st.progress(weight)
