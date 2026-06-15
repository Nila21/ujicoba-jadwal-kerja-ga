import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import io
import matplotlib.pyplot as plt

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Optimasi Penjadwalan WSS", layout="wide")

st.title("Aplikasi Optimasi Penjadwalan Shift Kerja (Algoritma Genetika)")
st.markdown("Berdasarkan aturan penjadwalan toko dan analisis constraint (bobot disamakan).")

# --- INPUT DATA KARYAWAN ---
st.sidebar.header("Pengaturan Karyawan")
pj_input = st.sidebar.text_input("Nama PJ Toko (pisahkan dengan koma)", "Indah, Andri")
staf_input = st.sidebar.text_input("Nama Staf Toko (pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Alfi, Novi")

pj_list = [x.strip() for x in pj_input.split(",") if x.strip()]
staf_list = [x.strip() for x in staf_input.split(",") if x.strip()]
all_emp = pj_list + staf_list
num_emp = len(all_emp)

# --- PARAMETER ALGORITMA GENETIKA ---
st.sidebar.header("Parameter Algoritma Genetika")
pop_size = st.sidebar.number_input("Ukuran Populasi", min_value=10, max_value=200, value=50)
max_gen = st.sidebar.number_input("Maksimal Generasi", min_value=10, max_value=1000, value=300)
mut_rate = st.sidebar.slider("Probabilitas Mutasi", 0.01, 1.0, 0.1)

# Shifts: 0=Pagi, 1=Siang, 2=Break, 3=Libur
SHIFT_NAMES = {0: "Pagi", 1: "Siang", 2: "Break", 3: "Libur"}

# --- FUNGSI ALGORITMA GENETIKA ---
def generate_random_day(day_index):
    # Hari minggu (asumsi hari ke-7, index 6)
    is_sunday = (day_index % 7 == 6)
    
    day_sched = [0] * num_emp
    if is_sunday:
        # Tidak ada yang boleh libur pada hari Minggu
        shifts = [0, 1, 2] * 3
        shifts = shifts[:num_emp]
        random.shuffle(shifts)
        day_sched = shifts
    else:
        # Maksimal 1 orang libur per hari
        num_off = random.choice([0, 1])
        if num_off == 1:
            off_idx = random.randint(0, num_emp - 1)
            shifts = [0, 1, 2] * 3
            shifts = shifts[:num_emp - 1]
            random.shuffle(shifts)
            idx = 0
            for i in range(num_emp):
                if i == off_idx:
                    day_sched[i] = 3
                else:
                    day_sched[i] = shifts[idx]
                    idx += 1
        else:
            shifts = [0, 1, 2] * 3
            shifts = shifts[:num_emp]
            random.shuffle(shifts)
            day_sched = shifts
    return day_sched

def create_individual():
    return [generate_random_day(d) for d in range(30)]

# --- DEFINISI BOBOT (Letakkan di bagian atas file) ---
W_HARD = 100
W_SOFT = 50

# --- FUNGSI ALGORITMA GENETIKA ---
def calculate_fitness(ind):
    penalty = 0
    libur_counts = [0] * num_emp
    
    for d in range(30):
        day_sched = ind[d]
        is_sunday = (d % 7 == 6)
        
        c_pagi = day_sched.count(0)
        c_siang = day_sched.count(1)
        c_break = day_sched.count(2)
        c_libur = day_sched.count(3)
        
        for i, s in enumerate(day_sched):
            if s == 3:
                # PERBAIKAN: Gunakan [i] agar setiap karyawan dihitung masing-masing
                libur_counts[i] += 1 
                
        # 1. HARD: Constraint Libur
        if is_sunday and c_libur > 0:
            penalty += W_HARD * c_libur
        elif not is_sunday and c_libur > 1:
            penalty += W_HARD * (c_libur - 1)
            
        # 2. HARD: Tidak boleh ada dua PJ di shift yang sama
        pj_shifts = [day_sched[i] for i in range(len(pj_list))]
        for s in [0, 1, 2]:
            if pj_shifts.count(s) > 1:
                penalty += W_HARD
                
        # 3. SOFT: Distribusi Karyawan per Shift (Ganti W_LOW jadi W_SOFT)
        if c_libur == 0:
            if c_pagi < 2 or c_siang < 2 or c_break < 2: penalty += W_SOFT
        elif c_libur == 1:
            if c_pagi < 2 or c_siang < 2 or c_break < 2: penalty += W_SOFT

        # 4 & 5. SOFT: Constraint Hari Berurutan (Ganti W_LOW jadi W_SOFT)
        if d < 29:
            next_sched = ind[d+1]
            for i in range(num_emp):
                s_today = day_sched[i]
                s_next = next_sched[i]
                if (s_today == 2 and s_next == 2) or (s_today == 1 and s_next == 2):
                    penalty += W_SOFT
                    
    # 6. SOFT: Libur 3 hari dalam sebulan (Ganti W_MED jadi W_SOFT)
    for lc in libur_counts:
        if lc != 3:
            penalty += W_HARD * abs(lc - 3)
            
    return penalty


# Tambahkan rate=0.85 di dalam kurung
def crossover(p1, p2, rate=0.85): 
    if random.random() < rate:
        pt = random.randint(1, len(p1) - 2) 
        c1 = p1[:pt] + p2[pt:]
        c2 = p2[:pt] + p1[pt:]
        return c1, c2
    else:
        return p1.copy(), p2.copy()


def mutate(ind, rate):
    for d in range(30):
        if random.random() < rate:
            ind[d] = generate_random_day(d)
    return ind

# --- TAMPILAN ANTARMUKA TABS ---
tab1, tab2 = st.tabs(["🖥️ Aplikasi Penjadwalan (PJ Toko)", "📊 Analisis GA (Peneliti)"])

with tab1:
    st.header("Buat Jadwal Shift Karyawan")
    if st.button("Mulai Optimasi Jadwal"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()
        
        # Inisialisasi
        population = [create_individual() for _ in range(pop_size)]
        best_ind = None
        best_penalty = float('inf')
        history = []
        
        # Loop Generasi
        for gen in range(max_gen):
            penalties = [calculate_fitness(ind) for ind in population]
            min_pen = min(penalties)
            
            if min_pen < best_penalty:
                best_penalty = min_pen
                best_ind = population[penalties.index(min_pen)]
                
            history.append(best_penalty)
            
            # Seleksi, Crossover, dan Mutasi (Tournament Selection)
            new_pop = []
            while len(new_pop) < pop_size:
                i1, i2 = random.sample(range(pop_size), 2)
                p1 = population[i1] if penalties[i1] < penalties[i2] else population[i2]
                
                i3, i4 = random.sample(range(pop_size), 2)
                p2 = population[i3] if penalties[i3] < penalties[i4] else population[i4]
                
                c1, c2 = crossover(p1, p2, prob_crossover)
                new_pop.append(mutate(c1, mut_rate))
                if len(new_pop) < pop_size:
                    new_pop.append(mutate(c2, mut_rate))
                    
            population = new_pop
            
            if gen % 10 == 0 or gen == max_gen - 1:
                progress_bar.progress((gen + 1) / max_gen)
                status_text.text(f"Generasi {gen+1}/{max_gen} - Penalti Terbaik: {best_penalty}")
                
        exec_time = time.time() - start_time
        st.success(f"Optimasi Selesai! Waktu Eksekusi: {exec_time:.2f} detik. Sisa Penalti: {best_penalty}")
        
        # Pembuatan DataFrame Hasil
        df_data = []
        for d in range(30):
            row = {"Hari": f"Hari {d+1}"}
            for i, emp in enumerate(all_emp):
                row[emp] = SHIFT_NAMES[best_ind[d][i]]
            df_data.append(row)
            
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Download ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Jadwal Shift')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Jadwal Excel",
            data=excel_data,
            file_name="Jadwal_Shift_WSS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Simpan State untuk Tab Analisis
        st.session_state['history'] = history
        st.session_state['exec_time'] = exec_time
        st.session_state['best_penalty'] = best_penalty

with tab2:
    st.header("Analisis Kinerja Algoritma Genetika")
    if 'history' in st.session_state:
        col1, col2, col3 = st.columns(3)
        col1.metric("Sisa Penalti Akhir", st.session_state['best_penalty'])
        col2.metric("Waktu Eksekusi", f"{st.session_state['exec_time']:.2f} detik")
        col3.metric("Total Generasi Dieksekusi", max_gen)
        
        st.subheader("Grafik Konvergensi Penalti")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(st.session_state['history'], color='green', linewidth=2)
        ax.set_title("Penurunan Penalti Tiap Generasi")
        ax.set_xlabel("Generasi")
        ax.set_ylabel("Nilai Penalti (Fitness)")
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)
        
        st.subheader("Rincian Parameter Aturan (Semua Bobot Setara)")
        st.markdown(
            """
            * **P1**: Karyawan dilarang masuk shift Break 2 hari beruntun.
            * **P2**: Proporsi shift harus mencukupi (Minimum 1 representasi PJ & 2 staf saat masuk penuh).
            * **P3**: Jatah 3x libur per bulan dengan batasan 1 karyawan per hari, dan wajib masuk di hari Minggu.
            * **P4**: Tidak diperbolehkan 2 PJ berada di *shift* yang sama, satu harus diganti staff jika terpaksa.
            * **P5**: Jika shift Siang hari ini, dilarang masuk shift Break di esok harinya.
            """
        )
    else:
        st.info("ℹ️ Silakan jalankan optimasi terlebih dahulu di tab 'Aplikasi Penjadwalan' untuk memunculkan analisis dan metrik performa algoritma.")
