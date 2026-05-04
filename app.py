import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Penjadwalan WSS Dawuhan", layout="wide")

st.title("Sistem Penjadwalan Shift WSS Dawuhan")
st.write("Prototipe Optimasi Jadwal Kerja menggunakan Algoritma Genetika")

# 1. KONFIGURASI DATA
KARYAWAN = {
    'PJ': ['Indah', 'Andri'],
    'STAF': ['Tika', 'Firman', 'Elan', 'Nila', 'Novi', 'Alfi']
}
SEMUA_STAF = KARYAWAN['PJ'] + KARYAWAN['STAF']
SHIFT = ['Pagi', 'Siang', 'Break']
JUMLAH_HARI = 30

# 2. FUNGSI CEK ATURAN (FITNESS)
def hitung_fitness(jadwal):
    penalti = 0
    for hari in range(JUMLAH_HARI):
        data_hari = jadwal[hari]
        is_minggu = (hari + 1) % 7 == 0
        
        for s in SHIFT:
            petugas_shift = [nama for nama, shf in data_hari.items() if shf == s]
            pj_di_shift = [p for p in petugas_shift if p in KARYAWAN['PJ']]
            if len(pj_di_shift) < 1:
                penalti += 100 
        
        siapa_libur = [nama for nama, shf in data_hari.items() if shf == 'Libur']
        if is_minggu:
            if len(siapa_libur) > 0: penalti += 50
        else:
            if len(siapa_libur) > 1: penalti += 20
            
    for hari in range(JUMLAH_HARI - 1):
        for nama in SEMUA_STAF:
            shift_skrg = jadwal[hari][nama]
            shift_besok = jadwal[hari+1][nama]
            if shift_skrg == 'Break' and shift_besok == 'Pagi':
                penalti += 10
                
    return 1 / (1 + penalti)

# 3. MEMBUAT JADWAL ACAK
def buat_jadwal_acak():
    jadwal_sebulan = []
    for hari in range(JUMLAH_HARI):
        is_minggu = (hari + 1) % 7 == 0
        harian = {}
        staf_tersedia = SEMUA_STAF.copy()
        random.shuffle(staf_tersedia)
        if is_minggu:
            for i, nama in enumerate(staf_tersedia):
                harian[nama] = SHIFT[i % 3]
        else:
            harian[staf_tersedia[0]] = 'Libur'
            for i, nama in enumerate(staf_tersedia[1:]):
                harian[nama] = SHIFT[i % 3]
        jadwal_sebulan.append(harian)
    return jadwal_sebulan

# 4. PROSES OPTIMASI
if st.button('Generate Jadwal WSS'):
    with st.spinner('Menghitung kombinasi jadwal terbaik...'):
        populasi = [buat_jadwal_acak() for _ in range(20)]
        generasi = 100
        for g in range(generasi):
            populasi = sorted(populasi, key=lambda x: hitung_fitness(x), reverse=True)
            terbaik = populasi[:5]
            anak_baru = []
            for _ in range(15):
                induk = random.choice(terbaik)
                anak = [hari.copy() for hari in induk]
                h = random.randint(0, JUMLAH_HARI-1)
                k1, k2 = random.sample(SEMUA_STAF, 2)
                anak[h][k1], anak[h][k2] = anak[h][k2], anak[h][k1]
                anak_baru.append(anak)
            populasi = terbaik + anak_baru
        
        hasil = populasi[0]
        df = pd.DataFrame(hasil).T
        df.columns = [f'Hr {i+1}' for i in range(JUMLAH_HARI)]
        
        st.success("Berhasil! Berikut adalah jadwal optimal:")
        st.dataframe(df)

        # Audit sederhana
        st.subheader("Ringkasan Shift Break")
        rekap = {n: list(df.loc[n]).count('Break') for n in SEMUA_STAF}
        st.write(rekap)
