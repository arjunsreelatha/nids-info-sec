import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

DATA_PATH = "data/processed/clean.parquet"
META_PATH = "data/processed/meta.json"
PLOT_DIR = "docs/eda"
REPORT_PATH = "docs/EDA_report.md"

TABLE2 = {"Normal": 122000, "DDoS": 64000, "DoS": 48000, "Bot": 14000,
          "Brute force": 11000, "Infiltration": 10000, "Web": 3702}
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"


def set_plot_style():
    plt.rcParams.update({"font.family": "sans-serif", "text.color": INK, "axes.labelcolor": INK2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb",
                         "axes.facecolor": "#fcfcfb", "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6})


def save_figure(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_class_balance(df, plot_dir):
    classes = list(TABLE2)
    paper = [TABLE2[c] for c in classes]
    ours = [int((df["class"] == c).sum()) for c in classes]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    y = np.arange(len(classes))
    ax.barh(y - 0.2, paper, 0.36, color=BLUE, label="Paper (Table 2)")
    ax.barh(y + 0.2, ours, 0.36, color=ORANGE, label="Ours (kept)")
    for yi, p, o in zip(y, paper, ours):
        ax.text(p, yi - 0.2, f" {p:,}", va="center", fontsize=8, color=INK2)
        ax.text(o, yi + 0.2, f" {o:,}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y, classes)
    ax.invert_yaxis()
    ax.set_xlim(0, 140000)
    ax.set_xlabel("Rows")
    ax.grid(axis="y", visible=False)
    ax.set_title("Class balance: paper vs ours (Web is short: only 928 rows exist)", loc="left", fontsize=11)
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, f"{plot_dir}/class_balance.png")
    return classes, paper, ours


def rank_features_by_separation(df, feats):
    normal, attack = df[df["label"] == 0], df[df["label"] == 1]
    scores = {f: ks_2samp(normal[f], attack[f]).statistic for f in feats}
    return pd.Series(scores).sort_values(ascending=False)


def plot_feature_distributions(df, ks, top, plot_dir):
    normal, attack = df[df["label"] == 0], df[df["label"] == 1]
    fig, axes = plt.subplots(2, 4, figsize=(13, 5.6))
    for ax, f in zip(axes.ravel(), top):
        bins = np.histogram_bin_edges(df[f], bins=40)
        ax.hist(normal[f], bins=bins, color=BLUE, alpha=0.75, density=True, label="Normal")
        ax.hist(attack[f], bins=bins, color=ORANGE, alpha=0.75, density=True, label="Attack")
        ax.set_title(f"{f}  (KS {ks[f]:.2f})", fontsize=9, loc="left")
        ax.tick_params(labelsize=8)
        ax.set_yticks([])
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.suptitle("Top 8 most separating features, log-transformed (density; normal vs attack)", x=0.01, ha="left", fontsize=11)
    save_figure(fig, f"{plot_dir}/feature_distributions.png")


def class_separability(df, classes, top):
    normal = df[df["label"] == 0]
    return pd.DataFrame({f: {c: ks_2samp(normal[f], df[df["class"] == c][f]).statistic
                             for c in classes[1:]} for f in top})


def plot_class_separability(sep, top, plot_dir):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.imshow(sep.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(top)), top, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(sep)), sep.index)
    ax.grid(False)
    for i in range(sep.shape[0]):
        for j in range(sep.shape[1]):
            v = sep.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color="white" if v > 0.55 else INK)
    ax.set_title("Separability from normal per attack class (KS statistic; low = hard to detect)", loc="left", fontsize=11)
    save_figure(fig, f"{plot_dir}/class_separability.png")


def write_report(df, feats, classes, paper, ours, ks, sep, report_path):
    desc = df[feats].describe().T[["mean", "std", "min", "max"]]
    hardest = sep.max(axis=1).sort_values().index[0]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# EDA Report (Phase 3)\n\nSource: `data/processed/clean.parquet` (after `scripts/preprocess.py`). Regenerate with `python scripts/eda.py`.\n\n")
        f.write(f"- Rows: {len(df):,}; features: {len(feats)}; attack share: {df['label'].mean():.1%} (normal {1 - df['label'].mean():.1%})\n")
        f.write(f"- Missing values: {int(df[feats].isna().sum().sum())}; constant columns remaining: {sum(df[c].nunique() <= 1 for c in feats)}\n\n")
        f.write("## Class balance\n\n![class balance](eda/class_balance.png)\n\n")
        f.write("| Class | PAPER (Table 2) | OUR |\n|---|---|---|\n")
        for c, p, o in zip(classes, paper, ours):
            f.write(f"| {c} | {p:,} | {o:,} |\n")
        f.write("\nWeb is the only shortfall (928 of 3,702). It is also the smallest class, so any Web holdout run has a small test group.\n\n")
        f.write("## Feature distributions\n\n![feature distributions](eda/feature_distributions.png)\n\n")
        f.write("Top 10 features by KS statistic between normal and attack:\n\n| Feature | KS |\n|---|---|\n")
        for name, v in ks.head(10).items():
            f.write(f"| {name} | {v:.3f} |\n")
        f.write("\n## Per-class separability\n\n![separability](eda/class_separability.png)\n\n")
        f.write(f"Least separable class on these features: **{hardest}** (max KS {sep.max(axis=1).min():.2f}). "
                "Classes that look like normal traffic are the ones a supervised RF is most likely to miss when held out as unknown.\n\n")
        f.write("## Feature summary (log-transformed, unscaled)\n\n| Feature | mean | std | min | max |\n|---|---|---|---|---|\n")
        for name, r in desc.iterrows():
            f.write(f"| {name} | {r['mean']:.3f} | {r['std']:.3f} | {r['min']:.3f} | {r['max']:.3f} |\n")


def main(data_path=DATA_PATH, meta_path=META_PATH, plot_dir=PLOT_DIR, report_path=REPORT_PATH):
    set_plot_style()
    os.makedirs(plot_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    df = pd.read_parquet(data_path)
    with open(meta_path) as f:
        feats = json.load(f)["feature_cols"]

    classes, paper, ours = plot_class_balance(df, plot_dir)
    ks = rank_features_by_separation(df, feats)
    top = ks.head(8).index.tolist()
    plot_feature_distributions(df, ks, top, plot_dir)
    sep = class_separability(df, classes, top)
    plot_class_separability(sep, top, plot_dir)
    write_report(df, feats, classes, paper, ours, ks, sep, report_path)
    print("top features:", top)
    print(sep.round(2))


if __name__ == "__main__":
    main()
