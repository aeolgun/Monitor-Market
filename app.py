import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Terminal", layout="wide")

# CSS: Okunabilirlik ve Net Renkler
st.markdown("""
    <style>
    /* Kart Genel Yapısı */
    .stContainer {
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        background-color: #ffffff;
        padding: 0px !important;
    }
    /* Metin Renklerini Sabitleme (Beyaz font hatasını önlemek için) */
    h3, h4, p, span, div {
        color: #1a1a1a !important;
    }
    .metric-box {
        padding: 15px;
        border-radius: 12px 12px 0 0;
        text-align: center;
    }
    .param-row {
        display: flex;
        justify-content: space-between;
        padding: 5px 15px;
        border-bottom: 1px solid #eee;
        font-size: 14px;
    }
    .label { font-weight: bold; color: #555 !important; }
    .value { font-family: 'Courier New', monospace; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Parametre Değerlerini Çekme (Hata korumalı)
def get_p(attr, default):
    return getattr(p, attr, default)

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    file_path = os.path.join(os.path.dirname(__file__), "inputs.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
    return ["THYAO", "ASELS"]

st.title("📊 BIST Strateji İzleme")
tv = get_tv_connection()
placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    # Parametreleri her döngüde tazeleyelim
    Z_DILIMI = get_p('ZAMAN_DILIMI', '4h')
    EMA_H_LEN = get_p('EMA_HIZLI', 20)
    EMA_Y_LEN = get_p('EMA_YAVAS', 50)
    RSI_LEN = get_p('RSI_PERIYOT', 14)
    RSI_SINIR = get_p('RSI_SINIR', 50)
    HACIM_LEN = get_p('HACIM_MA_PERIYOT', 20)
    KA_ORAN = get_p('KAR_AL_ORAN', 25.0)
    ZK_ORAN = get_p('ZARAR_KES_ORAN', 5.0)

    interval_map = {'1h': Interval.in_1_hour, '4h': Interval.in_4_hour, '1d': Interval.in_daily}

    with placeholder.container():
        cols = st.columns(3)
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=interval_map.get(Z_DILIMI), n_bars=100)
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    
                    # Teknik Veriler
                    rsi_val = ta.rsi(df['close'], length=RSI_LEN).iloc[-1]
                    ema_h_val = ta.ema(df['close'], length=EMA_H_LEN).iloc[-1]
                    ema_y_val = ta.ema(df['close'], length=EMA_Y_LEN).iloc[-1]
                    v_ma_val = ta.sma(df['volume'], length=HACIM_LEN).iloc[-1]
                    curr_vol = df['volume'].iloc[-1]
                    
                    # TAM RENK MANTIĞI (Daha doygun renkler)
                    if ema_h_val > ema_y_val and rsi_val > RSI_SINIR:
                        bg_color = "#22c55e"  # Tam Yeşil
                        status = "GÜÇLÜ AL"
                    elif ema_h_val < ema_y_val:
                        bg_color = "#ef4444"  # Tam Kırmızı
                        status = "SATIŞ RİSKİ"
                    else:
                        bg_color = "#facc15"  # Tam Sarı
                        status = "NÖTR / İZLE"

                    with cols[idx % 3]:
                        with st.container():
                            # Renkli Başlık Bölümü
                            st.markdown(f"""
                                <div class="metric-box" style="background-color:{bg_color};">
                                    <h3 style="color: white !important; margin:0;">{h}</h3>
                                    <h4 style="color: white !important; margin:0;">{price:.2f} TL</h4>
                                    <small style="color: white !important;">{status}</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Parametre Satırları (Beyaz arka plan üzerine siyah metin)
                            st.markdown(f"""
                                <div class="param-row"><span class="label">Zaman Dilimi</span><span class="value">{Z_DILIMI}</span></div>
                                <div class="param-row"><span class="label">EMA {EMA_H_LEN}</span><span class="value">{ema_h_val:.2f}</span></div>
                                <div class="param-row"><span class="label">EMA {EMA_Y_LEN}</span><span class="value">{ema_y_val:.2f}</span></div>
                                <div class="param-row"><span class="label">RSI {RSI_LEN}</span><span class="value">{rsi_val:.1f}</span></div>
                                <div class="param-row"><span class="label">Hacim MA ({HACIM_LEN})</span><span class="value">{'Yeterli ✅' if curr_vol > v_ma_val else 'Düşük ❌'}</span></div>
                                <div class="param-row" style="border:none;"><span class="label">Hedef Kar</span><span class="value">%{KA_ORAN}</span></div>
                            """, unsafe_allow_html=True)
                            
                            # Alt Bilgi (Hedef Fiyatlar)
                            st.divider()
                            p1, p2 = st.columns(2)
                            p1.success(f"🎯 Kar Al\n{price*(1+KA_ORAN/100):.2f}")
                            p2.error(f"🛡️ Stop\n{price*(1-ZK_ORAN/100):.2f}")
            except:
                st.error(f"{h} verisi çekilemedi.")

        st.caption(f"⏱️ Güncelleme: {datetime.now().strftime('%H:%M:%S')} | Mod: {Z_DILIMI}")
    
    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()