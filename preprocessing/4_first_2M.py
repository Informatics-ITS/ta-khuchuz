import pandas as pd

# Baca data
df = pd.read_csv("../datasets/dataset-featured.csv")

# Pisahkan benign untuk cadangan
benign_pool = df[df['attack_type'] == 0].copy()

# Buat list hasil akhir
dfs = []

# Proses attack_type 3, 2, 1
for label in [3, 2, 1]:
    subset = df[df['attack_type'] == label]
    count_needed = 250_000
    actual_count = len(subset)
    
    if actual_count >= count_needed:
        dfs.append(subset.head(count_needed))
    else:
        # Tambahkan semua yang tersedia, lalu ambil sisa dari benign_pool
        dfs.append(subset)
        fill_count = count_needed - actual_count
        benign_fill = benign_pool.head(fill_count)
        dfs.append(benign_fill)
        # Hapus yang sudah dipakai dari pool benign
        benign_pool = benign_pool.iloc[fill_count:]

# Tambahkan 250.000 benign terakhir
dfs.append(benign_pool.head(250_000))

# Gabungkan semua
final_df = pd.concat(dfs).sample(frac=1, random_state=42).reset_index(drop=True)  # acak hasil

# Verifikasi
print("Total rows:", len(final_df))
print(final_df['attack_type'].value_counts())

# Simpan
final_df.to_csv("../datasets/dataset-final.csv", index=False)
