import os
import sys
import time
import random
import re
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
import recordlinkage
import dedupe
from dedupe import variables
from dedupe.core import BlockingError

# ============================================================
# CONFIGURAZIONE
# ============================================================


# Assicurati che questi nomi file siano corretti per il tuo collega
CRAIGSLIST_RAW = 'vehicles.csv'        # File con colonna "VIN"
USEDCARS_RAW   = 'used_cars_data.csv'  # File con colonna "vin"

OUT_DIR = "data/full_dataset" # Ho cambiato nome cartella per distinguere
CRAIGSLIST_SAMPLE = f"{OUT_DIR}/vehicles.csv"
USEDCARS_SAMPLE = f"{OUT_DIR}/used_cars_data.csv"


CSV_CHUNKSIZE = 100_000

MEDIATED_SCHEMA = [
    "vin", "make", "model", "year", "price", "mileage",
    "fuel", "transmission", "state", "region", "description"
]

CRAIGSLIST_MAPPING = {
    "VIN": "vin", "manufacturer": "make", "model": "model", "year": "year",
    "price": "price", "odometer": "mileage", "fuel": "fuel",
    "transmission": "transmission", "state": "state", "region": "region",
    "description": "description"
}

USEDCARS_MAPPING = {
    "vin": "vin",
    "make_name": "make",
    "model_name": "model",
    "year": "year",
    "price": "price",
    "mileage": "mileage",
    "fuel_type": "fuel",
    "transmission": "transmission",
    "description": "description"
}

# ============================================================
# 1. DATASET BUILD (VIN SOLO PER GT)
# ============================================================

def get_vins_lightweight(path, vin_col):
    vins = set()
    for chunk in pd.read_csv(path, usecols=[vin_col],
                             chunksize=CSV_CHUNKSIZE,
                             low_memory=False):
        vins.update(chunk[vin_col].dropna().astype(str))
    return vins


def stream_and_filter(path, vins, mapping):
    vin_col = [k for k, v in mapping.items() if v == "vin"][0]
    make_col = [k for k, v in mapping.items() if v == "make"][0]
    year_col = [k for k, v in mapping.items() if v == "year"][0]

    dfs = []
    for chunk in pd.read_csv(path,
                             chunksize=CSV_CHUNKSIZE,
                             low_memory=False):
        chunk[vin_col] = chunk[vin_col].astype(str)
        chunk = chunk[chunk[vin_col].isin(vins)]
        if chunk.empty:
            continue

        chunk = chunk.dropna(subset=[make_col, year_col])
        chunk = chunk[
            ~chunk[make_col].astype(str).str.lower().str.contains("unknown")
        ]
        dfs.append(chunk)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def build_dataset():
    if os.path.exists(CRAIGSLIST_SAMPLE) and os.path.exists(USEDCARS_SAMPLE):
         # Se i file esistono, li elimino
        if os.path.exists(CRAIGSLIST_SAMPLE):
            os.remove(CRAIGSLIST_SAMPLE)
            print(f"🗑 Eliminato file esistente: {CRAIGSLIST_SAMPLE}")

        if os.path.exists(USEDCARS_SAMPLE):
            os.remove(USEDCARS_SAMPLE)
            print(f"🗑 Eliminato file esistente: {USEDCARS_SAMPLE}")

    print("▶ Lettura VIN dai file raw...")
    vins_cl = get_vins_lightweight(CRAIGSLIST_RAW, "VIN")
    vins_uc = get_vins_lightweight(USEDCARS_RAW, "vin")

    # INTERSEZIONE COMPLETA
    common_vins = list(vins_cl.intersection(vins_uc))
    
    if not common_vins:
        print("❌ Nessun VIN in comune trovato nei file raw.")
        sys.exit(1)

    print(f"▶ Trovati {len(common_vins)} VIN in comune. Estrazione di TUTTI i dati (nessun campionamento)...")

    # USIAMO TUTTI I VIN (Nessun random.sample)
    target_vins = set(common_vins)

    df_cl = stream_and_filter(CRAIGSLIST_RAW, target_vins, CRAIGSLIST_MAPPING)
    df_uc = stream_and_filter(USEDCARS_RAW, target_vins, USEDCARS_MAPPING)

    # Intersezione finale post-pulizia (senza limiti numerici)
    final_vins = list(set(df_cl["VIN"]).intersection(df_uc["vin"]))

    df_cl = df_cl[df_cl["VIN"].isin(final_vins)]
    df_uc = df_uc[df_uc["vin"].isin(final_vins)]

    os.makedirs(OUT_DIR, exist_ok=True)
    df_cl.to_csv(CRAIGSLIST_SAMPLE, index=False)
    df_uc.to_csv(USEDCARS_SAMPLE, index=False)
    print(f"✔ Dataset completo creato con {len(final_vins)} coppie.")


# ============================================================
# 2. CLEANING & SCHEMA
# ============================================================

def clean_text(v):
    if pd.isna(v):
        return ""
    return re.sub(r"[^a-z0-9]", "", str(v).lower())


def align_to_schema(df, mapping):
    df = df.rename(columns=mapping)

    for c in MEDIATED_SCHEMA:
        if c not in df.columns:
            df[c] = ""

    df = df[MEDIATED_SCHEMA].fillna("")

    for c in ["make", "model"]:
        df[c] = df[c].apply(clean_text)

    df["year"] = df["year"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["price"] = df["price"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["price_num"] = pd.to_numeric(df["price"], errors="coerce")

    return df


def feature_analysis(df):
    return pd.DataFrame([{
        "attribute": c,
        "null_%": round(df[c].isna().mean() * 100, 2),
        "unique": df[c].nunique()
    } for c in df.columns])

# ============================================================
# 3. RECORD LINKAGE
# ============================================================

def run_record_linkage(df1, df2, strategy):
    indexer = recordlinkage.Index()

    if strategy == "B1":
        indexer.block("make")
    else:
        indexer.sortedneighbourhood("year", window=1)

    candidates = indexer.index(df1, df2)
    if len(candidates) == 0:
        return []

    compare = recordlinkage.Compare()
    compare.string("make", "make", method="jarowinkler", threshold=0.9)
    compare.string("model", "model", method="jarowinkler", threshold=0.8)
    compare.string("year", "year", method="levenshtein", threshold=0.9)
    compare.numeric("price_num", "price_num", method="gauss", offset=0.2, scale=0.2)

    features = compare.compute(candidates, df1, df2)
    return features[features.sum(axis=1) >= 3].index.tolist()

# ============================================================
# 4. DEDUPE
# ============================================================

def safe(v):
    if pd.isna(v) or str(v).strip() == "":
        return None
    return str(v)

def safe_price(v):
    try:
        v = float(v)
        return v if v > 0 else None
    except:
        return None

def train_dedupe(df1, df2, train_gt):
    print("▶ [Dedupe] Training in modalità sandbox")

    fields = [
        variables.String("make", has_missing=True),
        variables.String("model", has_missing=True),
        variables.ShortString("year", has_missing=True),
        variables.Price("price", has_missing=True)
    ]

    linker = dedupe.RecordLink(fields)

    # Dizionari completi
    c_data_full = {
        f"c_{r.orig_cl_id}": {
            "make": safe(r.make), "model": safe(r.model),
            "year": safe(r.year), "price": safe_price(r.price_num)
        } for _, r in df1.iterrows()
    }

    u_data_full = {
        f"u_{r.orig_uc_id}": {
            "make": safe(r.make), "model": safe(r.model),
            "year": safe(r.year), "price": safe_price(r.price_num)
        } for _, r in df2.iterrows()
    }

    # Dataset ridotto per training sicuro
    subset_size = min(len(train_gt), 50)
    train_subset = train_gt.sample(subset_size, random_state=42)

    labeled = {"match": [], "distinct": []}
    used_c, used_u = set(), set()

    for _, r in train_subset.iterrows():
        ck, uk = f"c_{r.orig_cl_id}", f"u_{r.orig_uc_id}"
        labeled["match"].append((c_data_full[ck], u_data_full[uk]))
        used_c.add(ck)
        used_u.add(uk)

    while len(labeled["distinct"]) < len(labeled["match"]):
        k1 = random.choice(list(c_data_full))
        k2 = random.choice(list(u_data_full))
        if k1 != k2:
            labeled["distinct"].append((c_data_full[k1], u_data_full[k2]))
            used_c.add(k1)
            used_u.add(k2)

    c_train = {k: c_data_full[k] for k in used_c}
    u_train = {k: u_data_full[k] for k in used_u}

    linker.prepare_training(c_train, u_train, sample_size=len(c_train)+len(u_train))
    linker.mark_pairs(labeled)
    linker.train()

    return linker, c_data_full, u_data_full

def run_dedupe_B1(linker, c_data, u_data, threshold=0.5):
    print("   [Dedupe-B1] Blocking su make")
    pairs = []
    makes = {v["make"] for v in c_data.values() if v.get("make")}

    for mk in makes:
        c_block = {k: v for k, v in c_data.items() if v.get("make") == mk}
        u_block = {k: v for k, v in u_data.items() if v.get("make") == mk}

        if not c_block or not u_block: continue

        try:
            linked = linker.join(c_block, u_block, threshold=threshold)
            for (id1, id2), _ in linked:
                pairs.append((int(id1.replace("c_", "")), int(id2.replace("u_", ""))))
        except BlockingError: continue
    return pairs

def run_dedupe_B2(linker, c_data, u_data, threshold=0.5):
    print("   [Dedupe-B2] Blocking su year")
    pairs = []
    years = {v["year"] for v in c_data.values() if v.get("year")}

    for y in years:
        c_block = {k: v for k, v in c_data.items() if v.get("year") == y}
        u_block = {k: v for k, v in u_data.items() if v.get("year") == y}

        if not c_block or not u_block: continue

        try:
            linked = linker.join(c_block, u_block, threshold=threshold)
            for (id1, id2), _ in linked:
                pairs.append((int(id1.replace("c_", "")), int(id2.replace("u_", ""))))
        except BlockingError: continue
    return pairs

# ============================================================
# 6. DITTO EXPORT
# ============================================================

def serialize_row(row):
    """Serializza una riga nel formato COL val COL val... richiesto da Ditto"""
    # Escludiamo colonne tecniche o non utili per il matching testuale
    ignore = ["vin", "orig_cl_id", "orig_uc_id", "price_num"]
    items = []
    for col, val in row.items():
        if col not in ignore:
            items.append(f"COL {col} VAL {val}")
    return " ".join(items)

def export_ditto_data(df_gt, df1, df2, filename):
    """Genera file train/val/test per Ditto (con negativi casuali)"""
    print(f"   Exporting {filename}...")
    lines = []

    # 1. Positivi (Match reali)
    for _, row in df_gt.iterrows():
        r1 = df1.loc[row["orig_cl_id"]]
        r2 = df2.loc[row["orig_uc_id"]]
        lines.append(f"{serialize_row(r1)}\t{serialize_row(r2)}\t1")

    # 2. Negativi (Casuali per bilanciare)
    # Generiamo tanti negativi quanti positivi
    n_pos = len(lines)
    all_id1 = df1.index.tolist()
    all_id2 = df2.index.tolist()

    count = 0
    while count < n_pos:
        id1 = random.choice(all_id1)
        id2 = random.choice(all_id2)

        # Controllo VIN per essere certi sia negativo
        # (df1/df2 qui devono avere il VIN, quindi usiamo quelli originali nel main)
        if df1.loc[id1, "vin"] != df2.loc[id2, "vin"]:
            r1 = df1.loc[id1]
            r2 = df2.loc[id2]
            lines.append(f"{serialize_row(r1)}\t{serialize_row(r2)}\t0")
            count += 1

    # Shuffle
    random.shuffle(lines)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ============================================================
# METRICHE
# ============================================================

def eval_metrics(pairs, gt):
    pred = set(pairs)
    true = set(zip(gt.orig_cl_id, gt.orig_uc_id))

    tp = len(pred & true)
    fp = len(pred - true)
    fn = len(true - pred)

    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    return p, r, f1

# ============================================================
# MAIN
# ============================================================

def main():
    build_dataset()

    cl = align_to_schema(pd.read_csv(CRAIGSLIST_SAMPLE), CRAIGSLIST_MAPPING)
    uc = align_to_schema(pd.read_csv(USEDCARS_SAMPLE), USEDCARS_MAPPING)

    cl["orig_cl_id"] = cl.index
    uc["orig_uc_id"] = uc.index

    print("\n▶ Analisi attributi:")
    print(feature_analysis(cl).head())

    # Ground truth (VIN)
    gt = cl.merge(uc, on="vin")[["orig_cl_id", "orig_uc_id"]]
    print(f"▶ Ground Truth Totale: {len(gt)} coppie")

    # Split train / val / test
    train_gt, temp = train_test_split(gt, test_size=0.4, random_state=42)
    val_gt, test_gt = train_test_split(temp, test_size=0.5, random_state=42)

    # --- EXPORT DITTO (Prima di droppare VIN) ---
    print("\n--- Export Ditto ---")
    # Passiamo cl/uc completi (con vin) per verifica negativi
    export_ditto_data(train_gt, cl, uc, f"{OUT_DIR}/ditto_train.txt")
    export_ditto_data(val_gt, cl, uc, f"{OUT_DIR}/ditto_val.txt")
    export_ditto_data(test_gt, cl, uc, f"{OUT_DIR}/ditto_test.txt")
    print("✔ File generati. Eseguire training su Colab/GPU.")

    # RIMOZIONE VIN PER IL RESTO
    cl_novin = cl.drop(columns=["vin"])
    uc_novin = uc.drop(columns=["vin"])

    print("\n--- Record Linkage ---")
    for b in ["B1", "B2"]:
        t0 = time.time()
        pairs = run_record_linkage(cl_novin, uc_novin, b)
        p, r, f1 = eval_metrics(pairs, test_gt)
        print(f"RL-{b} | P={p:.2f} R={r:.2f} F1={f1:.2f} "
              f"Time={time.time()-t0:.3f}s")

    print("\n--- Dedupe ---")
    t0 = time.time()
    linker, c_data, u_data = train_dedupe(cl_novin, uc_novin, train_gt)
    train_time = time.time() - t0

    t0 = time.time()
    pairs_B1 = run_dedupe_B1(linker, c_data, u_data)
    p, r, f1 = eval_metrics(pairs_B1, test_gt)
    print(f"Dedupe-B1 | P={p:.2f} R={r:.2f} F1={f1:.2f} "
          f"Train={train_time:.2f}s Inf={time.time()-t0:.3f}s")

    t0 = time.time()
    pairs_B2 = run_dedupe_B2(linker, c_data, u_data)
    p, r, f1 = eval_metrics(pairs_B2, test_gt)
    print(f"Dedupe-B2 | P={p:.2f} R={r:.2f} F1={f1:.2f} "
          f"Train={train_time:.2f}s Inf={time.time()-t0:.3f}s")
    
    # --- BLOCKING STATS FOR DITTO ---
    print("\n--- Analisi Blocking per Ditto (4.H) ---")
    # Calcoliamo quanti match veri del TEST set sopravvivono al blocking
    # Questo è il "limite superiore" (Recall massima) per le pipeline B1-Ditto e B2-Ditto
    indexer_b1 = recordlinkage.Index(); indexer_b1.block("make")
    cand_b1 = indexer_b1.index(cl_novin, uc_novin)
    
    indexer_b2 = recordlinkage.Index(); indexer_b2.sortedneighbourhood("year", window=1)
    cand_b2 = indexer_b2.index(cl_novin, uc_novin)
    
    # Calcolo Recall del blocking
    true_pairs = set(zip(test_gt.orig_cl_id, test_gt.orig_uc_id))
    
    captured_b1 = len(set(cand_b1).intersection(true_pairs))
    recall_b1 = captured_b1 / len(true_pairs) if true_pairs else 0
    
    captured_b2 = len(set(cand_b2).intersection(true_pairs))
    recall_b2 = captured_b2 / len(true_pairs) if true_pairs else 0
    
    print(f"B1 Blocking (Make): Candidati={len(cand_b1)}, Recall Max={recall_b1:.2f}")
    print(f"B2 Blocking (Year): Candidati={len(cand_b2)}, Recall Max={recall_b2:.2f}")
    print("Nota: La Recall finale di Ditto sarà: (Recall Max) * (Recall del modello Ditto su Colab)")


    print("\n✔ PIPELINE COMPLETATA")


if __name__ == "__main__":
    main()