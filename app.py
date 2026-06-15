import streamlit as st
import pandas as pd
import numpy as np
import random
import io

# ==========================================
# 1. KONFIGURASI & BOBOT PENALTI
# ==========================================
# Sesuaikan angka bobot di bawah ini dengan tabel analisis batasan Anda
W_MINGGU = 100          # Penalti jika hari Minggu ada yang libur
W_MAX_LIBUR = 100       # Penalti jika sehari ada lebih dari 1 orang libur
W_JATAH_LIBUR = 100      # Penalti jika jatah libur sebulan tidak pas 3 kali
W_SIANG_BREAK = 50      # Penalti jika masuk shift Siang, besoknya shift Break
W_BREAK_BREAK = 50      # Penalti jika masuk shift Break 2 hari berturut-turut
W_KOMPOSISI_NORMAL = 50 # Penalti jika komposisi shift tidak sesuai saat semua masuk
W_KOMPOSISI_LIBUR = 50  # Penalti jika komposisi shift Pagi bukan 2 orang saat ada yang libur
W_SHIFT_KOSONG = 100    # Penalti jika ada shift yang sama sekali tidak ada orang

# --- BATASAN BARU ---
W_PJ_SAMA_SHIFT = 80   # Penalti jika PJ 1 dan PJ 2 berada di shift yang sama (jika keduanya masuk)

# ==========================================
# 2. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(page_title="Optimasi Jadwal Shift WSS", layout="wide")

st.title("🏬 Optimasi Penjadwalan Shift Kerja (Algoritma Genetika)")
st.markdown("""
Aplikasi ini mengatur jadwal berdasarkan batasan *multi-constraint*:
1. **Hari Minggu** wajib masuk semua.
2. Sehari maksimal **1 orang libur** (Senin-Sabtu).
3. Sebulan setiap karyawan libur **tepat 3 kali**.
4. Rotasi dilarang: **Siang -> Break** dan **Break -> Break**.
5. **Dua PJ tidak boleh berada di shift yang sama** pada hari yang sama (kecuali salah satunya libur).
6. Jika semua masuk: tiap shift minimal terisi seimbang. Jika 1 libur: **Shift Pagi terisi 2 orang** (1 PJ/pengganti + 1 Staf).
""")

# ==========================================
# 3. SIDEBAR - NAMA KARYAWAN & PARAMETER GA
# ==========================================
st.sidebar.header("👥 Manajemen Karyawan")
pj1 = st.sidebar.text_input("PJ Toko 1", value="Indah", key="pj1_in")
pj2 = st.sidebar.text_input("PJ Toko 2", value="Andri", key="pj2_in")
staf1 = st.sidebar.text_input("Staf 1", value="Tika", key="s1_in")
staf2 = st.sidebar.text_input("Staf 2", value="Firman", key="s2_in")
staf3 = st.sidebar.text_input("Staf 3", value="Elan", key="s3_in")
staf4 = st.sidebar.text_input("Staf 4", value="Nila", key="s4_in")
staf5 = st.sidebar.text_input("Staf 5", value="Alfi", key="s5_in")
staf6 = st.sidebar.text_input("Staf 6", value="Novi", key="s6_in")

karyawan = [pj1, pj2, staf1, staf2, staf3, staf4, staf5, staf6]

st.sidebar.header("⚙️ Parameter Algoritma")
pop_size = st.sidebar.number_input("Ukuran Populasi", min_value=10, max_value=200, value=50, step=10, key="pop")
generations = st.sidebar.number_input("Jumlah Generasi", min_value=50, max_value=1000, value=300, step=50, key="gen")
mutation_rate = st.sidebar.slider("Probabilitas Mutasi", 0.01, 0.5, 0.1, key="mut")

# ==========================================
# 4. FUNGSI ALGORITMA GENETIKA
# ==========================================
def create_individual():
    """Membuat 1 kromosom secara acak bersyarat."""
    ind = [[1 for _ in range(30)] for _ in range(8)]
    for d in range(30):
        is_sunday = (d % 7 == 6)
        
        off_employee = -1
        if not is_sunday and random.random() < 0.7: 
            off_employee = random.randint(0, 7)
            ind[off_employee][d] = 0
            
        working_emps = [e for e in range(8) if e != off_employee]
        random.shuffle(working_emps)
        
        for i, emp in enumerate(working_emps):
            ind[emp][d] = (i % 3) + 1 
    return ind

def calculate_fitness(ind):
    """Menghitung nilai penalti. Semakin kecil penalti, jadwal semakin optimal."""
    penalty = 0 
    
    # 1. Evaluasi per hari (Kolom)
    for d in range(30):
        is_sunday = (d % 7 == 6)
        shifts_today = [ind[e][d] for e in range(8)]
        
        off_count = shifts_today.count(0)
        pagi_count = shifts_today.count(1)
        siang_count = shifts_today.count(2)
        break_count = shifts_today.count(3)
        
        # --- ATURAN BARU: CEK KESAMAAN SHIFT PJ ---
        # Indeks 0 adalah PJ 1, Indeks 1 adalah PJ 2
        pj1_shift = ind[0][d]
        pj2_shift = ind[1][d]
        
        # Jika kedua PJ tidak libur, mereka tidak boleh berada di shift yang sama
        if pj1_shift != 0 and pj2_shift != 0 and pj1_shift == pj2_shift:
            penalty += W_PJ_SAMA_SHIFT
            
        # Constraint: Minggu masuk semua
        if is_sunday and off_count > 0:
            penalty += W_MINGGU * off_count
            
        # Constraint: Maksimal 1 orang libur sehari
        if not is_sunday and off_count > 1:
            penalty += W_MAX_LIBUR * (off_count - 1)
            
        # Constraint Komposisi Shift
        if off_count == 1:
            if pagi_count != 2:
                penalty += W_KOMPOSISI_LIBUR
        elif off_count == 0:
            if pagi_count < 2 or siang_count < 2 or break_count < 2:
                penalty += W_KOMPOSISI_NORMAL
                
        # Cek shift kosong
        if pagi_count == 0 or siang_count == 0 or break_count == 0:
            penalty += W_SHIFT_KOSONG
            
    # 2. Evaluasi per Karyawan (Baris)
    for e in range(8):
        shifts_emp = ind[e]
        off_days = shifts_emp.count(0)
        
        # Constraint: Libur sebulan 3 kali
        if off_days != 3:
            penalty += W_JATAH_LIBUR * abs(off_days - 3)
            
        # Constraint: Rotasi Shift
        for d in range(29):
            today = shifts_emp[d]
            tomorrow = shifts_emp[d+1]
            
            if today == 2 and tomorrow == 3: # Siang -> Break
                penalty += W_SIANG_BREAK
            if today == 3 and tomorrow == 3: # Break -> Break
                penalty += W_BREAK_BREAK
                
    fitness_score = 10000 - penalty
    return fitness_score, penalty

def crossover(parent1, parent2):
    child1, child2 = [], []
    for e in range(8):
        if random.random() > 0.5:
            child1.append(parent1[e].copy())
            child2.append(parent2[e].copy())
        else:
            child1.append(parent2[e].copy())
            child2.append(parent1[e].copy())
    return child1, child2

def mutate(ind):
    for e in range(8):
        if random.random() < mutation_rate:
            day = random.randint(0, 29)
            ind[e][day] = random.randint(0, 3)
    return ind

# ==========================================
# 5. EKSEKUSI & TAMPILAN
# ==========================================
if st.button("🚀 Optimasi Jadwal (Mulai GA)", key="run_ga"):
    with st.spinner("Memproses algoritma genetika..."):
        population = [create_individual() for _ in range(pop_size)]
        
        progress = st.progress(0)
        for gen in range(generations):
            pop_scored = [(ind, calculate_fitness(ind)) for ind in population]
            pop_scored.sort(key=lambda x: x[1][0], reverse=True)
            
            population = [x[0] for x in pop_scored]
            next_gen = population[:int(0.2 * pop_size)]
            
            while len(next_gen) < pop_size:
                p1, p2 = random.sample(population[:int(0.5 * pop_size)], 2)
                c1, c2 = crossover(p1, p2)
                next_gen.append(mutate(c1))
                if len(next_gen) < pop_size:
                    next_gen.append(mutate(c2))
                    
            population = next_gen
            progress.progress((gen + 1) / generations)
        
        best_ind = population[0]
        best_fitness, best_penalty = calculate_fitness(best_ind)
        
        shift_map = {0: "Libur", 1: "Pagi", 2: "Siang", 3: "Break"}
        df_data = []
        for e in range(8):
            row = [karyawan[e]] + [shift_map[best_ind[e][d]] for d in range(30)]
            df_data.append(row)
            
        kolom = ["Nama Karyawan"] + [f"Hari {i+1}" for i in range(30)]
        df = pd.DataFrame(df_data, columns=kolom)
        
        def color_map(val):
            if val == 'Libur': return 'background-color: #ffcccc; color: black;'
            if val == 'Pagi': return 'background-color: #ccffcc; color: black;'
            if val == 'Siang': return 'background-color: #cce5ff; color: black;'
            if val == 'Break': return 'background-color: #fff2cc; color: black;'
            return ''
            
        styled_df = df.style.map(color_map, subset=[f"Hari {i+1}" for i in range(30)])
        
        st.success(f"Selesai! Sisa Penalti: {best_penalty} (Fitness: {best_fitness})")
        st.dataframe(styled_df, use_container_width=True)
        
        # ==========================================
        # 6. DOWNLOAD EXCEL
        # ==========================================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Jadwal Optimal')
            workbook = writer.book
            worksheet = writer.sheets['Jadwal Optimal']
            
            f_libur = workbook.add_format({'bg_color': '#ffcccc', 'font_color': 'black'})
            f_pagi = workbook.add_format({'bg_color': '#ccffcc', 'font_color': 'black'})
            f_siang = workbook.add_format({'bg_color': '#cce5ff', 'font_color': 'black'})
            f_break = workbook.add_format({'bg_color': '#fff2cc', 'font_color': 'black'})
            
            for row in range(8):
                for col in range(30):
                    val = df.iloc[row, col+1]
                    if val == 'Libur': worksheet.write(row+1, col+1, val, f_libur)
                    elif val == 'Pagi': worksheet.write(row+1, col+1, val, f_pagi)
                    elif val == 'Siang': worksheet.write(row+1, col+1, val, f_siang)
                    elif val == 'Break': worksheet.write(row+1, col+1, val, f_break)
                    
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:AE', 8)

        st.download_button(
            label="📥 Download Jadwal (.xlsx)",
            data=output.getvalue(),
            file_name="Jadwal_Shift_Optimal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
