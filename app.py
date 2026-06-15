import streamlit as st
import numpy as np
import pandas as pd
import random

# ==========================================
# 1. SETUP DATASET & ATURAN (BISA KAMU SESUAIKAN)
# ==========================================

# Nama-nama karyawan WSS Dawuhan (Contoh data awal)
# PJ = Penanggung Jawab, STAF = Staf Biasa
KARYAWAN = [
    {"nama": "Nila (PJ)", "role": "PJ"},
    {"nama": "Andi (PJ)", "role": "PJ"},
    {"nama": "Budi (STAF)", "role": "STAF"},
    {"nama": "Cici (STAF)", "role": "STAF"},
    {"nama": "Dedi (STAF)", "role": "STAF"},
    {"nama": "Eka (STAF)", "role": "STAF"},
    {"nama": "Fani (STAF)", "role": "STAF"},
    {"nama": "Gita (STAF)", "role": "STAF"}
]

NUM_KARYAWAN = len(KARYAWAN)
NUM_HARI = 7  # Kita buat untuk 1 minggu (Senin - Minggu)

# Definisi Kode Shift Kerja
# 0 = Libur, 1 = Pagi, 2 = Siang, 3 = Break
KODE_SHIFT = [0, 1, 2, 3]
NAMA_SHIFT = {0: "Libur ❌", 1: "Pagi 🌅", 2: "Siang ☀️", 3: "Break 🔄"}

# ==========================================
# 2. FUNGSI HITUNG PELANGGARAN (FUNGSI FITNESS)
# ==========================================

def hitung_penalti_dan_fitness(jadwal_matriks):
    penalti = 0
    detail_pelanggaran = []
    
    for h in range(NUM_HARI):
        hari_nama = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][h]
        
        # Hitung personel yang masuk pada hari H
        jumlah_pj = 0
        jumlah_staf = 0
        total_personel_hari_ini = 0
        
        for k in range(NUM_KARYAWAN):
            shift_karyawan = jadwal_matriks[k][h]
            role_karyawan = KARYAWAN[k]["role"]
            
            if shift_karyawan != 0:  # Jika tidak libur (artinya masuk kerja)
                total_personel_hari_ini += 1
                if role_karyawan == "PJ":
                    jumlah_pj += 1
                else:
                    jumlah_staf += 1
                    
        # --- ATURAN 1: Hari Minggu Semua Wajib Masuk (Hasil Wawancara) ---
        if h == 6:  # Indeks ke-6 adalah hari Minggu
            for k in range(NUM_KARYAWAN):
                if jadwal_matriks[k][h] == 0:
                    penalti += 100
                    detail_pelanggaran.append(f"Minggu: {KARYAWAN[k]['nama']} malah Libur! (Penalti +100)")
                    
        # --- ATURAN 2: Jatah Libur Sehari Maksimal 1 Orang ---
        jumlah_libur_hari_ini = sum(1 for k in range(NUM_KARYAWAN) if jadwal_matriks[k][h] == 0)
        if h != 6 and jumlah_libur_hari_ini > 1:
            penalti += 40
            detail_pelanggaran.append(f"{hari_nama}: Yang libur ada {jumlah_libur_hari_ini} orang, aturan maksimal 1 orang! (Penalti +40)")
            
        # --- ATURAN 3: Minimal Harus Ada 1 PJ yang Masuk ---
        if total_personel_hari_ini > 0 and jumlah_pj == 0:
            penalti += 100
            detail_pelanggaran.append(f"{hari_nama}: Toko buka tapi tidak ada PJ asli yang masuk! (Penalti +100)")
            
        # --- ATURAN 4: Total Personel Per Hari Minimal 3 Orang ---
        if total_personel_hari_ini < 3:
            penalti += 80
            detail_pelanggaran.append(f"{hari_nama}: Jumlah pekerja kurang dari 3 orang! Cuma ada {total_personel_hari_ini} orang. (Penalti +80)")

    # --- ATURAN 5: Tidak Boleh Shift Break (3) Dua Hari Berturut-turut ---
    for k in range(NUM_KARYAWAN):
        for h in range(NUM_HARI - 1):
            if jadwal_matriks[k][h] == 3 and jadwal_matriks[k][h+1] == 3:
                penalti += 50
                hari_1 = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][h]
                hari_2 = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][h+1]
                detail_pelanggaran.append(f"{KARYAWAN[k]['nama']}: Kena shift break berurutan di hari {hari_1} & {hari_2}! (Penalti +50)")

    # Rumus Nilai Fitness Skripsi
    fitness = 1 / (1 + penalti)
    return fitness, penalti, detail_pelanggaran

# ==========================================
# 3. LOGIKA ALGORITMA GENETIKA (OTAK OPTIMASI)
# ==========================================

def buat_jadwal_acak():
    # Membuat satu susunan jadwal acak total (Kromosom)
    return np.random.choice(KODE_SHIFT, size=(NUM_KARYAWAN, NUM_HARI))

def jalankan_optimasi(ukuran_populasi, generasi_maksimal):
    # Tahap 1: Inisialisasi Populasi Awal (Generasi ke-0)
    populasi = [buat_jadwal_acak() for _ in range(ukuran_populasi)]
    
    riwayat_fitness = []
    jadwal_terbaik = populasi[0]
    fitness_terbaik = 0
    penalti_terbaik = 9999
    pelanggaran_terbaik = []
    
    # Ambil sampel acak awal untuk nanti ditampilkan di Sub 4.1.1
    jadwal_acak_awal = np.copy(populasi[0])
    _, penalti_awal, pelanggaran_awal = hitung_penalti_dan_fitness(jadwal_acak_awal)

    # Proses Evolusi Per Generasi
    for gen in range(generasi_maksimal):
        # Hitung skor semua jadwal di populasi saat ini
        skor_populasi = [hitung_penalti_dan_fitness(ind) for ind in populasi]
        
        # Cari siapa yang terbaik di generasi ini
        for i, (fit, pen, det) in enumerate(skor_populasi):
            if fit > fitness_terbaik:
                fitness_terbaik = fit
                penalti_terbaik = pen
                jadwal_terbaik = populasi[i]
                pelanggaran_terbaik = det
                
        riwayat_fitness.append(fitness_terbaik)
        
        # Seleksi: Ambil jadwal-jadwal yang lumayan bagus (Metode Turnamen sederhana)
        populasi_baru = []
        for _ in range(ukuran_populasi):
            kandidat_1 = random.choice(populasi)
            kandidat_2 = random.choice(populasi)
            fit_1, _, _ = hitung_penalti_dan_fitness(kandidat_1)
            fit_2, _, _ = hitung_penalti_dan_fitness(kandidat_2)
            populasi_baru.append(np.copy(kandidat_1 if fit_1 > fit_2 else kandidat_2))
            
        # Crossover (Kawin Silang jadwal) & Mutasi (Ubah Acak Jadwal)
        for i in range(0, ukuran_populasi, 2):
            if random.random() < 0.8:  # Crossover Rate 80%
                titik_potong = random.randint(1, NUM_HARI - 1)
                populasi_baru[i][:, titik_potong:], populasi_baru[i+1][:, titik_potong:] = \
                populasi_baru[i+1][:, titik_potong:], np.copy(populasi_baru[i][:, titik_potong:])
                
            # Mutasi sebesar 10%
            if random.random() < 0.1:
                k_acak = random.randint(0, NUM_KARYAWAN - 1)
                h_acak = random.randint(0, NUM_HARI - 1)
                populasi_baru[i][k_acak][h_acak] = random.choice(KODE_SHIFT)
                
        populasi = populasi_baru
        
    return jadwal_acak_awal, penalti_awal, pelanggaran_awal, jadwal_terbaik, fitness_terbaik, penalti_terbaik, pelanggaran_terbaik, riwayat_fitness

# ==========================================
# 4. TAMPILAN DASHBOARD (STREAMLIT)
# ==========================================

st.set_page_config(layout="wide")
st.title("📊 Dashboard Optimasi Penjadwalan WSS Dawuhan")
st.write("Aplikasi Eksperimen Kuantitatif Algoritma Genetika")

# Sidebar untuk Atur Parameter Uji Coba (Untuk Data Bab 4)
st.sidebar.header("🎛️ Parameter Algoritma Genetika")
pop_size = st.sidebar.slider("Ukuran Populasi (Population Size)", min_value=10, max_value=100, value=50, step=10)
max_gen = st.sidebar.slider("Jumlah Generasi (Max Generation)", min_value=50, max_value=500, value=100, step=50)

if st.sidebar.button("🚀 Jalankan Eksperimen Optimasi"):
    
    # Eksekusi Algoritma
    js_awal, pen_awal, pel_awal, js_akhir, fit_akhir, pen_akhir, pel_akhir, riwayat = jalankan_optimasi(pop_size, max_gen)
    
    # --- BAGIAN 1: DATA UNTUK SUB-BAB 4.1.1 (KONDISI AWAL YANG RUSAK) ---
    st.header("1. Data Inisialisasi Awal (Generasi ke-0) - Bahan Sub-bab 4.1.1")
    st.subheader(f"Total Nilai Penalti Awal: {pen_awal} (Nilai Eror Tinggi)")
    
    df_awal = pd.DataFrame(js_awal, columns=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
    df_awal.insert(0, "Nama Karyawan", [k["nama"] for k in KARYAWAN])
    df_awal_tampil = df_awal.copy()
    for col in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
        df_awal_tampil[col] = df_awal_tampil[col].map(NAMA_SHIFT)
        
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("💬 **Jadwal Acak Awal (Silakan Screenshot untuk Sub-bab 4.1.1):**")
        st.dataframe(df_awal_tampil, use_container_width=True)
    with col2:
        st.write("⚠️ **Daftar Pelanggaran Aturan Toko di Awal:**")
        for p in pel_awal[:6]:  # Tampilkan 6 contoh eror saja biar tidak kepanjangan
            st.error(p)
            
    st.markdown("---")
    
    # --- BAGIAN 2: DATA GRAFIK UNTUK SUB-BAB 4.3 (VISUALISASI KONVERGENSI) ---
    st.header("2. Grafik Performa Konvergensi Fitness - Bahan Sub-bab 4.3")
    st.write("💬 **Silakan Screenshot grafik garis di bawah ini untuk menunjukkan peningkatan performa rumus algoritmamu:**")
    df_grafik = pd.DataFrame({"Generasi": range(len(riwayat)), "Nilai Fitness": riwayat})
    st.line_chart(df_grafik.set_index("Generasi"))
    
    st.markdown("---")
    
    # --- BAGIAN 3: DATA JADWAL OPTIMAL UNTUK SUB-BAB 4.4.1 (HASIL AKHIR) ---
    st.header("3. Hasil Output Penjadwalan Optimal Akhir - Bahan Sub-bab 4.4.1")
    st.subheader(f"✅ Nilai Fitness Akhir: {fit_akhir:.5f} | Sisa Penalti Pelanggaran: {pen_akhir}")
    
    df_akhir = pd.DataFrame(js_akhir, columns=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
    df_akhir.insert(0, "Nama Karyawan", [k["nama"] for k in KARYAWAN])
    df_akhir_tampil = df_akhir.copy()
    for col in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
        df_akhir_tampil[col] = df_akhir_tampil[col].map(NAMA_SHIFT)
        
    col3, col4 = st.columns([2, 1])
    with col3:
        st.write("🏆 **Jadwal Akhir yang Sudah Bersih Eror (Silakan Screenshot untuk Hasil Skripsi):**")
        st.dataframe(df_akhir_tampil, use_container_width=True)
    with col4:
        st.write("📋 **Status Evaluasi Aturan Akhir:**")
        if pen_akhir == 0:
            st.success("Sempurna! Semua aturan hasil wawancara berhasil dipenuhi komputer (0 Pelanggaran).")
        else:
            st.warning(f"Masih ada {pen_akhir} nilai penalti eror. Coba naikkan Ukuran Populasi atau Generasi di sidebar kiri!")
            for p in pel_akhir[:5]:
                st.write(p)
else:
    st.info("💡 Silakan klik tombol **'Jalankan Eksperimen Optimasi'** di sidebar menu sebelah kiri untuk memulai komputasi matematika.")
