import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

ATTACKS = ["DDoS", "DoS", "Bot", "Brute force", "Infiltration", "Web"]
DATA_PATH = "data/processed/clean.parquet"


def split_rows(df, unknown, seed):
    known, held_out = df[df["class"] != unknown], df[df["class"] == unknown]
    train, test = train_test_split(known, test_size=0.2, stratify=known["class"], random_state=seed)
    train, val = train_test_split(train, test_size=0.1, stratify=train["class"], random_state=seed)
    test = pd.concat([test, held_out])
    return train, val, test


def scale_parts(parts, feats):
    scaler = MinMaxScaler().fit(parts["train"][feats])
    out = {"scaler": scaler, "feature_cols": feats}
    for name, part in parts.items():
        out[f"X_{name}"] = np.clip(scaler.transform(part[feats]), 0, 1).astype(np.float32)
        out[f"y_{name}"] = part["label"].to_numpy()
        out[f"cls_{name}"] = part["class"].to_numpy()
    return out


def make_split(unknown, seed=42, path=DATA_PATH):
    assert unknown in ATTACKS, f"unknown must be one of {ATTACKS}"
    df = pd.read_parquet(path)
    feats = [c for c in df.columns if c not in ("class", "label")]
    train, val, test = split_rows(df, unknown, seed)
    return scale_parts({"train": train, "val": val, "test": test}, feats)


def check_no_leakage(split, unknown):
    seen_in_training = set(split["cls_train"]) | set(split["cls_val"])
    assert unknown not in seen_in_training, "unknown class leaked into train/val"


if __name__ == "__main__":
    s = make_split("DoS")
    for k in ("train", "val", "test"):
        print(k, s[f"X_{k}"].shape, "attack frac", round(s[f"y_{k}"].mean(), 3))
    check_no_leakage(s, "DoS")
    print("no leakage of unknown class into train/val: OK")
