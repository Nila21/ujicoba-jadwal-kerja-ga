import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import io
import matplotlib.pyplot as plt

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Optimasi Penjadwalan WSS", layout="wide")

st.title("Aplikasi Optimasi Penjadwalan Shift Kerja")
st.markdown("Algoritma Genetika - Penjadwalan Shift Karyawan WSS")

# --- INPUT DATA ---
st.sidebar.header("Pengaturan Karyawan")
pj_input = st.sidebar.text_input("Nama PJ Toko (pisahkan dengan koma)", "Indah, Andri")
staf_input = st.sidebar.text_input("Nama Staf Toko (pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Alfi, Novi")

pj_list = [x.strip() for x in pj_input.split(",") if x.strip()]
staf_list = [x.strip() for x in staf_input.split(",") if x.strip()]
all_emp = pj_list + staf_list
num_emp = len(all_emp)

# --- PARAMETER ---
pop_size = st.sidebar.number_input("Ukuran Populasi", 10, 200, 50)
max_gen = st.sidebar.number_input("Maksimal Generasi", 10, 1000, 300)
mut_rate = st.sidebar.slider("Probabilitas Mutasi", 0.01, 1.0, 0.1)

SHIFT_NAMES = {0: "Pagi", 1: "Siang", 2: "Break", 3: "Libur"}

# --- FUNGSI GENETIKA ---
def generate_random_day(day_index):
    is_sunday = (day_index % 7 == 6)
    day_sched = [0] * num_emp
    if is_sunday:
        shifts = [0, 1, 2] * 3
        shifts = shifts[:num_emp]
        random.shuffle(shifts)
        day_sched = shifts
    else:
        num_off = random.choice([0, 1])
        if num_off == 1:
            off_idx = random.randint(0, num_emp - 1)
            shifts = [0, 1, 2] * 3
            shifts = shifts[:num_emp - 1]
            random.shuffle(shifts)
            idx = 0
            for i in range(num_emp):
                if i == off_idx: day_sched[i] = 3
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

def calculate_fitness(ind):
    penalty = 0
    weight = 10
    libur_counts = [0] * num_emp
    for d in range(30):
        day_sched = ind[d]
        is_sunday = (d % 7 == 6)
        c_pagi = day_sched.count(0)
        c_siang = day_sched.count(1)
        c_break = day_sched.count(2)
        c_libur = day_sched.count(3)
        for i, s in enumerate(day_sched):
            if s == 3: libur_counts[i] += 1
        if is_sunday and c_libur > 0: penalty += weight * c_libur
        elif not is_sunday and c_libur > 1: penalty += weight * (c_libur - 1)
        
        pj_shifts = [day_sched[i] for i in range(len(pj_list))]
        for s in [0, 1, 2]:
            if pj_shifts.count(s) > 1: penalty += weight
            
        if c_pagi < 2 or c_siang < 2 or c_break < 2: penalty += weight
        
        if d < 29:
            next_sched = ind[d+1]
            for i in range(num_emp):
                if day_sched[i] == 2 and next_sched[i] == 2: penalty += weight
                if day_sched[i] == 1 and next_sched[i] == 2: penalty += weight
    for lc in libur_counts:
        if lc != 3: penalty += weight * abs(lc - 3)
    return penalty

def crossover(p1, p2):
    pt = random.randint(1, 28)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]

def mutate(ind, rate):
    for d in range(30):
        if random.random() < rate: ind[d] = generate_random_day(d)
    return ind

# --- UI ---
tab1, tab2 = st.tabs(["🖥️ Aplikasi Penjadwalan", "📊 Analisis GA"])

if 'history' not in st.session_state:
    st.session_state['history'] = []

with tab1:
    if st.button("Mulai Optimasi Jadwal"):
        population = [create_individual() for _ in range(pop_size)]
        best_ind, best_penalty = None, float('inf')
        history = []
        
        for gen in range(max_gen):
            penalties = [calculate_fitness(ind) for ind in population]
            min_pen = min(penalties)
            if min_pen < best_penalty:
                best_penalty = min_pen
                best_ind = population[penalties.index(min_pen)]
            history.append(best_penalty)
            
            new_pop = []
            while len(new_pop) < pop_size:
                p1, p2 = population[random.randint(0, pop_size-1)], population[random.randint(0, pop_size-1)]
                c1, c2 = crossover(p1, p2)
                new_pop.extend([mutate(c1, mut_rate), mutate(c2, mut_rate)])
            population = new_pop[:pop_size]
        
        st.success("Optimasi Selesai!")
        st.session_state['best_ind'] = best_ind
        st.session_state['history'] = history
        st.session_state['best_penalty'] = best_penalty

    if 'best_ind' in st.session_state:
        df = pd.DataFrame([{"Hari": f"Hari {d+1}", **{all_emp[i]: SHIFT_NAMES[st.session_state['best_ind'][d][i]] for i in range(num_emp)}} for d in range(30)])
        st.dataframe(df, use_container_width=True)

with tab2:
    if st.session_state['history']:
        st.line_chart(st.session_state['history'])
        st.write(f"Penalti Akhir: {st.session_state['best_penalty']}")
