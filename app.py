import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Jadwal Ultra", layout="wide")

st.title("🗓️ Generator Jadwal Shift Toko (Versi Ultra Final)")
st.markdown("Sistem ini menggunakan *Heavy Penalty Logic* untuk menjamin keadilan jatah libur (Wajib 3x) dan aturan Shift PJ.")

# --- SIDEBAR: MANAJEMEN KARYAWAN ---
with st.sidebar:
    st.header("🏢 Konfigurasi Cabang")
    
    pj_input = st.text_area("Daftar PJ (Pisahkan dengan koma)", "Indah, Andri")
    staf_input = st.text_area("Daftar Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")
    
    list_pj = [x.strip() for x in pj_input.split(",") if x.strip()]
    list_staf = [x.strip() for x in staf_input.split(",") if x.strip()]
    semua_karyawan = list_pj + list_staf
    total_k = len(semua_karyawan)
    
    st.divider()
    st.subheader("📊 Info Karyawan")
    st.info(f"Total: {total_k} Orang ({len(list_pj)} PJ, {len(list_staf)} Staf)")
    
    st.divider()
    st.header("⚙️ Parameter Ultra")
    val_generasi = st.slider("Jumlah Generasi (Iterasi)", 100, 2000, 1000)
    val_populasi = st.slider("Ukuran Populasi (Variasi)", 20, 100, 80)

# --- LOGIKA FITNESS (ULTRA STRICT) ---
def hitung_fitness(individu, list_pj, semua_karyawan):
    penalti = 0
    libur_count = {k: 0 for k in semua_karyawan}
    break_count = {k: 0 for k in semua_karyawan}
    
    prev_siang = []
    prev_break = []

    for d in range(30):
        hari_ke = d + 1
        is_minggu = (hari_ke % 7 == 0)
        k_hari = individu[d]
        
        # 1. Identifikasi Libur & Aktif
        if is_minggu:
            aktif = k_hari
            libur = []
        else:
            libur = [k_hari[-1]]
            aktif = k_hari[:-1]
            for l in libur: libur_count[l] += 1
        
        # 2. Pembagian Shift (Pagi, Siang, Break)
        n = len(aktif)
        p = n // 3
        pagi = aktif[0:p]
        siang = aktif[p:p*2]
        brk = aktif[p*2:]
        
        for b in brk: break_count[b] += 1

        # 3. ATURAN PJ: Hanya boleh 1 PJ per shift.
        # Jika satu shift tidak ada PJ, penalti besar. 
        # Jika satu shift lebih dari 1 PJ, penalti besar.
        for s in [pagi, siang, brk]:
            count_pj = sum(1 for person in s if person in list_pj)
            if count_pj != 1:
                penalti += 10000 # Sangat dilarang tidak ada PJ atau >1 PJ

        # 4. ATURAN JEDA SHIFT
        # Siang -> Besok tidak boleh Break
        for k in prev_siang:
            if k in brk: penalti += 15000
        
        # Break -> Besok tidak boleh Break (Berurutan)
        for k in prev_break:
            if k in brk: penalti += 15000

        prev_siang = siang
        prev_break = brk

    # 5. LOCK LIBUR: WAJIB 3 KALI
    for k in libur_count:
        if libur_count[k] != 3:
            penalti += abs(libur_count[k] - 3) * 100000 

    # 6. Keadilan Break (Selisih antar orang tidak boleh > 1)
    if break_count:
        vals_b = list(break_count.values())
        diff_b = max(vals_b) - min(vals_b)
        if diff_b > 1:
            penalti += diff_b * 5000

    return 1 / (1 + penalti)

# --- ENGINE GENERATOR ---
if st.button("🚀 Jalankan Algoritma Ultra Adil"):
    if total_k < 6:
        st.error("Jumlah karyawan tidak mencukupi!")
    elif len(list_pj) < 2:
        st.error("Minimal harus ada 2 PJ agar bisa berbagi shift!")
    else:
        # Inisialisasi awal
        populasi = [[random.sample(semua_karyawan, total_k) for _ in range(30)] for _ in range(val_populasi)]
        
        progress_bar = st.progress(0)
        status_box = st.empty()

        for g in range(val_generasi):
            populasi = sorted(populasi, key=lambda x: hitung_fitness(x, list_pj, semua_karyawan), reverse=True)
            
            # Elitisme
            anak_baru = populasi[:10]
            
            while len(anak_baru) < val_populasi:
                induk1, induk2 = random.sample(populasi[:20], 2)
                titik_potong = random.randint(5, 25)
                anak = induk1[:titik_potong] + induk2[titik_potong:]
                
                # Mutasi: Menukar orang di hari yang sama untuk mencari komposisi PJ yang pas
                if random.random() < 0.4:
                    h = random.randint(0, 29)
                    idx1, idx2 = random.sample(range(total_k), 2)
                    anak[h][idx1], anak[h][idx2] = anak[h][idx2], anak[h][idx1]
                
                anak_baru.append(anak)
            
            populasi = anak_baru
            if g % 20 == 0:
                progress_bar.progress((g + 1) / val_generasi)
                status_box.info(f"Optimasi sedang berjalan... Generasi ke-{g}")

        status_box.success("✅ Jadwal Optimal Berhasil Disusun!")
        best = populasi[0]

        # --- PEMROSESAN HASIL ---
        hasil_harian = []
        rekap = {k: {"Pagi": 0, "Siang": 0, "Break": 0, "Libur": 0} for k in semua_karyawan}
        
        for d in range(30):
            hari_ke = d + 1
            is_m = (hari_ke % 7 == 0)
            k = best[d]
            n_aktif = total_k if is_m else total_k - 1
            p_val = n_aktif // 3
            
            pagi, siang, brk = k[0:p_val], k[p_val:p_val*2], k[p_val*2:n_aktif]
            libur = [k[-1]] if not is_m else []
            
            for x in pagi: rekap[x]["Pagi"] += 1
            for x in siang: rekap[x]["Siang"] += 1
            for x in brk: rekap[x]["Break"] += 1
            for x in libur: rekap[x]["Libur"] += 1
            
            hasil_harian.append({
                "Hari": f"Hari {hari_ke}",
                "Shift Pagi": ", ".join(pagi),
                "Shift Siang": ", ".join(siang),
                "Shift Break": ", ".join(brk),
                "Libur": ", ".join(libur) if libur else "-"
            })

        # --- DISPLAY ---
        st.subheader("📋 Jadwal Kerja Hasil Optimasi")
        st.dataframe(pd.DataFrame(hasil_harian), use_container_width=True)

        st.divider()
        st.subheader("📊 Laporan Akumulasi & Keadilan")
        df_rekap = pd.DataFrame(rekap).T.reset_index().rename(columns={'index': 'Nama Karyawan'})
        
        col_tabel, col_cek = st.columns([2, 1])
        col_tabel.table(df_rekap)
        
        with col_cek:
            st.write("**Status Kelayakan:**")
            l_val = all(df_rekap['Libur'] == 3)
            if l_val: st.success("✅ LIBUR: Semua 3x")
            else: st.error("❌ LIBUR: Belum Rata")
            
            diff_b = df_rekap['Break'].max() - df_rekap['Break'].min()
            if diff_b <= 1: st.success(f"✅ BREAK: Adil (Selisih {diff_b})")
            else: st.warning(f"⚠️ BREAK: Selisih {diff_b}")

        # --- DOWNLOAD ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(hasil_harian).to_excel(writer, index=False, sheet_name='Jadwal')
            df_rekap.to_excel(writer, index=False, sheet_name='Rekap')
        st.download_button("📥 Download Excel", output.getvalue(), "Jadwal_Toko.xlsx")
