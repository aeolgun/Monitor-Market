import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Yapılandırması
st.set_page_config(page_title="Monitor-Market", layout="wide")

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip().upper() for line in f.readlines() if line.strip()]
        else: return ["THYAO.IS"]
    except: return ["THYAO.IS"]

def get_data(symbol):
    # Yahoo'yu yormamak için her istek öncesi çok kısa bekleme
    time.sleep(0.6) 
    
    try:
        ticker = yf.Ticker(symbol)
        df = pd.DataFrame()
        
        # 1. DENEME: Saatlik Veri (1h) - 3 kez deniyoruz
        for _ in range(3):
            df = ticker.history(period="60d", interval="1h")
            if not df.empty and len(df) >= p.EMA_YAVAS:
                interval_type = "Saatlik"
                break
            time.sleep(1)
            
        # 2. DENEME: Saatlik gelmezse Günlük Veri (1d) dene
        if df.empty or len(df) < p.EMA_YAVAS:
            df = ticker.history(period="150d", interval="1d")
            interval_type = "Günlük"

        if df.empty or len(df) < p.EMA_YAVAS:
            return None, None, None

        # İndikatör Hesaplamaları
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1], interval_type
    except Exception as e:
        return None, None, None

# --- ARAYÜZ ---
st.title("📈 Monitor-Market: Canlı BIST Takibi")

# Parametreleri al (Hata payı için getattr kullanıldı)
ka_oran = getattr(p, 'KAR_AL_ORAN', 25.0)
zk_oran = getattr(p, 'ZARAR_KES_ORAN', 5.0)

with st.expander("🛡️ Strateji ve Risk Parametreleri", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.metric("Hedef Kar", f"%{ka_oran}")
    c1.metric("Zarar Kes", f"%{zk_oran}")
    c2.write(f"**Trend:** EMA {p.EMA_HIZLI}/{p.EMA_YAVAS}")
    c2.write(f"**RSI:** {p.RSI_SINIR} Eşik")
    c3.write(f"**Hacim MA:** {p.HACIM_MA_PERIYOT}")
    c3.write(f"**Yenileme:** {p.GUNCELLEME_SANIYESI}s")

st.divider()

placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    with placeholder.container():
        cols = st.columns(2)
        success_count = 0
        
        for idx, h in enumerate(hisseler):
            data, price, i_type = get_data(h)
            
            if data is not None:
                success_count += 1
                # Sinyal Kararı
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data.get('Volume', 0) > data.get('v_ma', 0)
                
                # Hedef Fiyatlar
                tp_fiyat = price * (1 + ka_oran / 100)
                sl_fiyat = price * (1 - zk_oran / 100)
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum, renk = "🟢 GÜÇLÜ AL", "green"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum, renk = "🔴 SAT / RİSK", "red"
                else:
                    durum, renk = "🟡 BEKLE / NÖTR", "gray"

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.subheader(f"{h.replace('.IS', '')} : {price:.2f} TL")
                        st.markdown(f"**Sinyal:** {durum} *({i_type})*")
                        
                        d1, d2 = st.columns(2)
                        with d1:
                            st.write("**Teknikler**")
                            st.write(f"RSI: `{round(data['rsi'], 1)}`")
                            st.write(f"Hacim: `{'✅' if hacim_onay else '❌'}`")
                        
                        with d2:
                            st.write("**Hedefler**")
                            st.success(f"🎯 Kar: {tp_fiyat:.2f}")
                            st.error(f"🛡️ Stop: {sl_fiyat:.2f}")

        if success_count == 0:
            st.warning("⚠️ Hisse verileri çekilemedi. Pazar kapalı olabilir veya inputs.txt dosyasını kontrol edin.")
            
        st.write(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()