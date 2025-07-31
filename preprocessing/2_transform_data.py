import pandas as pd
df = pd.read_csv("../datasets/dataset-cleaned.csv", low_memory=False)

bool_cols = df.select_dtypes(include='bool').columns.tolist()
for col in bool_cols:
	df[col] = df[col].astype(int)

for col in df.columns:
	if df[col].dtype == object and df[col].isin(['True', 'False']).all():
		df[col] = df[col].map({'True': 1, 'False': 0})

df['Login Timestamp'] = pd.to_datetime(df['Login Timestamp'], errors='coerce')
df['Login Timestamp'] = df['Login Timestamp'].astype('int64') // 10**6

df.to_csv("../datasets/dataset-transformed.csv", index=False)