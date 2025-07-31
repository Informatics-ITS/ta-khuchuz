import pandas as pd
import numpy as np
from tqdm import tqdm
from joblib import Parallel, delayed

df = pd.read_csv("../datasets/dataset-transformed.csv", low_memory=False)
df = df.sort_values(by=["IP Address", "Login Timestamp"]).reset_index(drop=True)

features = [
	'failed_count_last_5min',
	'failed_ratio_last_5min',
	'unique_user_ids_last_5min'
]

for col in features:
    df[col] = 0.0

def process_ip_group(ip, group):
    try:
        result = []
        timestamps = group['Login Timestamp'].values
        login_success = group['Login Successful'].values
        user_ids = group['User ID'].values

        for i in range(len(group)):
            now = timestamps[i]
            t_window = now - 300000
            
            start_idx = np.searchsorted(timestamps, t_window, side='left')
            end_idx = i + 1
            
            if end_idx - start_idx == 0:
                result.append([0, 0, 0])
                continue
                
            win = slice(start_idx, end_idx)
            size = end_idx - start_idx
            
            fails = (login_success[win] == 0).sum()
            fails_ratio = fails / size
            unique_users = np.unique(user_ids[win]).size
            
            result.append([fails, fails_ratio, unique_users])
        return pd.DataFrame(result, columns=features, index=group.index)
    except Exception as e:
        print(f"IP {ip} gagal diproses: {e}")
        return None

grouped = dict(tuple(df.groupby("IP Address")))
ip_list = list(grouped.keys())

results = Parallel(n_jobs=-1)(
    delayed(process_ip_group)(ip, grouped[ip]) for ip in tqdm(ip_list, desc="Memproses IP")
)

valid_results = [r for r in results if isinstance(r, pd.DataFrame) and not r.empty]

if valid_results:
    df_features = pd.concat(valid_results).sort_index()
    df.update(df_features)

    def classify_attack_type(row):
        try:
            if row['failed_count_last_5min']>=7 and row['failed_ratio_last_5min']>=0.7:
                return 1
            elif row['unique_user_ids_last_5min']>=5 and row['failed_count_last_5min']>=5:
                return 2
        except Exception:
            pass
        return 0

    df['attack_type'] = df.apply(classify_attack_type, axis=1)
    df.to_csv("../datasets/dataset-featured.csv", index=False)
    print("Fitur & attack_type berhasil disimpan")
else:
    print("Tidak ada hasil valid yang bisa disimpan.")