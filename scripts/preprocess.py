import glob
import json
import os

import numpy as np
import pandas as pd

SEED = 42
CHUNK = 500_000
RAW_GLOB = "data/raw/*.csv"
OUT_DIR = "data/processed"
REPORT_PATH = "docs/preprocessing_report.md"

TABLE2 = {"Normal": 122000, "DDoS": 64000, "DoS": 48000, "Bot": 14000,
          "Brute force": 11000, "Infiltration": 10000, "Web": 3702}
LABEL_MAP = {
    "Benign": "Normal",
    "DDOS attack-HOIC": "DDoS", "DDOS attack-LOIC-UDP": "DDoS", "DDoS attacks-LOIC-HTTP": "DDoS",
    "DoS attacks-GoldenEye": "DoS", "DoS attacks-Slowloris": "DoS",
    "DoS attacks-Hulk": "DoS", "DoS attacks-SlowHTTPTest": "DoS",
    "Bot": "Bot",
    "FTP-BruteForce": "Brute force", "SSH-Bruteforce": "Brute force",
    "Infilteration": "Infiltration",
    "Brute Force -Web": "Web", "Brute Force -XSS": "Web", "SQL Injection": "Web",
}
DROP_COLS = ["Flow ID", "Src IP", "Dst IP", "Src Port", "Timestamp"]
CATEGORICAL = ["Protocol"]
LABEL = "Label"


def clean_chunk(chunk, stats):
    stats["rows_read"] += len(chunk)

    is_header = chunk[LABEL] == LABEL
    stats["header_rows"] += int(is_header.sum())
    chunk = chunk[~is_header]

    chunk["class"] = chunk[LABEL].map(LABEL_MAP)
    unmapped = chunk["class"].isna()
    stats["unmapped_label_rows"] += int(unmapped.sum())
    chunk = chunk[~unmapped].drop(columns=LABEL)

    feats = [c for c in chunk.columns if c != "class"]
    chunk[feats] = chunk[feats].apply(pd.to_numeric, errors="coerce")
    chunk[feats] = chunk[feats].replace([np.inf, -np.inf], np.nan)
    has_bad_value = chunk[feats].isna().any(axis=1)
    stats["nan_or_inf_rows"] += int(has_bad_value.sum())
    return chunk[~has_bad_value]


def keep_random_rows(chunk, kept, available, rng):
    chunk["_key"] = rng.random(len(chunk))
    for cls, rows in chunk.groupby("class"):
        available[cls] = available.get(cls, 0) + len(rows)
        candidates = [kept[cls], rows] if cls in kept else [rows]
        kept[cls] = pd.concat(candidates).nsmallest(TABLE2[cls], "_key")


def sample_raw_files(raw_glob, seed):
    rng = np.random.default_rng(seed)
    kept, available = {}, {}
    stats = {"files": 0, "rows_read": 0, "header_rows": 0, "unmapped_label_rows": 0, "nan_or_inf_rows": 0}
    for path in sorted(glob.glob(raw_glob)):
        stats["files"] += 1
        reader = pd.read_csv(path, chunksize=CHUNK, low_memory=False, usecols=lambda c: c not in DROP_COLS)
        for chunk in reader:
            keep_random_rows(clean_chunk(chunk, stats), kept, available, rng)
        print(os.path.basename(path), "done", flush=True)
    return kept, available, stats


def combine_and_shuffle(kept, seed):
    df = pd.concat(kept.values(), ignore_index=True).drop(columns="_key")
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def drop_zero_variance(df):
    feats = [c for c in df.columns if c != "class"]
    zero_var = [c for c in feats if df[c].nunique() <= 1]
    return df.drop(columns=zero_var), zero_var


def log_transform(df):
    numeric = [c for c in df.columns if c not in CATEGORICAL + ["class"]]
    df[numeric] = np.sign(df[numeric]) * np.log1p(df[numeric].abs())
    return df, numeric


def one_hot_encode(df):
    return pd.get_dummies(df, columns=CATEGORICAL, prefix="Protocol", dtype=np.int8)


def add_binary_label(df):
    df["label"] = (df["class"] != "Normal").astype(np.int8)
    return df


def save_outputs(df, zero_var, available, stats, seed, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    df.to_parquet(f"{out_dir}/clean.parquet", index=False)
    feature_cols = [c for c in df.columns if c not in ("class", "label")]
    meta = {"seed": seed, "feature_cols": feature_cols, "zero_variance_dropped": zero_var,
            "available_after_cleaning": available, "kept": df["class"].value_counts().to_dict(),
            "stats": stats}
    with open(f"{out_dir}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    return feature_cols


def write_report(df, zero_var, numeric, feature_cols, available, stats, seed, report_path):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    short = {k: v for k, v in TABLE2.items() if available.get(k, 0) < v}
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Preprocessing Report (Phase 3)\n\n")
        f.write(f"Script: `scripts/preprocess.py`, seed {seed}. Output: `data/processed/clean.parquet` (unscaled; see `scripts/splits.py`).\n\n")
        f.write(f"- Raw files: {stats['files']}; rows read: {stats['rows_read']:,}\n")
        f.write(f"- Removed: {stats['header_rows']} repeated header rows, {stats['unmapped_label_rows']} unmapped-label rows, "
                f"{stats['nan_or_inf_rows']:,} rows with NaN/inf\n\n")
        f.write("## Class counts: paper Table 2 vs ours\n\n| Class | PAPER (Table 2) | Available after cleaning | OUR (kept) |\n|---|---|---|---|\n")
        for k, v in TABLE2.items():
            f.write(f"| {k} | {v:,} | {available.get(k, 0):,} | {len(df[df['class'] == k]):,} |\n")
        f.write(f"| **Total** | {sum(TABLE2.values()):,} | {sum(available.values()):,} | {len(df):,} |\n\n")
        if short:
            f.write(f"**Shortfall:** {short} — fewer rows exist than Table 2 requires; all available rows were kept (not resampled with replacement).\n\n")
        f.write(f"## Features\n\n- Dropped identifiers: {DROP_COLS}\n- Dropped zero-variance ({len(zero_var)}): {zero_var}\n"
                f"- Numeric features log-transformed (signed log1p): {len(numeric)}\n- One-hot: {CATEGORICAL}\n"
                f"- Final feature count: **{len(feature_cols)}** (paper: 43 raw NetFlow features — different feature set, see docs/UNSPECIFIED.md)\n")


def main(raw_glob=RAW_GLOB, out_dir=OUT_DIR, report_path=REPORT_PATH, seed=SEED):
    kept, available, stats = sample_raw_files(raw_glob, seed)
    df = combine_and_shuffle(kept, seed)
    df, zero_var = drop_zero_variance(df)
    df, numeric = log_transform(df)
    df = one_hot_encode(df)
    df = add_binary_label(df)
    feature_cols = save_outputs(df, zero_var, available, stats, seed, out_dir)
    write_report(df, zero_var, numeric, feature_cols, available, stats, seed, report_path)
    print(df["class"].value_counts())
    print("features:", len(feature_cols), "shape:", df.shape)
    return df


if __name__ == "__main__":
    main()
