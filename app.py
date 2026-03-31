import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Genişliği ve Başlık
st.set_page_config(page_title="BIST Pro-Monitor", layout="wide", initial_sidebar_state="expanded")

# TradingView Zaman Dilimi Eşleşmesi
interval_map = {
    '1h': Interval.in_1_hour,
    '4h': Interval.in_4_hour,
    '1d': Interval.in_daily
}

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
    return ["THYAO", "ASELS"]

# --- ARAYÜZ ÜST PANEL ---
st.title("🛡️ BIST Profesyonel Takip Terminali")
st.caption(f"Aktif Periyot: {p.ZAMAN_DILIMI} | Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")

# Yan Menü: Tüm Parametrelerin Görünümü
with st.sidebar:
    st.header("⚙️ Strateji Detayları")
    st.divider()
    st.write(f"**Zaman Dilimi:** `{p.ZAMAN_DILIMI}`")
    st.write(f"**EMA Hızlı/Yavaş:** `{p.EMA_HIZLI} / {p.EMA_YAVAS}`")
    st.write(f"**RSI Eşik:** `{p.RSI_SINIR}`")
    st.write(f"**Hacim MA:** `{p.HACIM_MA_PERIYOT}`")
    st.divider()
    st.metric("🎯 Hedef Kar", f"%{p.KAR_AL_ORAN}")
    st.metric("🛡️ Zarar Kes", f"%{p.ZARAR_KES_ORAN}", delta_color="inverse")

tv = get_tv_connection()
placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    selected_interval = interval_map.get(p.ZAMAN_DILIMI, Interval.in_1_hour)
    
    with placeholder.container():
        # Hisseleri 3'lü kolonlar halinde dizelim (Daha derli toplu)
        cols = st.columns(3)
        
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=selected_interval, n_bars=100)
                
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    
                    # Hesaplamalar
                    rsi = ta.rsi(df['close'], length=p.RSI_PERIYOT).iloc[-1]
                    ema_h = ta.ema(df['close'], length=p.EMA_HIZLI).iloc[-1]
                    ema_y = ta.ema(df['close'], length=p.EMA_YAVAS).iloc[-1]
                    v_ma = ta.sma(df['volume'], length=p.HACIM_MA_PERIYOT).iloc[-1]
                    guncel_hacim = df['volume'].iloc[-1]
                    
                    # Sinyal Mantığı
                    trend_yukari = ema_h > ema_y
                    rsi_onay = rsi > p.RSI_SINIR
                    hacim_onay = guncel_hacim > v_ma
                    
                    # Renk ve Durum Belirleme
                    if trend_yukari and rsi_onay and hacim_onay:
                        durum, renk, bg_color = "GÜÇLÜ AL", "🟢", "#d4edda"
                    elif not trend_yukari or rsi > p.RSI_ASIRI_ALIM:
                        durum, renk, bg_color = "SAT / RİSK", "🔴", "#f8d7da"
                    else:
                        durum, renk, bg_color = "NÖTR / BEKLE", "🟡", "#fff3cd"

                    # Kart Tasarımı
                    with cols[idx % 3]:
                        # Custom CSS ile renkli kart oluşturma
                        st.markdown(f"""
                            <div style="background-color:{bg_color}; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px">
                                <h3 style="margin:0; color:#333;">{h} <span style="float:right;">{price:.2f} TL</span></h3>
                                <p style="margin:5px 0; font-weight:bold; color:#555;">{renk} {durum}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        with st.container(border=True):
                            m1, m2 = st.columns(2)
                            m1.metric("RSI", f"{rsi:.1f}", delta=f"{rsi-p.RSI_SINIR:.1f}" if rsi_onay else f"{rsi-p.RSI_SINIR:.1f}")
                            m2.metric("Hacim", "Yüksek" if hacim_onay else "Düşük")
                            
                            st.write(f"**EMA {p.EMA_HIZLI}:** `{ema_h:.2f}` | **EMA {p.EMA_YAVAS}:** `{ema_y:.2f}`")
                            
                            # Hedef Fiyatlar
                            st.divider()
                            t1, t2 = st.columns(2)
                            t1.write(f"🎯 **Kar:**\n{price*(1+p.KAR_AL_ORAN/100):.2f}")
                            t2.write(f"🛡️ **Stop:**\n{price*(1-p.ZARAR_KES_ORAN/100):.2f}")
                else:
                    cols[idx % 3].error(f"{h} Verisi Alınamadı")
            except Exception as e:
                cols[idx % 3].error(f"{h} Hatası")
                
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()