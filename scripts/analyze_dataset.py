import glob
import os

import numpy as np
import pandas as pd

SEED = 42
SAMPLE_PER_CLASS = 500
CHUNK = 500_000
LABEL = "Label"
RAW_GLOB = "data/raw/*.csv"
SAMPLE_PATH = "data/sample/sample.csv"
REPORT_PATH = "docs/dataset_report.md"
TABLE2 = {"Normal": 122000, "DDoS": 64000, "DoS": 48000, "Bot": 14000,
          "Brute force": 11000, "Infiltration": 10000, "Web": 3702}


def scan_raw_files(raw_glob, seed):
    rng = np.random.default_rng(seed)
    counts, per_file, reservoir, columns_seen = {}, [], {}, {}
    totals = {"rows": 0, "header_rows": 0, "nan": 0, "inf": 0}
    files = sorted(glob.glob(raw_glob))
    for path in files:
        file_rows = 0
        for chunk in pd.read_csv(path, chunksize=CHUNK, low_memory=False):
            columns_seen.setdefault(path, list(chunk.columns))
            chunk = drop_header_rows(chunk, totals)
            count_bad_cells(chunk, totals)
            file_rows += len(chunk)
            collect_class_samples(chunk, counts, reservoir, rng)
        totals["rows"] += file_rows
        per_file.append((os.path.basename(path), file_rows, len(columns_seen[path])))
        print(path, file_rows, "rows", flush=True)
    return files, counts, per_file, reservoir, columns_seen, totals


def drop_header_rows(chunk, totals):
    is_header = chunk[LABEL] == LABEL
    totals["header_rows"] += int(is_header.sum())
    return chunk[~is_header]


def count_bad_cells(chunk, totals):
    numeric = chunk.select_dtypes(include=[np.number])
    totals["nan"] += int(numeric.isna().sum().sum())
    totals["inf"] += int(np.isinf(numeric.to_numpy()).sum())


def collect_class_samples(chunk, counts, reservoir, rng):
    for label, rows in chunk.groupby(LABEL):
        counts[label] = counts.get(label, 0) + len(rows)
        keep = rows.sample(min(len(rows), SAMPLE_PER_CLASS), random_state=int(rng.integers(1 << 31)))
        reservoir.setdefault(label, []).append(keep)


def build_sample(reservoir, seed):
    per_class = [pd.concat(parts).sample(min(SAMPLE_PER_CLASS, sum(map(len, parts))), random_state=seed)
                 for parts in reservoir.values()]
    return pd.concat(per_class)


def write_report(report_path, files, counts, per_file, columns_seen, totals, sample, seed):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    first = next(iter(columns_seen.values()))
    extra = {os.path.basename(p): sorted(set(c) - set(first)) for p, c in columns_seen.items() if set(c) - set(first)}
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Dataset Report (Phase 2)\n\n")
        f.write("Source: Kaggle `solarmainframe/ids-intrusion-csv` (the dataset the paper links).\n\n")
        f.write(f"- Files: {len(files)}; total data rows: **{totals['rows']:,}** (paper Table 2 total: {sum(TABLE2.values()):,})\n")
        f.write(f"- Repeated header rows dropped: {totals['header_rows']}; NaN cells: {totals['nan']:,}; inf cells: {totals['inf']:,}\n")
        f.write(f"- Dev sample: `data/sample/sample.csv`, {len(sample):,} rows, seed {seed}, max {SAMPLE_PER_CLASS} per label\n\n")
        f.write("## Label counts (actual)\n\n| Label | Rows |\n|---|---|\n")
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
            f.write(f"| {k} | {v:,} |\n")
        f.write("\n## Paper Table 2 (target)\n\n| Class | Rows |\n|---|---|\n")
        for k, v in TABLE2.items():
            f.write(f"| {k} | {v:,} |\n")
        f.write("\n## Per file\n\n| File | Rows | Columns |\n|---|---|---|\n")
        for name, n, c in per_file:
            f.write(f"| {name} | {n:,} | {c} |\n")
        f.write(f"\n## Columns ({len(first)}, from first file)\n\n" + ", ".join(f"`{c}`" for c in first) + "\n")
        if extra:
            f.write(f"\nExtra columns in some files: {extra}\n")


def main(raw_glob=RAW_GLOB, sample_path=SAMPLE_PATH, report_path=REPORT_PATH, seed=SEED):
    files, counts, per_file, reservoir, columns_seen, totals = scan_raw_files(raw_glob, seed)
    sample = build_sample(reservoir, seed)
    os.makedirs(os.path.dirname(sample_path), exist_ok=True)
    sample.to_csv(sample_path, index=False)
    write_report(report_path, files, counts, per_file, columns_seen, totals, sample, seed)
    print("total rows", totals["rows"])
    print(pd.Series(counts).sort_values(ascending=False))
    print("sample", sample.shape)


if __name__ == "__main__":
    main()
