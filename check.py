from flask import Flask, request
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

# Load model dan scaler
model = joblib.load("models/svm_bruteforce_final_nonlinear_none.pkl")
scaler = joblib.load("models/svm_scaler_final_nonlinear_none.pkl")

# Fitur yang digunakan untuk prediksi
features = [
    'failed_count_last_5min',
    'failed_ratio_last_5min',
    'unique_user_ids_last_5min'
]

@app.route("/")
def home():
    return """
    <h2>Prediksi Brute Force</h2>
    <form method="post" action="/predict">
        <textarea name="logdata" rows="15" cols="100" placeholder="Tempelkan log di sini..."></textarea><br>
        <input type="submit" value="Prediksi">
    </form>
    """

@app.route("/predict", methods=["POST"])
def predict():
    try:
        raw_text = request.form.get("logdata", "")
        lines = raw_text.strip().splitlines()
        rows = [line.strip().split(",") for line in lines]

        df = pd.DataFrame(rows, columns=["index", "Login Timestamp", "User ID", "IP Address", "Login Successful"])
        df['Login Timestamp'] = pd.to_numeric(df['Login Timestamp'], errors='coerce')
        df['Login Successful'] = df['Login Successful'].astype(int)
        df = df.dropna(subset=['Login Timestamp'])

        # Inisialisasi kolom fitur
        for col in features:
            df[col] = 0.0

        # Hitung fitur IP
        for ip, group in df.groupby("IP Address"):
            group = group.sort_values(by="Login Timestamp")
            ts = group['Login Timestamp'].values
            success = group['Login Successful'].values
            users = group['User ID'].values
            hasil = []

            for i in range(len(group)):
                start = np.searchsorted(ts, ts[i] - 300000, side='left')
                win = slice(start, i + 1)
                size = win.stop - win.start
                fails = (success[win] == 0).sum()
                ratio = fails / size if size > 0 else 0
                unique_users = len(set(users[win]))

                hasil.append((fails, ratio, unique_users))

            df.loc[group.index, features] = hasil

        # Prediksi
        X_scaled = scaler.transform(df[features])
        preds = model.predict(X_scaled)
        df["prediction"] = preds.tolist()

        # Aturan klasifikasi manual
        def classify_should(row):
            try:
                if row['failed_count_last_5min'] >= 7 and row['failed_ratio_last_5min'] >= 0.7:
                    return 1  # Simple brute force
                if row['unique_user_ids_last_5min'] >= 5 and row['failed_count_last_5min'] >= 5:
                    return 2  # Credential stuffing
            except Exception:
                pass
            return 0

        df['should'] = df.apply(classify_should, axis=1)

        # Tampilkan hasil
        result_html = "<h2>Hasil Prediksi</h2><table border='1'><tr>"
        result_html += "<th>Index</th><th>Timestamp</th><th>Username</th><th>IP</th><th>Status Login</th><th>Prediksi SVM</th><th>Metode Threshold</th>"
        for f in features:
            result_html += f"<th>{f}</th>"
        result_html += "</tr>"

        for _, row in df.iterrows():
            pred_label   = "benign" if row['prediction'] == 0 else "bruteforce"
            should_label = "benign" if row['should']     == 0 else "bruteforce"

            result_html += (
                f"<tr><td>{row['index']}</td>"
                f"<td>{row['Login Timestamp']}</td>"
                f"<td>{row['User ID']}</td>"
                f"<td>{row['IP Address']}</td>"
                f"<td>{row['Login Successful']}</td>"
                f"<td>{pred_label}</td>"
                f"<td>{should_label}</td>"
            )

            for f in features:
                result_html += f"<td>{round(row[f], 3)}</td>"
            result_html += "</tr>"

        result_html += "</table><br><a href='/'>Kembali</a>"
        return result_html

    except Exception as e:
        return f"<b>Terjadi kesalahan:</b> {str(e)}<br><a href='/'>Kembali</a>"

if __name__ == "__main__":
    app.run(debug=True, port=5050)
