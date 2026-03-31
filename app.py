import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Analiz Terminali", layout="wide")

# CSS: Alarm ve Kart Tasarımı
st.markdown("""
    <style>
    .param-label { color: #555; font-size: 12px; font-weight: bold; }
    .param-value { color: #000; font-size: 14px; font-family: monospace; }
    .stContainer { border: 1px solid #e6e9ef; border-radius: 10px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# Parametreleri Güvenli Çekme
ZAMAN_DILIMI = getattr(p, 'ZAMAN_DILIMI', '4h')
GUNCELLEME = getattr(p, 'GUNCELLEME_SANIYESI', 60)
EMA_H = getattr(p, 'EMA_HIZLI', 20)
EMA_Y = getattr(p, 'EMA_YAVAS', 50)

interval_map = {'1h': Interval.in_1_hour, '4h': Interval.in_4_hour, '1d': Interval.in_daily}

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    file_path = os.path.join(os.path.dirname(__file__), "inputs.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
    return ["THYAO", "ASELS"]

st.title("📊 BIST Detaylı Teknik Takip")
tv = get_tv_connection()
placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    with placeholder.container():
        cols = st.columns(3)
        
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=interval_map.get(ZAMAN_DILIMI), n_bars=100)
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    
                    # Teknik Hesaplamalar
                    rsi_val = ta.rsi(df['close'], length=p.RSI_PERIYOT).iloc[-1]
                    ema_h_val = ta.ema(df['close'], length=EMA_H).iloc[-1]
                    ema_y_val = ta.ema(df['close'], length=EMA_Y).iloc[-1]
                    v_ma_val = ta.sma(df['volume'], length=p.HACIM_MA_PERIYOT).iloc[-1]
                    current_vol = df['volume'].iloc[-1]
                    
                    # Durum Belirleme
                    is_bullish = ema_h_val > ema_y_val and rsi_val > p.RSI_SINIR
                    bg_color = "#d4edda" if is_bullish else "#f8d7da" if ema_h_val < ema_y_val else "#fff3cd"
                    status_text = "ALIM FIRSATI" if is_bullish else "SATICILI SEYİR" if ema_h_val < ema_y_val else "BEKLE / NÖTR"

                    with cols[idx % 3]:
                        # Ana Kart Başlığı
                        st.markdown(f"""
                            <div style="background-color:{bg_color}; padding:10px; border-radius:10px 10px 0 0; border:1px solid #ddd; text-align:center;">
                                <h3 style="margin:0;">{h}</h3>
                                <b style="font-size:20px;">{price:.2f} TL</b><br>
                                <small>{status_text}</small>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Parametre Detay Kutusu
                        with st.container(border=True):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"<span class='param-label'>Zaman:</span> <span class='param-value'>{ZAMAN_DILIMI}</span>", unsafe_allow_html=True)
                                st.markdown(f"<span class='param-label'>EMA {EMA_H}:</span> <span class='param-value'>{ema_h_val:.2f}</span>", unsafe_allow_html=True)
                                st.markdown(f"<span class='param-label'>EMA {EMA_Y}:</span> <span class='param-value'>{ema_y_val:.2f}</span>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<span class='param-label'>RSI ({p.RSI_PERIYOT}):</span> <span class='param-value'>{rsi_val:.1f}</span>", unsafe_allow_html=True)
                                st.markdown(f"<span class='param-label'>Hacim MA:</span> <span class='param-value'>{'✅ OK' if current_vol > v_ma_val else '❌ DÜŞÜK'}</span>", unsafe_allow_html=True)
                                st.markdown(f"<span class='param-label'>Hedef:</span> <span class='param-value'>%{p.KAR_AL_ORAN}</span>", unsafe_allow_html=True)
                            
                            st.divider()
                            # Kar Al / Zarar Kes Seviyeleri
                            st.success(f"🎯 Kar Al: **{price*(1+p.KAR_AL_ORAN/100):.2f}**")
                            st.error(f"🛡️ Stop: **{price*(1-p.ZARAR_KES_ORAN/100):.2f}**")

            except Exception as e:
                st.error(f"{h} hatası")

        st.caption(f"⏱️ Son Kontrol: {datetime.now().strftime('%H:%M:%S')} | Veri Kaynağı: TradingView")
        
    time.sleep(GUNCELLEME)
    st.rerun()