import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Jadwal Pro", layout="wide")

st.title("🗓️ Generator Jadwal Shift Toko (Versi Super Strict)")

# --- SIDEBAR: MANAJEMEN KARYAWAN ---
with st.sidebar:
    st.header("🏢 Konfigurasi Cabang")
    
    pj_input = st.text_area("Daftar PJ (Pisahkan dengan koma)", "Indah, Andri")
    staf_input = st.text_area("Daftar Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")
    
    list_pj = [x.strip() for x in pj_input.split(",") if x.strip()]
    list_staf = [x.strip() for x in staf_input.split(",") if x.strip()]
    semua_karyawan = list_pj + list_staf
    
    st.divider()
    st.subheader("📊 Info Karyawan Terdaftar")
    col1, col2 = st.columns(2)
    col1.metric("PJ", len(list_pj))
    col2.metric("Staf", len(list_staf))
    st.info(f"**Total:** {len(semua_karyawan)} Orang")
    
    st.divider()
    st.header("⚙️ Parameter Algoritma")
    generasi = st.slider("Jumlah Generasi", 100, 1000, 300)
    st.caption("Tips: Jika hasil libur belum adil, naikkan ke 500+")

# --- LOGIKA FITNESS (OTAK ALGORITMA) ---
def hitung_fitness(individu, list_pj, semua_karyawan):
    penalti = 0
    libur_count = {k: 0 for k in semua_karyawan}
    break_count = {k: 0 for k in semua_karyawan}
    total_k = len(semua_karyawan)
    
    for d in range(30):
        hari_ke = d + 1
        is_minggu = (hari_ke % 7 == 0)
        k_hari = individu[d]
        
        # 1. Menentukan Siapa yang Aktif & Libur
        if is_minggu:
            aktif = k_hari
        else:
            libur = [k_hari[-1]]
            aktif = k_hari[:-1]
            for l in libur: libur_count[l] += 1
        
        # 2. Pembagian Shift
        n = len(aktif)
        p = n // 3
        pagi, siang, brk = aktif[0:p], aktif[p:p*2], aktif[p*2:]
        for b in brk: break_count[b] += 1

        # 3. Constraint: Minimal 1 PJ per Shift
        for s in [pagi, siang, brk]:
            if not any(pj in list_pj for pj in s):
                penalti += 500 # Penalti berat jika shift tanpa PJ

        # 4. Constraint: Jeda Istirahat (Siang -> Besok Break DILARANG)
        if d < 29:
            k_besok = individu[d+1]
            # Estimasi shift break besok
            n_b = total_k if (d+2)%7==0 else total_k-1
            p_b = n_b // 3
            brk_besok = k_besok[p_b*2:n_b]
            
            for k in siang:
                if k in brk_besok: penalti += 2000 # Sangat dilarang
            for k in brk:
                if k in brk_besok: penalti += 2000 # Istirahat antar hari

    # 5. Keadilan Libur (HARUS 3 KALI)
    for k in libur_count:
        if libur_count[k] != 3:
            penalti += abs(libur_count[k] - 3) * 10000 # Hard Lock

    # 6. Keadilan Break (Maksimal selisih 1-2 hari)
    vals_brk = list(break_count.values())
    if vals_brk:
        diff_brk = max(vals_brk) - min(vals_brk)
        if diff_brk > 1:
            penalti += diff_brk * 1000

    return 1 / (1 + penalti)

# --- PROSES GENERATE ---
if st.button("🚀 Generate Jadwal Paling Adil"):
    if len(semua_karyawan) < 6:
        st.error("Karyawan kurang!")
    else:
        # Inisialisasi Populasi (Dinaikkan ke 40 agar variasi lebih banyak)
        pop_size = 40
        populasi = [[random.sample(semua_karyawan, len(semua_karyawan)) for _ in range(30)] for _ in range(pop_size)]
        
        progress_bar = st.progress(0)
        status = st.empty()

        for g in range(generasi):
            # Sortir berdasarkan yang paling sedikit melanggar aturan
            populasi = sorted(populasi, key=lambda x: hitung_fitness(x, list_pj, semua_karyawan), reverse=True)
            
            # Crossover & Mutation sederhana
            new_pop = populasi[:10] # Ambil 10 terbaik (Elitism)
            while len(new_pop) < pop_size:
                p1, p2 = random.sample(populasi[:15], 2)
                titik = random.randint(5, 25)
                anak = p1[:titik] + p2[titik:]
                if random.random() < 0.2: # Mutasi 20%
                    idx = random.randint(0, 29)
                    random.shuffle(anak[idx])
                new_pop.append(anak)
            populasi = new_pop
            
            progress_bar.progress((g + 1) / generasi)
            if g % 10 == 0:
                status.text(f"Menganalisis kemungkinan jadwal... (Generasi {g})")

        status.success("✅ Jadwal Optimal Ditemukan!")
        best = populasi[0]

        # --- REKAP DATA ---
        data_harian = []
        rekap = {k: {"Pagi": 0, "Siang": 0, "Break": 0, "Libur": 0} for k in semua_karyawan}
        
        for d in range(30):
            hari_ke = d + 1
            is_minggu = (hari_ke % 7 == 0)
            k = best[d]
            n_a = len(semua_karyawan) if is_minggu else len(semua_karyawan) - 1
            p = n_a // 3
            
            pagi, siang, brk = k[0:p], k[p:p*2], k[p*2:n_a]
            libur = [k[-1]] if not is_minggu else []
            
            for x in pagi: rekap[x]["Pagi"] += 1
            for x in siang: rekap[x]["Siang"] += 1
            for x in brk: rekap[x]["Break"] += 1
            for x in libur: rekap[x]["Libur"] += 1
            
            data_harian.append({
                "Hari": f"Hari {hari_ke}",
                "Pagi": ", ".join(pagi),
                "Siang": ", ".join(siang),
                "Break": ", ".join(brk),
                "Libur": ", ".join(libur) if libur else "-"
            })

        # --- TAMPILAN ---
        st.subheader("📋 Jadwal Kerja 30 Hari")
        st.dataframe(pd.DataFrame(data_harian), use_container_width=True)

        st.divider()
        st.subheader("📊 Statistik Keadilan")
        df_stats = pd.DataFrame(rekap).T.reset_index().rename(columns={'index': 'Nama'})
        
        c1, c2 = st.columns([2, 1])
        c1.table(df_stats)
        
        with c2:
            st.write("**Validasi Aturan:**")
            lb_ok = all(df_stats['Libur'] == 3)
            if lb_ok: st.success("✅ Semua libur tepat 3x")
            else: st.error("❌ Ada libur yang tidak pas")
            
            brk_diff = df_stats['Break'].max() - df_stats['Break'].min()
            if brk_diff <= 2: st.success(f"✅ Pembagian Break Adil (Selisih {brk_diff})")
            else: st.warning(f"⚠️ Selisih Break {brk_diff} hari (Kurang Adil)")

        # --- DOWNLOAD ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(data_harian).to_excel(writer, index=False, sheet_name='Jadwal')
            df_stats.to_excel(writer, index=False, sheet_name='Statistik')
        
        st.download_button(label="📥 Download Hasil (Excel)", data=output.getvalue(), file_name="Jadwal_Toko_Final.xlsx")
