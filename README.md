# NIDS: Random Forest + Autoencoder

Student reproduction of *"A Dual-Layer AI-Based Approach for Real-Time Network Intrusion Detection Using Random Forest and Autoencoder"* (Khemani et al., Journal on Information Security, 2026) on CICIDS2018, with a monitoring dashboard.

A Random Forest flags a flow when its attack probability exceeds T1. An autoencoder then rechecks flagged flows, and a low reconstruction error (below T2) turns the flag back into normal.

## Status

- Done: dataset scan and dev sample, preprocessing, EDA, leakage-safe train/val/test split, mock-data dashboard.
- Not yet: RF, RF(Pro) and AE baselines, hybrid model, unknown-attack experiment, `/predict` API.

## Setup

```
pip install -r requirements.txt
```

Download the CICIDS2018 CSVs from Kaggle (`solarmainframe/ids-intrusion-csv`) into `data/raw/`. The raw data is about 6.7 GB and is not in this repo.

## Run

```
python scripts/analyze_dataset.py   # scan raw files, write data/sample/sample.csv
python scripts/preprocess.py        # sample to paper Table 2 counts, write data/processed/clean.parquet
python scripts/eda.py               # class balance and feature plots
python scripts/splits.py            # test the train/val/test split
```

Dashboard (mock data):

```
cd frontend
npm install
npm run dev
```

## Layout

- `scripts/`: data pipeline (`analyze_dataset.py`, `preprocess.py`, `eda.py`, `splits.py`)
- `frontend/`: React dashboard
- `data/sample/`: small reproducible sample (seed 42)

## Notes

- Only 928 Web attack rows exist in the dataset; the paper's Table 2 lists 3,702. All 928 are kept.
- The raw data has about 80 features per flow, not the paper's 43. After dropping identifiers and constant columns, 72 features remain.
- Binary classification only (normal vs attack), as in the paper.
