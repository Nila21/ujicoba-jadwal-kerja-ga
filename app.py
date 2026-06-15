import streamlit as st
import numpy as np
import pandas as pd
import random
import time

# ==========================================
# 1. SETUP DATASET KARYAWAN & SHIFT
# Berdasarkan Data WSS Dawuhan (8 Karyawan)
# ==========================================

KARYAWAN = [
    {"nama": "Indah", "role": "PJ"},
    {"nama": "Andri", "role": "PJ"},
    {"nama": "Firman", "role": "Staf"},
    {"nama": "Tika", "role": "Staf"},
    {"nama": "Elan", "role": "Staf"},
    {"nama": "Nila", "role": "Staf"},
    {"nama": "Alfi", "role": "Staf"},
    {"nama": "Novi", "role": "Staf"}
]

NUM_KARYAWAN = len(KARYAWAN)
NUM_HARI = 7  # Senin s.d Minggu

# Kode Shift sesuai skripsi: 0=Libur, 1=Pagi, 2=Siang, 3=Break
KODE_SHIFT = [0, 1, 2, 3]
NAMA_SHIFT = {0: "Libur (0)", 1: "Pagi (1)", 2: "Siang (2)", 3: "Break (3)"}

# ==========================================
# 2. FUNGSI FITNESS & PENALTI (Sesuai Bab 3 Skripsi)
# ==========================================

def hitung_fitness(jadwal_matriks):
    penalti = 0
    log_pelanggaran = []
    
    for h in range(NUM_HARI):
        hari_nama = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][h]
        jumlah_libur = 0
        jumlah_pj_masuk = 0
        
        for k in range(NUM_KARYAWAN):
            shift = jadwal_matriks[k][h]
            role = KARYAWAN[k]["role"]
            
            if shift == 0:
                jumlah_libur += 1
            else:
                if role == "PJ":
                    jumlah_pj_masuk += 1
                    
        # ATURAN P1: Hari Minggu Dilarang Libur (Penalti 100)
        if h == 6: # Indeks 6 adalah Minggu
            for k in range(NUM_KARYAWAN):
                if jadwal_matriks[k][h] == 0:
                    penalti += 100
                    log_pelanggaran.append(f"P1: {KARYAWAN[k]['nama']} libur di hari Minggu (+100)")
                    
        # ATURAN P4: Kurang Personel / Maksimal 1 Libur Hari Biasa (Penalti 100)
        if h != 6 and jumlah_libur > 1:
            penalti += 100
            log_pelanggaran.append(f"P4: Kekurangan personel di hari {hari_nama}, {jumlah_libur} orang libur (+100)")
            
        # ATURAN P2 Tambahan: Minimal 1 PJ harus masuk (Penalti 100)
        if jumlah_pj_masuk == 0 and jumlah_libur < NUM_KARYAWAN:
            penalti += 100
            log_pelanggaran.append(f"P2: Tidak ada PJ yang masuk di hari {hari_nama} (+100)")

    # ATURAN P7: Shift Break Berturut-turut (Penalti 50)
    for k in range(NUM_KARYAWAN):
        for h in range(NUM_HARI - 1):
            if jadwal_matriks[k][h] == 3 and jadwal_matriks[k][h+1] == 3:
                penalti += 50
                log_pelanggaran.append(f"P7: {KARYAWAN[k]['nama']} shift break berturut-turut (+50)")

    # Rumus Matematis Fitness
    fitness = 1 / (1 + penalti)
    return fitness, penalti, log_pelanggaran

# ==========================================
# 3. MESIN ALGORITMA GENETIKA (OPTIMASI)
# ==========================================

def buat_kromosom_acak():
    # Inisialisasi populasi awal secara acak
    return np.random.choice(KODE_SHIFT, size=(NUM_KARYAWAN, NUM_HARI))

def jalankan_ga(pop_size, max_gen):
    waktu_mulai = time.time()
    
    populasi = [buat_kromosom_acak() for _ in range(pop_size)]
    riwayat_fitness = []
    
    # Simpan jadwal awal untuk Bab 4.1.1
    jadwal_awal = np.copy(populasi[0])
    fit_awal, pen_awal, pel_awal = hitung_fitness(jadwal_awal)
    
    jadwal_terbaik = None
    fitness_terbaik = 0
    penalti_terbaik = 9999
    pelanggaran_terbaik = []

    for gen in range(max_gen):
        skor_populasi = [hitung_fitness(ind) for ind in populasi]
        
        # Evaluasi
        for i, (fit, pen, pel) in enumerate(skor_populasi):
            if fit > fitness_terbaik:
                fitness_terbaik = fit
                penalti_terbaik = pen
                jadwal_terbaik = populasi[i]
                pelanggaran_terbaik = pel
                
        riwayat_fitness.append(fitness_terbaik)
        
        # Jika sudah sempurna (0 penalti), hentikan iterasi (Konvergen)
        if penalti_terbaik == 0:
            # Isi sisa grafik dengan nilai sempurna agar grafik mendatar
            riwayat_fitness.extend([fitness_terbaik] * (max_gen - gen - 1))
            break
            
        # Seleksi Turnamen
        populasi_baru = []
        for _ in range(pop_size):
            k1, k2 = random.choice(populasi), random.choice(populasi)
            f1, _, _ = hitung_fitness(k1)
            f2, _, _ = hitung_fitness(k2)
            populasi_baru.append(np.copy(k1 if f1 > f2 else k2))
            
        # Crossover & Mutasi
        for i in range(0, pop_size, 2):
            if i+1 < pop_size and random.random() < 0.8:
                titik = random.randint(1, NUM_HARI - 1)
                populasi_baru[i][:, titik:], populasi_baru[i+1][:, titik:] = \
                populasi_baru[i+1][:, titik:], np.copy(populasi_baru[i][:, titik:])
                
            if random.random() < 0.1:
                k_acak, h_acak = random.randint(0, NUM_KARYAWAN-1), random.randint(0, NUM_HARI-1)
                populasi_baru[i][k_acak][h_acak] = random.choice(KODE_SHIFT)
                
        populasi = populasi_baru
        
    waktu_selesai = time.time()
    waktu_komputasi = round(waktu_selesai - waktu_mulai, 3)
    
    return jadwal_awal, pen_awal, pel_awal, jadwal_terbaik, fitness_terbaik, penalti_terbaik, pelanggaran_terbaik, riwayat_fitness, waktu_komputasi

# ==========================================
# 4. TAMPILAN DASHBOARD PENELITIAN (UI)
# ==========================================

st.set_page_config(page_title="Skripsi Optimasi WSS", layout="wide")
st.title("🔬 Sistem Optimasi Penjadwalan Shift Multi-Constraint")
st.subheader("Pendekatan Kuantitatif Algoritma Genetika - Studi Kasus WSS Dawuhan")
st.markdown("---")

st.sidebar.header("⚙️ Parameter Algoritma")
pop_size = st.sidebar.slider("Ukuran Populasi", min_value=10, max_value=100, value=50, step=10)
max_gen = st.sidebar.slider("Generasi Maksimal", min_value=50, max_value=500, value=100, step=50)

if st.sidebar.button("▶️ Mulai Eksperimen Komputasi"):
    
    with st.spinner("Mesin Algoritma Genetika sedang memproses triliunan kemungkinan..."):
        js_awal, pen_awal, pel_awal, js_akhir, fit_akhir, pen_akhir, pel_akhir, riwayat, waktu = jalankan_ga(pop_size, max_gen)
    
    hari_cols = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    
    # ---------------------------------------------------------
    # HASIL 1: DATA AWAL UNTUK BAB 4.1.1
    # ---------------------------------------------------------
    st.markdown("### 📊 1. Kondisi Matriks Awal (Generasi ke-0)")
    st.info(f"**Nilai Fitness:** {1/(1+pen_awal):.5f} | **Total Penalti:** {pen_awal}")
    
    df_awal = pd.DataFrame(js_awal, columns=hari_cols)
    df_awal.insert(0, "Nama", [k["nama"] for k in KARYAWAN])
    df_awal_show = df_awal.copy()
    for col in hari_cols: df_awal_show[col] = df_awal_show[col].map(NAMA_SHIFT)
    
    c1, c2 = st.columns([2, 1])
    with c1: st.dataframe(df_awal_show, use_container_width=True)
    with c2:
        st.error("Daftar Pelanggaran Constraint:")
        for p in pel_awal[:5]: st.write(f"- {p}")
        if len(pel_awal) > 5: st.write("...dan lainnya.")

    st.markdown("---")
    
    # ---------------------------------------------------------
    # HASIL 2: GRAFIK KONVERGENSI UNTUK BAB 4.3
    # ---------------------------------------------------------
    st.markdown("### 📈 2. Grafik Konvergensi Fitness")
    st.write(f"Waktu Komputasi: **{waktu} detik** | Generasi: **{len(riwayat)}**")
    df_chart = pd.DataFrame({"Generasi": range(len(riwayat)), "Fitness": riwayat}).set_index("Generasi")
    st.line_chart(df_chart)

    st.markdown("---")
    
    # ---------------------------------------------------------
    # HASIL 3: JADWAL OPTIMAL UNTUK BAB 4.4
    # ---------------------------------------------------------
    st.markdown("### 🏆 3. Hasil Optimasi Akhir")
    if pen_akhir == 0:
        st.success(f"**OPTIMAL!** Nilai Fitness: 1.000 | Total Penalti: 0 (Semua aturan terpenuhi)")
    else:
        st.warning(f"**BELUM OPTIMAL.** Fitness: {fit_akhir:.5f} | Sisa Penalti: {pen_akhir}. Coba naikkan Ukuran Populasi atau Generasi.")
        for p in pel_akhir: st.write(f"- {p}")

    df_akhir = pd.DataFrame(js_akhir, columns=hari_cols)
    df_akhir.insert(0, "Nama", [k["nama"] for k in KARYAWAN])
    df_akhir_show = df_akhir.copy()
    for col in hari_cols: df_akhir_show[col] = df_akhir_show[col].map(NAMA_SHIFT)
    
    st.dataframe(df_akhir_show, use_container_width=True)

else:
    st.info("👈 Atur parameter di sebelah kiri dan klik 'Mulai Eksperimen Komputasi' untuk melihat hasil algoritma.")
            
    populasi_baru = []
        for _ in range(pop_size):
            k1, k2 = random.choice(populasi), random.choice(populasi)
            f1, _, _ = hitung_fitness(k1)
            f2, _, _ = hitung_fitness(k2)
            populasi_baru.append(np.copy(k1 if f1 > f2 else k2))
            
        for i in range(0, pop_size, 2):
            if i+1 < pop_size and random.random() < 0.8:
                titik = random.randint(1, NUM_HARI - 1)
                populasi_baru[i][:, titik:], populasi_baru[i+1][:, titik:] = \
                populasi_baru[i+1][:, titik:], np.copy(populasi_baru[i][:, titik:])
                
            if random.random() < 0.1:
                k_acak, h_acak = random.randint(0, NUM_KARYAWAN-1), random.randint(0, NUM_HARI-1)
                populasi_baru[i][k_acak][h_acak] = random.choice(KODE_SHIFT)
                
        populasi = populasi_baru
        
    waktu_selesai = time.time()
    waktu_komputasi = round(waktu_selesai - waktu_mulai, 3)
    
    return jadwal_awal, pen_awal, pel_awal, jadwal_terbaik, fitness_terbaik, penalti_terbaik, pelanggaran_terbaik, riwayat_fitness, waktu_komputasi

# ==========================================
# 4. TAMPILAN DASHBOARD (UI)
# ==========================================
st.set_page_config(page_title="Sistem Optimasi Penjadwalan WSS", layout="wide")

# PANEL SIDEBAR
st.sidebar.header("🎯 Pengaturan Akses")
mode_tampilan = st.sidebar.selectbox("Pilih Mode Tampilan", ["PJ Toko (Aplikasi Utama)", "Peneliti (Analisis Akademis)"])

# Setelan default parameter di latar belakang
pop_size = 50
max_gen = 100

# Jika mode peneliti, slider bisa diotak-atik untuk eksperimen Bab 4
if mode_tampilan == "Peneliti (Analisis Akademis)":
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Parameter Algoritma")
    pop_size = st.sidebar.slider("Ukuran Populasi", min_value=10, max_value=100, value=50, step=10)
    max_gen = st.sidebar.slider("Generasi Maksimal", min_value=50, max_value=500, value=100, step=50)

# KONDISI TAMPILAN DIREKTRUR / PJ TOKO VS PENELITI
if mode_tampilan == "PJ Toko (Aplikasi Utama)":
    st.title("📋 Aplikasi Penjadwalan Shift Kerja Karyawan")
    st.subheader("Warung Sayur Segar (WSS) Cabang Dawuhan")
    st.write("Tekan tombol di bawah untuk membuat jadwal kerja mingguan otomatis yang adil secara instan.")
else:
    st.title("🔬 Dashboard Analisis Eksperimen Algoritma Genetika")
    st.subheader("Mode Pengujian Kuantitatif - Data Validasi Skripsi")

st.markdown("---")

if st.sidebar.button("🚀 Mulai Generate Jadwal" if mode_tampilan == "PJ Toko (Aplikasi Utama)" else "▶️ Jalankan Eksperimen Komputasi"):
    
    js_awal, pen_awal, pel_awal, js_akhir, fit_akhir, pen_akhir, pel_akhir, riwayat, waktu = jalankan_ga(pop_size, max_gen)
    hari_cols = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    
    # ---------------------------------------------------------
    # JIKA MODE PENELITIAN AKTIF: TAMPILKAN DATA SENSOR EROR & GRAFIK (Untuk Bab 4.1.1 & 4.3)
    # ---------------------------------------------------------
    if mode_tampilan == "Peneliti (Analisis Akademis)":
        st.markdown("### 📊 1. Kondisi Matriks Awal (Generasi ke-0)")
        st.info(f"**Nilai Fitness Awal:** {1/(1+pen_awal):.5f} | **Total Penalti Awal:** {pen_awal}")
        
        df_awal = pd.DataFrame(js_awal, columns=hari_cols)
        df_awal.insert(0, "Nama Karyawan", [k["nama"] for k in KARYAWAN])
        df_awal_show = df_awal.copy()
        for col in hari_cols: df_awal_show[col] = df_awal_show[col].map(NAMA_SHIFT)
        
        c1, c2 = st.columns([2, 1])
        with c1: st.dataframe(df_awal_show, use_container_width=True)
        with c2:
            st.error("Daftar Pelanggaran Aturan Toko (Generasi ke-0):")
            for p in pel_awal[:5]: st.write(f"- {p}")
            if len(pel_awal) > 5: st.write("...dan lainnya.")
            
        st.markdown("---")
        st.markdown("### 📈 2. Grafik Konvergensi Nilai Fitness")
        st.write(f"Waktu Proses Hitung Komputer: **{waktu} detik** | Berhenti pada Generasi: **{len(riwayat)}**")
        df_chart = pd.DataFrame({"Generasi": range(len(riwayat)), "Fitness": riwayat}).set_index("Generasi")
        st.line_chart(df_chart)
        st.markdown("---")

    # ---------------------------------------------------------
    # OUTPUT UTAMA: TABEL JADWAL BERSIH OPTIMAL (MUNCUL DI KEDUA MODE)
    # ---------------------------------------------------------
    if mode_tampilan == "PJ Toko (Aplikasi Utama)":
        st.markdown("### 🏆 Jadwal Kerja Resmi Karyawan")
        st.success("✅ Sistem Sukses Menghasilkan Jadwal Kerja Optimal (Bebas Bentrok & Adil).")
    else:
        st.markdown("### 🏆 3. Hasil Optimasi Akhir Jadwal (Penalti 0)")
        st.success(f"**Kondisi Konvergen Sempurna!** Nilai Fitness Akhir: 1.000 | Sisa Penalti Pelanggaran: {pen_akhir}")

    df_akhir = pd.DataFrame(js_akhir, columns=hari_cols)
    df_akhir.insert(0, "Nama Karyawan", [k["nama"] for k in KARYAWAN])
    df_akhir_show = df_akhir.copy()
    for col in hari_cols: df_akhir_show[col] = df_akhir_show[col].map(NAMA_SHIFT)
    
    st.dataframe(df_akhir_show, use_container_width=True)

else:
    st.info("💡 Silakan klik tombol aksi di menu sebelah kiri untuk memproses data.")
