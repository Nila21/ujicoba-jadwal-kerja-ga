import streamlit as st
import random
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Optimasi Jadwal Multi-Cabang", layout="wide")

st.title("Sistem Penjadwalan Kerja WSS - Edisi Multi-Cabang")
st.write("Sesuaikan daftar karyawan sesuai cabang penelitian Anda.")

# --- SIDEBAR INPUT ---
st.sidebar.header("Konfigurasi Cabang")
input_pj = st.sidebar.text_area("Daftar Nama PJ (Pisahkan dengan koma)", "Indah, Andri")
input_staf = st.sidebar.text_area("Daftar Nama Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")

LIST_PJ = [x.strip() for x in input_pj.split(",") if x.strip()]
LIST_STAF = [x.strip() for x in input_staf.split(",") if x.strip()]
SEMUA_STAF = LIST_PJ + LIST_STAF

st.sidebar.info(f"Total Karyawan: {len(SEMUA_STAF)} orang")
SHIFT = ['Pagi', 'Siang', 'Break']
JUMLAH_HARI = 30

# --- LOGIKA ALGORITMA ---
def hitung_fitness(jadwal):
    penalti = 0
    for hari in range(JUMLAH_HARI):
        data_hari = jadwal[hari]
        for s in SHIFT:
            petugas_shift = [nama for nama, shf in data_hari.items() if shf == s]
            pj_di_shift = [p for p in petugas_shift if p in LIST_PJ]
            if len(pj_di_shift) < 1:
                penalti += 100 
    return 1 / (1 + penalti)

def buat_jadwal_acak():
    jadwal_sebulan = []
    for hari in range(JUMLAH_HARI):
        harian = {}
        staf_tersedia = SEMUA_STAF.copy()
        random.shuffle(staf_tersedia)
        for i, nama in enumerate(staf_tersedia):
            harian[nama] = SHIFT[i % 3]
        jadwal_sebulan.append(harian)
    return jadwal_sebulan

# --- TAMPILAN UTAMA ---
if st.button('Generate Jadwal Cabang Ini'):
    if len(SEMUA_STAF) < 3:
        st.error("Minimal harus ada 3 karyawan!")
    else:
        with st.spinner('Menghitung optimasi...'):
            populasi = [buat_jadwal_acak() for _ in range(20)]
            for g in range(50):
                populasi = sorted(populasi, key=lambda x: hitung_fitness(x), reverse=True)
                terbaik = populasi[:5]
                induk = random.choice(terbaik)
                anak = [hari.copy() for hari in induk]
                populasi = terbaik + [anak]
            
            hasil = populasi[0]
            df = pd.DataFrame(hasil).T
            df.columns = [f'H{i+1}' for i in range(JUMLAH_HARI)]
            
            st.success(f"Berhasil membuat jadwal!")
            st.dataframe(df)

            # --- FITUR DOWNLOAD EXCEL RAPI ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Jadwal_Shift')
            
            st.download_button(
                label="📥 Download Jadwal Versi Excel Rapi",
                data=output.getvalue(),
                file_name=f"Jadwal_Shift_WSS_{len(SEMUA_STAF)}_Orang.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.subheader("Audit Jatah Break")
            rekap = {n: list(df.loc[n]).count('Break') for n in SEMUA_STAF}
            st.write(rekap)
