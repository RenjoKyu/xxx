import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import os

# 1. การตั้งค่าระบบ (System Configuration)
st.set_page_config(
    page_title="Stock Hunter Pro",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ดึงค่า Key จาก Environment Variables
SERVER_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD")

# --- ระบบยืนยันตัวตน (Authentication) ---
active_api_key = None
user_status = "Guest"

with st.sidebar:
    st.header("การยืนยันตัวตน")
    
    # ปุ่มกดไปขอ Key (Text Only, No Emoji)
    st.link_button("ขอ API Key (Google AI Studio)", "https://aistudio.google.com/app/apikey", type="secondary")
    
    st.markdown("---")
    
    # ช่องกรอกรหัส
    auth_input = st.text_input(
        "รหัสผ่าน / API Key", 
        type="password", 
        help="กรอกรหัสผู้ดูแลระบบ หรือ Gemini API Key ของท่าน"
    )
    
    if auth_input:
        if ADMIN_PASS and auth_input == ADMIN_PASS:
            active_api_key = SERVER_KEY
            user_status = "Admin"
            st.success("สถานะ: ผู้ดูแลระบบ (Admin Mode)")
        elif auth_input.startswith("AIza"):
            active_api_key = auth_input
            user_status = "User"
            st.success("สถานะ: เชื่อมต่อด้วย Key ส่วนตัว")
        else:
            st.error("ข้อผิดพลาด: รหัสไม่ถูกต้อง")
    else:
        st.info("สถานะ: ผู้เยี่ยมชม (Guest Mode)")
        st.caption("ต้องยืนยันตัวตนเพื่อเข้าถึงบทวิเคราะห์เชิงลึก")

# --- ฟังก์ชันการทำงานหลัก (Core Functions) ---

@st.cache_data(ttl=3600)
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol.upper())
    try:
        # ดึงข้อมูลประวัติและข้อมูลบริษัท
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
        
        # Prompt สั่งงานเน้นภาษาทางการ ไม่ใส่อีโมจิ
        prompt = f"""
        วิเคราะห์หุ้น {symbol} ในฐานะนักกลยุทธ์การลงทุนสถาบัน
        เขียนบทสรุปผู้บริหาร (Executive Summary) เป็นภาษาไทยทางการ
        
        โครงสร้าง:
        1. ภาพรวมธุรกิจ (ลักษณะธุรกิจและโมเดลรายได้)
        2. ความได้เปรียบทางการแข่งขัน (Moat)
        3. ปัจจัยเสี่ยงสำคัญ (มหภาคและจุลภาค)
        
        ข้อกำหนด:
        - ใช้ภาษาไทยระดับทางการ เหมาะสำหรับรายงานการเงิน
        - ห้ามใช้อีโมจิหรือภาษาพูด
        - กระชับและตรงประเด็น
        """
        return model.generate_content(prompt).text
    except Exception as e:
        return f"ระบบขัดข้อง: {str(e)}"

def calculate_fractals(df):
    levels = []
    # คำนวณ Fractal (5 แท่งเทียน)
    for i in range(2, len(df)-2):
        low = df['Low'].iloc[i]
        if low < df['Low'].iloc[i-1] and \
           low < df['Low'].iloc[i-2] and \
           low < df['Low'].iloc[i+1] and \
           low < df['Low'].iloc[i+2]:
            levels.append(low)
    
    # รวมกลุ่มราคา (Consolidation)
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

# --- ส่วนแสดงผลผู้ใช้งาน (User Interface) ---

st.title("Stock Hunter Pro")
st.markdown("ระบบวิเคราะห์แนวรับเชิงปริมาณและปัจจัยพื้นฐาน (Quantitative Analysis System)")
st.markdown("---")

# ส่วนรับข้อมูลเข้า
col_input, col_action = st.columns([4, 1])
with col_input:
    symbol = st.text_input("สัญลักษณ์หลักทรัพย์ (Ticker)", value="NVDA", help="ตัวอย่าง: AAPL, TSLA, PTT.BK").upper()
with col_action:
    st.write("") 
    st.write("")
    run_analysis = st.button("เริ่มการวิเคราะห์", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner("กำลังประมวลผลข้อมูลตลาด..."):
        df, info = get_stock_data(symbol)
        
        if df is None:
            st.error(f"ไม่พบข้อมูลสำหรับสัญลักษณ์ '{symbol}' กรุณาตรวจสอบความถูกต้อง")
            st.stop()
            
        current_price = df['Close'].iloc[-1]
        year_high = df['High'].tail(52).max()
        year_low = df['Low'].tail(52).min()
        
        # ดึงชื่อเต็มบริษัท
        full_name = info.get('longName', symbol)
        
        # 1. ข้อมูลภาพรวม (Market Overview)
        st.subheader(f"{full_name} ({symbol})")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ราคาล่าสุด", f"${current_price:,.2f}")
        m2.metric("สูงสุด 52 สัปดาห์", f"${year_high:,.2f}")
        m3.metric("ต่ำสุด 52 สัปดาห์", f"${year_low:,.2f}")
        m4.metric("ความผันผวน (ATR)", f"{(year_high-year_low)/year_low*100:.1f}%")
        
        st.markdown("---")

        # 2. บทวิเคราะห์พื้นฐาน (AI Analysis)
        if active_api_key:
            st.subheader("บทวิเคราะห์ปัจจัยพื้นฐาน (Executive Summary)")
            with st.spinner("กำลังสร้างรายงาน..."):
                analysis_text = get_ai_analysis(symbol, active_api_key)
                st.info(analysis_text)
        elif user_status == "Guest":
            st.warning("โหมดผู้เยี่ยมชม: กรุณายืนยันตัวตนเพื่อเข้าถึงบทวิเคราะห์เชิงลึก")

        st.markdown("---")

        # 3. แผนกลยุทธ์แนวรับ (Quantitative Strategy)
        st.subheader("แผนกลยุทธ์แนวรับ (Fractal Model)")
        
        fractals = calculate_fractals(df)
        supports = [f for f in fractals if f[0] < current_price]
        supports.sort(key=lambda x: x[0], reverse=True)
        
        if not supports:
            st.write("สถานะ: ราคาสูงสุดตลอดกาล (ATH) / ไม่พบฐานราคาที่มีนัยสำคัญ")
        else:
            top_3 = supports[:3]
            total_strength = sum(x[1] for x in top_3)
            
            data = []
            for i, (price, count) in enumerate(top_3):
                weight = (count / total_strength)
                gap = (current_price - price) / current_price
                
                # จัดรูปแบบตารางให้ดูง่ายและเป็นทางการ
                data.append({
                    "ลำดับ": f"แนวรับที่ {i+1}",
                    "ราคาเป้าหมาย": f"{price:,.2f}",     # ไม่ใส่ $ ในเซลล์เพื่อให้ดูคลีนขึ้น (หัวข้อบอกหน่วยแล้ว)
                    "ส่วนต่างราคา (Gap)": f"-{gap:.1%}",
                    "ส่วนลดจากจุดสูงสุด": f"-{(year_high-price)/year_high:.1%}",
                    "ความแข็งแกร่ง (คะแนน)": f"{count}",
                    "น้ำหนักการลงทุน (แนะนำ)": f"{weight:.0%}"
                })
            
            # สร้าง DataFrame และปรับแต่ง Index
            df_table = pd.DataFrame(data).set_index("ลำดับ")
            
            # แสดงผลแบบตารางเต็มความกว้าง (Clean Table)
            st.table(df_table)
            
            st.caption("หมายเหตุ: น้ำหนักการลงทุนคำนวณจากความหนาแน่นของราคาในอดีต (Historical Price Density)")
