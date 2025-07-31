import pandas as pd
columns_to_drop = [
    "Country", "Region", "City", "ASN", "User Agent String",
    "Browser Name and Version", "OS Name and Version", "Device Type",
    "Is Attack IP", "Is Account Takeover", "Round-Trip Time [ms]"
]
first_chunk = True
chunk_number = 1
for chunk in pd.read_csv("../datasets/rba-dataset.csv", chunksize=500000, low_memory=False):
    chunk.drop(columns=columns_to_drop, errors='ignore', inplace=True)
    chunk.to_csv(
        "../datasets/dataset-cleaned.csv",
        index=False,
        mode='w' if first_chunk else 'a',
        header=first_chunk
    )
    first_chunk = False
    chunk_number += 1