import streamlit as st
import random
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Optimasi Jadwal Multi-Cabang", layout="wide")

st.title("Sistem Penjadwalan Kerja WSS - Multi Cabang")
st.write("Aplikasi ini otomatis menyesuaikan jumlah karyawan berdasarkan daftar nama yang diinput.")

# --- SIDEBAR INPUT ---
st.sidebar.header("Konfigurasi Cabang")
input_pj = st.sidebar.text_area("Daftar Nama PJ (Pisahkan dengan koma)", "Indah, Andri")
input_staf = st.sidebar.text_area("Daftar Nama Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")

# Proses Nama
LIST_PJ = [x.strip() for x in input_pj.split(",") if x.strip()]
LIST_STAF = [x.strip() for x in input_staf.split(",") if x.strip()]
SEMUA_STAF = LIST_PJ + LIST_STAF

total_org = len(SEMUA_STAF)
st.sidebar.success(f"Terdeteksi: {total_org} Karyawan")

SHIFT = ['Pagi', 'Siang', 'Break']
JUMLAH_HARI = 30

# --- LOGIKA FITNESS ---
def hitung_fitness(jadwal):
    penalti = 0
    for hari in range(JUMLAH_HARI):
        data_hari = jadwal[hari]
        for s in SHIFT:
            petugas_shift = [n for n, shf in data_hari.items() if shf == s]
            # Penalti jika shift kosong (Minimal 1 orang per shift)
            if len(petugas_shift) < 1: penalti += 1000
            # Penalti jika tidak ada PJ di shift tersebut
            pj_ada = [p for p in petugas_shift if p in LIST_PJ]
            if len(pj_ada) < 1: penalti += 500
    return 1 / (1 + penalti)

def buat_jadwal_acak():
    jadwal_sebulan = []
    for hari in range(JUMLAH_HARI):
        harian = {}
        tersedia = SEMUA_STAF.copy()
        random.shuffle(tersedia)
        
        # Pembagian adil: Setiap orang dapat jatah shift secara bergantian
        for i, nama in enumerate(tersedia):
            harian[nama] = SHIFT[i % 3]
        jadwal_sebulan.append(harian)
    return jadwal_sebulan

# --- TAMPILAN UTAMA ---
if st.button('Generate Jadwal Otomatis'):
    if total_org < 3:
        st.error("Waduh, minimal harus ada 3 orang biar shiftnya bisa dibagi!")
    else:
        with st.spinner(f'Mengoptimasi jadwal untuk {total_org} karyawan...'):
            populasi = [buat_jadwal_acak() for _ in range(30)]
            for g in range(100):
                populasi = sorted(populasi, key=lambda x: hitung_fitness(x), reverse=True)
                # Ambil yang terbaik, lakukan mutasi acak
                induk = populasi[0]
                anak = [hari.copy() for hari in induk]
                h = random.randint(0, JUMLAH_HARI-1)
                k = random.sample(SEMUA_STAF, 2)
                anak[h][k[0]], anak[h][k[1]] = anak[h][k[1]], anak[h][k[0]]
                populasi[-1] = anak
            
            hasil = populasi[0]
            df = pd.DataFrame(hasil).T
            df.columns = [f'H{i+1}' for i in range(JUMLAH_HARI)]
            
            st.dataframe(df)

            # Tombol Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Jadwal_Shift')
            
            st.download_button(
                label="📥 Download Excel Rapi",
                data=output.getvalue(),
                file_name=f"Jadwal_WSS_{total_org}_Karyawan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.subheader("Audit Keadilan (Total Break Sebulan)")
            rekap = {n: list(df.loc[n]).count('Break') for n in SEMUA_STAF}
            st.table(pd.DataFrame(rekap.items(), columns=['Nama Karyawan', 'Jumlah Break']))
