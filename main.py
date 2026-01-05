from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List, Optional

app = FastAPI()

class LevelModel(BaseModel):
    rank: int
    price: float
    weight_percent: int
    discount_from_high: float
    gap_from_current: float
    strength_count: int

class StockResponse(BaseModel):
    symbol: str
    company_name: str
    analysis_date: str
    current_price: float
    year_high: float
    year_low: float
    strategic_plan: List[LevelModel]
    advice: str

@app.get("/")
def home():
    return {"message": "Stock Hunter API is Running! 🚀"}

@app.get("/analyze/{symbol}", response_model=StockResponse)
def analyze_stock(symbol: str):
    search_date = datetime.now().strftime("%d/%m/%Y")
    ticker = yf.Ticker(symbol.upper())
    
    try:
        info = ticker.info
        full_name = info.get('longName', symbol.upper())
    except:
        full_name = "Unknown"

    # ดึงข้อมูล
    try:
        df = ticker.history(period="5y", interval="1wk")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    current_price = df['Close'].iloc[-1]
    one_year_df = df.tail(52)
    one_year_high = one_year_df['High'].max()
    one_year_low = one_year_df['Low'].min()
    
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
            
    waiting = [l for l in consolidated if l[0] < current_price]
    waiting.sort(key=lambda x: x[0], reverse=True)
    top_3 = waiting[:3]
    
    if not top_3:
        # Return default empty response structure instead of different dict
        return {
            "symbol": symbol.upper(),
            "company_name": full_name,
            "analysis_date": search_date,
            "current_price": round(current_price, 2),
            "year_high": round(one_year_high, 2),
            "year_low": round(one_year_low, 2),
            "strategic_plan": [],
            "advice": "All Time High / No Support Found"
        }

    total_strength = sum(l[1] for l in top_3)
    
    plan_data = []
    for i, (price, count) in enumerate(top_3):
        discount_pct = ((one_year_high - price) / one_year_high) * 100
        weight = round((count / total_strength) * 100)
        gap = ((current_price - price) / current_price) * 100
        
        plan_data.append({
            "rank": i + 1,
            "price": round(price, 2),
            "weight_percent": weight,
            "discount_from_high": round(discount_pct, 2),
            "gap_from_current": round(gap, 2),
            "strength_count": count
        })

    return {
        "symbol": symbol.upper(),
        "company_name": full_name,
        "analysis_date": search_date,
        "current_price": round(current_price, 2),
        "year_high": round(one_year_high, 2),
        "year_low": round(one_year_low, 2),
        "strategic_plan": plan_data,
        "advice": "Strategic Plan Calculated"
    }
