# Zero-Day IoT Attack Detection — Complete Code Explanation

> **Purpose of this document:** A beginner-friendly, line-by-line explanation of every notebook in this project. Written so you can read it, understand what each piece of code does, and confidently explain it yourself.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Notebook 01 — Data Preprocessing](#2-notebook-01--data-preprocessing)
3. [Notebook 02 — Known Attack Detection with LightGBM](#3-notebook-02--known-attack-detection-with-lightgbm)
4. [Notebook 03 — Zero-Day Detection with Autoencoder](#4-notebook-03--zero-day-detection-with-autoencoder)
5. [Notebook 04 — Fusion Model](#5-notebook-04--fusion-model)
6. [Notebook 05 — Visualization & Comparison](#6-notebook-05--visualization--comparison)
7. [How All Notebooks Connect](#7-how-all-notebooks-connect)
8. [Key Concepts Glossary](#8-key-concepts-glossary)

---

## 1. Project Overview

### What is this project about?

This project builds a **cybersecurity detection system for IoT (Internet of Things) devices**. IoT devices are things like smart cameras, sensors, routers, and smart home gadgets. These devices are often attacked by hackers.

The challenge in cybersecurity is **Zero-Day Attacks** — attacks that are brand new and have never been seen before. Traditional security systems only know how to detect attacks they have been trained on. If a hacker invents a new attack type, the system fails.

### What does this project solve?

This project uses **two AI models working together**:

| Model | Job |
|---|---|
| **LightGBM** | Recognizes known, named attacks (like DDoS, SQL Injection, etc.) |
| **Autoencoder (Neural Network)** | Detects unknown / new attacks by spotting "unusual" traffic |
| **Fusion Model** | Combines both models for the best of both worlds |

### Dataset Used

**Edge-IIoT Dataset** from Kaggle — a real-world IoT network traffic dataset.
- 157,800 rows of network traffic data
- 63 columns (network features like packet size, port numbers, etc.)
- 15 attack types + Normal traffic

### Project Pipeline (Big Picture)

```
Raw CSV Data
    ↓
01_Preprocessing  →  Clean data, split into Known / Zero-Day sets
    ↓
02_LightGBM       →  Train classifier on Known attacks
    ↓
03_Autoencoder    →  Train anomaly detector on Normal traffic only
    ↓
04_Fusion Model   →  Combine both models intelligently
    ↓
05_Visualization  →  Charts & comparison of all models
```

---

## 2. Notebook 01 — Data Preprocessing

**File:** `01_Preprocessing_Master.ipynb`

**Goal:** Load the raw dataset, clean it, and prepare it for the ML models.

---

### Step 1 — Install & Import Libraries

```python
!pip install kagglehub -q
```
- `!` means run a terminal command inside the notebook
- `pip install kagglehub` installs a tool to download datasets from Kaggle
- `-q` means "quiet" — don't show all the installation messages

```python
from google.colab import drive
drive.mount('/content/drive')
```
- This mounts (connects) Google Drive to the notebook
- All files will be saved to Google Drive so they persist after the session ends

```python
import pandas as pd       # For working with tables (DataFrames)
import numpy as np        # For math operations on arrays
import os                 # For file/folder operations
import gc                 # Garbage collector — frees up RAM
import joblib             # For saving/loading Python objects (like models)
import kagglehub          # For downloading Kaggle datasets

from sklearn.preprocessing import StandardScaler  # For scaling/normalizing data
```

**What each library does:**
- **pandas**: Think of it like Excel in Python — works with rows and columns of data
- **numpy**: Fast math on large arrays of numbers
- **os**: Create folders, check if files exist
- **gc**: Free up computer memory when no longer needed
- **joblib**: Save Python objects to disk (like saving a trained model)
- **sklearn**: Machine learning library — StandardScaler normalizes numbers

---

### Step 2 — Set Up Folder Paths

```python
BASE_PATH = "/content/drive/MyDrive/Zero-Day-IoT-Project"

DATA_PATH  = BASE_PATH + "/01_Data"
MODEL_PATH = BASE_PATH + "/03_Models"

os.makedirs(DATA_PATH,  exist_ok=True)
os.makedirs(MODEL_PATH, exist_ok=True)
```

- `BASE_PATH` is the root folder in Google Drive
- `DATA_PATH` is where data files will be saved
- `MODEL_PATH` is where trained models will be saved
- `os.makedirs(..., exist_ok=True)` creates the folder — if it already exists, don't crash

---

### Step 3 — Download the Dataset

```python
dataset_path = kagglehub.dataset_download("sibasispradhan/edge-iiotset-dataset")
print("Downloaded to:", dataset_path)
```

- Downloads the **Edge-IIoT dataset** from Kaggle automatically
- The dataset is ~351 MB
- The result is a local folder path where the CSV files are stored

---

### Step 4 — Load the CSV File

```python
file_path = dataset_path + "/ML-EdgeIIoT-dataset.csv"
df = pd.read_csv(file_path, low_memory=False)

print("Original Shape:", df.shape)
```

- `pd.read_csv(...)` reads the CSV file into a DataFrame (table)
- `low_memory=False` prevents pandas from guessing column types incorrectly on large files
- `df.shape` returns (rows, columns) → output: **(157800, 63)**
  - 157,800 rows of network traffic
  - 63 features (columns)

---

### Step 5 — Drop Irrelevant Columns

```python
drop_cols = [
    'frame.time',
    'ip.src_host',
    'ip.dst_host',
    'arp.src.proto_ipv4',
    'arp.dst.proto_ipv4',
    'http.request.full_uri',
    'http.request.uri.query',
    'http.file_data',
    'icmp.transmit_timestamp',
    'mqtt.msg'
]

df.drop(columns=drop_cols, inplace=True, errors='ignore')
print("After Drop:", df.shape)  # → (157800, 53)
```

**Why drop these columns?**
- `frame.time` — timestamp; not useful for detecting attack patterns
- `ip.src_host` / `ip.dst_host` — IP addresses are too specific; a model that memorizes IPs won't generalize
- `http.request.full_uri` / `http.file_data` — raw text data that needs special processing
- `mqtt.msg` — MQTT message content (too variable to use directly)

After dropping: **53 columns remain**

---

### Step 6 — Remove Nulls and Duplicates

```python
df.dropna(inplace=True)
df.drop_duplicates(inplace=True)
print("After Cleaning:", df.shape)  # → (152389, 53)
```

- `dropna()` removes any row that has a missing/empty value (NaN)
- `drop_duplicates()` removes exact duplicate rows
- Result: **152,389 rows** remain (about 5,400 rows removed)

---

### Step 7 — Check the Attack Distribution

```python
print(df['Attack_label'].value_counts())
print(df['Attack_type'].value_counts())
```

**Output:**
```
Attack_label
1    128237   ← Attack traffic
0     24152   ← Normal traffic

Attack_type
Normal                   24152
DDoS_UDP                 14498
DDoS_ICMP                13096
DDoS_HTTP                10559
SQL_injection            10286
DDoS_TCP                 10247
Uploading                10237
Vulnerability_scanner    10062
Password                  9978
Backdoor                  9866
Ransomware                9690
XSS                       9550
Port_Scanning             8921
Fingerprinting              853
MITM                        394
```

- `Attack_label = 1` means attack traffic, `0` means normal
- There are **15 attack types** in total
- The dataset is imbalanced — 128K attacks vs 24K normal traffic

---

### Step 8 — Save Attack Type Mapping

```python
mapping = pd.DataFrame({
    "Attack_type": sorted(df["Attack_type"].unique())
})
mapping.to_csv(DATA_PATH + "/attack_type_mapping.csv", index=False)
```

- Creates a CSV with the list of all 15 attack types (alphabetically sorted)
- This mapping file is useful for reference later

---

### Step 9 — Encode Text Columns

```python
obj_cols = df.select_dtypes(include='object').columns.tolist()

for col in obj_cols:
    df[col] = df[col].astype('category').cat.codes
```

- `select_dtypes(include='object')` finds all text/string columns
- ML models only understand numbers — so text must be converted
- `.astype('category').cat.codes` converts text categories to integers
  - Example: "Normal" → 7, "DDoS_UDP" → 4, "Backdoor" → 0

**Columns encoded:** `http.request.method`, `http.referer`, `tcp.options`, `mqtt.protoname`, `Attack_type`, and more

---

### Step 10 — Optimize Memory

```python
for col in df.select_dtypes(include='float64').columns:
    df[col] = df[col].astype('float32')

for col in df.select_dtypes(include='int64').columns:
    df[col] = df[col].astype('int32')
```

- `float64` uses 8 bytes per number; `float32` uses only 4 bytes
- `int64` uses 8 bytes; `int32` uses 4 bytes
- This cuts RAM usage roughly in half — important for large datasets

---

### Step 11 — Split into Known vs Zero-Day

```python
known_classes   = [7, 4, 2, 1, 11, 3, 8, 0, 10, 9]   # 10 attack types used for training
unknown_classes = [12, 13, 14, 5, 6]                   # 5 attack types hidden as "zero-day"

known_df = df[df['Attack_type'].isin(known_classes)].copy()
zero_df  = df[df['Attack_type'].isin(unknown_classes)].copy()

print("Known Train Shape:", known_df.shape)     # → (121293, 53)
print("Zero-Day Test Shape:", zero_df.shape)    # → (31096, 53)
```

**This is the key design decision of the project:**
- **Known classes** (10 types): The LightGBM model will be trained on these. It learns to identify these by name.
- **Unknown/Zero-Day classes** (5 types: Uploading, Vulnerability_scanner, XSS, Fingerprinting, MITM): These are **hidden** from the LightGBM model entirely. They simulate "new, never-seen attacks."

The numbers (0–14) are the encoded integer values of the attack types.

---

### Step 12 — Save Datasets

```python
df.to_parquet(DATA_PATH + "/master_clean.parquet")
known_df.to_parquet(DATA_PATH + "/known_train.parquet")
zero_df.to_parquet(DATA_PATH + "/zero_day_test.parquet")
```

- Saves as **Parquet format** (not CSV)
- Parquet is a compressed binary format — much faster to load and smaller in size than CSV
- Three files created:
  - `master_clean.parquet` — full cleaned dataset
  - `known_train.parquet` — only known attack types (for LightGBM training)
  - `zero_day_test.parquet` — zero-day attack types (for testing)

---

### Step 13 — Create and Save the Scaler

```python
feature_cols = [c for c in df.columns if c not in ['Attack_label', 'Attack_type']]

scaler = StandardScaler()
normal_known = known_df[known_df['Attack_label'] == 0]
scaler.fit(normal_known[feature_cols])

joblib.dump(scaler, MODEL_PATH + "/scaler.pkl")
```

**What is a StandardScaler?**
- Neural networks (like the Autoencoder) work best when all input numbers are on the same scale
- `StandardScaler` transforms data so each feature has mean = 0 and standard deviation = 1
- Formula: `z = (x - mean) / std_dev`

**Why fit only on Normal traffic?**
- The Autoencoder will be trained exclusively on Normal traffic
- So the scaler should only "learn" what normal looks like — not what attacks look like
- `scaler.fit(normal_known[feature_cols])` computes the mean and std of each feature from normal traffic only

`joblib.dump(scaler, ...)` saves the scaler to disk so other notebooks can reuse the exact same transformation.

---

### Step 14 — Free Memory

```python
del df
del known_df
del zero_df
gc.collect()
```

- `del` deletes the variable from memory
- `gc.collect()` forces Python to reclaim that memory immediately
- Good practice when working with large datasets in limited RAM

---

### Notebook 01 Summary

| Input | Output |
|---|---|
| Raw CSV (157,800 × 63) | `master_clean.parquet` (152,389 × 53) |
| — | `known_train.parquet` (121,293 × 53) |
| — | `zero_day_test.parquet` (31,096 × 53) |
| — | `attack_type_mapping.csv` |
| — | `scaler.pkl` |

---


## 3. Notebook 02 — Known Attack Detection with LightGBM

**File:** `02_Known_Attack_LightGBM.ipynb`

**Goal:** Train a powerful classifier that can identify the 10 known attack types (and normal traffic) by name.

---

### What is LightGBM?

**LightGBM** (Light Gradient Boosting Machine) is a fast and highly accurate ML algorithm made by Microsoft. It is based on **decision trees**.

**How does it work (simple explanation)?**
1. It builds many small decision trees one after another
2. Each new tree tries to fix the mistakes of the previous tree
3. Final prediction = combination of all trees

It's called "Light" because it's much faster than older boosting methods while achieving the same or better accuracy.

---

### Step 1 — Setup

```python
from google.colab import drive
drive.mount('/content/drive')

!pip install lightgbm -q
```

```python
import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import lightgbm as lgb
```

**New imports explained:**
- `train_test_split` — splits data into training and testing sets
- `classification_report` — shows precision, recall, F1-score for each class
- `confusion_matrix` — shows a table of correct vs incorrect predictions
- `lightgbm as lgb` — the LightGBM library itself

---

### Step 2 — Load the Dataset

```python
df = pd.read_parquet(DATA_PATH + "/known_train.parquet")
print("Dataset Shape:", df.shape)   # → (121293, 53)
```

- Loads the known-attacks-only dataset created in Notebook 01
- 121,293 rows, 53 columns

---

### Step 3 — Prepare Features and Target

```python
X = df.drop(columns=["Attack_type", "Attack_label"])
y = df["Attack_type"]

print("X Shape:", X.shape)     # → (121293, 51)
print("Classes:", y.nunique()) # → 10
```

- **X** = input features (51 columns — everything except the labels)
- **y** = target label (what we want to predict — the Attack_type, encoded as 0–14)
- `y.nunique()` = 10 unique classes (10 known attack types including Normal)

---

### Step 4 — Train/Test Split

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(X_train.shape, X_test.shape)  # → (97034, 51) (24259, 51)
```

**Parameters explained:**
- `test_size=0.2` → 20% of data goes to testing, 80% for training
  - Train: 97,034 rows | Test: 24,259 rows
- `random_state=42` → Fixed random seed so results are reproducible (same split every time)
- `stratify=y` → Ensures the class distribution in train and test sets matches the original
  - Without this, the split might accidentally have too many DDoS attacks in test but too few in train

---

### Step 5 — Train the LightGBM Model

```python
model = lgb.LGBMClassifier(
    objective="multiclass",
    num_class=y.nunique(),
    n_estimators=300,
    learning_rate=0.05,
    max_depth=10,
    num_leaves=50,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)
```

**Each parameter explained:**

| Parameter | Value | Meaning |
|---|---|---|
| `objective` | `"multiclass"` | This is a multi-class classification problem (10 classes) |
| `num_class` | `10` | Number of classes to predict |
| `n_estimators` | `300` | Build 300 decision trees |
| `learning_rate` | `0.05` | Each new tree contributes only 5% — prevents overfitting |
| `max_depth` | `10` | Each tree can be at most 10 levels deep |
| `num_leaves` | `50` | Each tree can have at most 50 leaf nodes |
| `subsample` | `0.8` | Use 80% of rows randomly for each tree — prevents overfitting |
| `colsample_bytree` | `0.8` | Use 80% of features randomly for each tree — prevents overfitting |
| `random_state` | `42` | For reproducibility |

**What is overfitting?**
When a model memorizes the training data but fails on new data. The `subsample` and `colsample_bytree` settings add randomness to prevent this.

---

### Step 6 — Evaluate the Model

```python
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
```

**Result: ~99.99% accuracy on known attacks**

**Classification Report explained:**
```
              precision    recall  f1-score   support
```
- **Precision**: Of all rows predicted as "DDoS_UDP", what % were actually DDoS_UDP?
- **Recall**: Of all actual DDoS_UDP rows, what % did the model correctly find?
- **F1-score**: Harmonic mean of precision and recall — overall quality per class
- **Support**: How many rows of that class were in the test set

---

### Step 7 — Feature Importance

```python
feat_importance = pd.DataFrame({
    "feature": X_train.columns,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)
```

- `feature_importances_` shows which features LightGBM relied on most
- Saved to `feature_importance.csv` for analysis

---

### Step 8 — Save the Model

```python
joblib.dump(model, MODEL_PATH + "/lightgbm_known.pkl")
```

- Saves the trained LightGBM model as a `.pkl` file (pickle format)
- Can be loaded and used in other notebooks without retraining

---

### Step 9 — Save Metrics

```python
report = classification_report(y_test, y_pred, output_dict=True)
pd.DataFrame(report).transpose().to_csv(REPORT_PATH + "/lightgbm_metrics.csv")
```

- `output_dict=True` returns the report as a Python dictionary instead of text
- Converts it to a DataFrame and saves it as a CSV

---

### Notebook 02 Summary

| Input | Output |
|---|---|
| `known_train.parquet` | `lightgbm_known.pkl` (trained model) |
| — | `lightgbm_metrics.csv` |
| — | `feature_importance.csv` |

**Key Result: 99.99% accuracy on 10 known attack types**

---

## 4. Notebook 03 — Zero-Day Detection with Autoencoder

**File:** `03_ZeroDay_Autoencoder.ipynb`

**Goal:** Train a neural network that learns what "normal" traffic looks like, so it can flag anything unusual as a potential zero-day attack.

---

### What is an Autoencoder?

An **Autoencoder** is a special type of neural network with two parts:
1. **Encoder**: Compresses the input into a smaller representation (bottleneck)
2. **Decoder**: Tries to reconstruct the original input from the compressed version

```
Input (51 features)
    → Encoder: 51 → 64 → 32 → 16 (bottleneck)
    → Decoder: 16 → 32 → 64 → 51
Output (51 features — reconstructed)
```

**The key idea for anomaly detection:**
- Train ONLY on normal traffic
- The autoencoder gets very good at reconstructing normal traffic (low reconstruction error)
- When it sees an attack (unusual traffic), it does a BAD job reconstructing it (high reconstruction error)
- **High reconstruction error = likely an attack**

---

### Step 1 — Imports and Setup

```python
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.callbacks import EarlyStopping
```

**TensorFlow / Keras explained:**
- **TensorFlow**: Google's deep learning framework
- **Keras**: A high-level API on top of TensorFlow — easier to use
- `Model` — base class for building neural network models
- `Input` — defines the input layer
- `Dense` — a fully connected neural network layer
- `EarlyStopping` — stops training early if the model stops improving (prevents overfitting)

---

### Step 2 — Load Data and Scaler

```python
df = pd.read_parquet(DATA_PATH + "/master_clean.parquet")
scaler = joblib.load(MODEL_PATH + "/scaler.pkl")
```

- Loads the full cleaned dataset (all 152,389 rows)
- Loads the scaler saved in Notebook 01 — important: use the SAME scaler everywhere

---

### Step 3 — Filter Only Normal Traffic for Training

```python
normal_df = df[df['Attack_label'] == 0].copy()
X_normal = normal_df[feature_cols]
X_normal_scaled = scaler.transform(X_normal)
print("Normal Data Shape:", X_normal_scaled.shape)  # → (24152, 51)
```

- **Only 24,152 rows of Normal traffic** are used for training
- `scaler.transform(X_normal)` scales the data using the scaler fitted in NB01
  - Note: `.transform()` applies the scaling; `.fit()` would recalculate it (we don't want that)

---

### Step 4 — Validation Split

```python
X_train, X_val = train_test_split(
    X_normal_scaled,
    test_size=0.2,
    random_state=42
)
print(X_train.shape, X_val.shape)  # → (19321, 51) (4831, 51)
```

- No labels needed here — both input AND output are `X_normal_scaled`
- The autoencoder just needs to learn to reconstruct its input
- 20% of normal traffic kept as validation to monitor training

---

### Step 5 — Build the Autoencoder

```python
input_dim = X_train.shape[1]   # = 51

inputs = Input(shape=(input_dim,))
x = Dense(64, activation='relu')(inputs)   # Encoder layer 1
x = Dense(32, activation='relu')(x)         # Encoder layer 2
x = Dense(16, activation='relu')(x)         # Bottleneck (compressed representation)
x = Dense(32, activation='relu')(x)         # Decoder layer 1
x = Dense(64, activation='relu')(x)         # Decoder layer 2
outputs = Dense(input_dim, activation='linear')(x)   # Output: reconstruct original

autoencoder = Model(inputs, outputs)
autoencoder.compile(optimizer='adam', loss='mse')
```

**Architecture breakdown:**

```
Input Layer:  51 neurons (one per feature)
Dense(64):    64 neurons — learns complex patterns
Dense(32):    32 neurons — compresses further
Dense(16):    16 neurons — BOTTLENECK (most compressed)
Dense(32):    32 neurons — starts expanding back
Dense(64):    64 neurons — continues expanding
Output:       51 neurons — reconstructed input
```

**Activation functions:**
- `relu` (Rectified Linear Unit): `f(x) = max(0, x)` — adds non-linearity; makes the network powerful enough to learn complex patterns
- `linear`: No transformation — used on output layer since we want to reconstruct raw numbers

**Loss function: MSE (Mean Squared Error)**
- `mse = mean((original - reconstructed)²)`
- Measures how different the reconstructed output is from the input
- Lower MSE = better reconstruction

**Optimizer: Adam**
- Automatically adjusts the learning rate during training
- One of the best general-purpose optimizers for neural networks

**Total parameters: 11,907** (a relatively small model — intentional for speed)

---

### Step 6 — Train the Autoencoder

```python
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True
)

history = autoencoder.fit(
    X_train, X_train,           # Input = Output (that's the autoencoder trick!)
    validation_data=(X_val, X_val),
    epochs=50,
    batch_size=256,
    callbacks=[early_stop],
    verbose=1
)
```

**Parameters explained:**

| Parameter | Value | Meaning |
|---|---|---|
| `X_train, X_train` | Same data for input and output | Autoencoder learns to reconstruct its own input |
| `epochs=50` | Max 50 training rounds | One epoch = model sees all training data once |
| `batch_size=256` | 256 rows at a time | Processes 256 rows before updating model weights |
| `callbacks=[early_stop]` | Early stopping enabled | Stop if no improvement |

**EarlyStopping parameters:**
- `monitor='val_loss'` — watch the validation loss
- `patience=5` — stop if val_loss doesn't improve for 5 consecutive epochs
- `restore_best_weights=True` — revert to the best version of the model

**Training output (selected epochs):**
```
Epoch 1:  loss: 0.5692 - val_loss: 0.3141
Epoch 10: loss: 0.0698 - val_loss: 0.0585
Epoch 20: loss: 0.0168 - val_loss: 0.0211
Epoch 34: loss: 0.0108 - val_loss: 0.0160  ← best
...stopped at epoch 45
```
The loss drops sharply at first then levels off — the model is learning.

---

### Step 7 — Calculate Reconstruction Error & Set Threshold

```python
X_val_pred = autoencoder.predict(X_val)
val_loss = np.mean(np.square(X_val - X_val_pred), axis=1)
print("Mean Reconstruction Error:", val_loss.mean())  # → ~0.0139
```

- `autoencoder.predict(X_val)` reconstructs the validation data
- `np.square(X_val - X_val_pred)` squares the difference between original and reconstructed
- `np.mean(..., axis=1)` averages across features → one error score per row

```python
threshold = np.percentile(val_loss, 95)
print("Threshold:", threshold)  # → ~0.0122
```

**Why 95th percentile?**
- Look at the reconstruction errors for all normal traffic
- Set the threshold at the 95th percentile
- Meaning: 95% of normal traffic falls BELOW this threshold
- Any traffic with reconstruction error ABOVE this threshold is flagged as anomalous (attack)
- The 5% of normal traffic that exceeds this threshold will be "false positives" — an acceptable tradeoff

---

### Step 8 — Save Threshold and Model

```python
joblib.dump(threshold, MODEL_PATH + "/ae_threshold.pkl")
autoencoder.save(MODEL_PATH + "/autoencoder.keras")
```

- Saves the threshold value so Notebook 04 can use the exact same cutoff
- Saves the trained autoencoder model

---

### Step 9 — Test on Full Dataset

```python
X_all = scaler.transform(df[feature_cols])
X_pred = autoencoder.predict(X_all)
recon_error = np.mean(np.square(X_all - X_pred), axis=1)
df['AE_Predicted_Label'] = (recon_error > threshold).astype(int)
```

- Scale all 152,389 rows
- Get reconstruction error for every row
- `(recon_error > threshold).astype(int)` → 1 if attack, 0 if normal

---

### Step 10 — Evaluate Results

```python
print(classification_report(df['Attack_label'], df['AE_Predicted_Label']))
```

**Results:**
```
              precision    recall  f1-score   support

           0       1.00      0.95      0.97     24152   ← Normal traffic
           1       0.99      1.00      1.00    128237   ← Attack traffic

    accuracy                           0.99    152389
```

**Confusion Matrix:**
```
[[ 22913   1239]   ← Normal: 22,913 correct, 1,239 false positives
 [     0 128237]]  ← Attacks: ALL 128,237 detected correctly!
```

**Key insight:** The autoencoder catches 100% of attack traffic (zero false negatives), with only 5% false positives on normal traffic — excellent performance!

---

### Notebook 03 Summary

| Input | Output |
|---|---|
| `master_clean.parquet` | `autoencoder.keras` (trained model) |
| `scaler.pkl` | `ae_threshold.pkl` |
| — | `autoencoder_metrics.csv` |

**Key Result: 99% overall accuracy — detects ALL attack traffic including zero-day types!**

---


## 5. Notebook 04 — Fusion Model

**File:** `04_Fusion_Model.ipynb`

**Goal:** Combine LightGBM and the Autoencoder into one smart system that handles both known attacks AND zero-day attacks.

---

### Why Do We Need a Fusion Model?

| Model | Strength | Weakness |
|---|---|---|
| **LightGBM** | Extremely accurate on known attacks (99.99%) | Cannot detect new/unknown attacks |
| **Autoencoder** | Can detect ANY unusual traffic (even zero-day) | Less precise about specific attack types |
| **Fusion** | Best of both — high accuracy + zero-day detection | — |

The fusion model uses a simple but powerful logic:
> **"If LightGBM is very confident the traffic is Normal, trust it. Otherwise, let the Autoencoder decide."**

---

### Step 1 — Load All Models

```python
lgb_model   = joblib.load(MODEL_PATH + "/lightgbm_known.pkl")
autoencoder = tf.keras.models.load_model(MODEL_PATH + "/autoencoder.keras")
threshold   = joblib.load(MODEL_PATH + "/ae_threshold.pkl")
scaler      = joblib.load(MODEL_PATH + "/scaler.pkl")
```

- Loads all 4 saved artifacts from previous notebooks
- This is why saving models properly in earlier notebooks is important!

---

### Step 2 — Build the Test Dataset

```python
full_df   = pd.read_parquet(DATA_PATH + "/master_clean.parquet")
normal_df = full_df[full_df['Attack_label'] == 0]          # Normal traffic only
zero_df   = pd.read_parquet(DATA_PATH + "/zero_day_test.parquet")  # Zero-day attacks

df = pd.concat([normal_df, zero_df], axis=0)
```

**Why this combination?**
- We test the Fusion Model on a realistic scenario:
  - Normal traffic: 24,152 rows
  - Zero-day attacks: 31,096 rows (types the LightGBM has NEVER seen!)
- Total test set: **55,248 rows**

This is the hardest test — can the system detect attacks it was never trained on?

---

### Step 3 — Get LightGBM Predictions

```python
lgb_probs = lgb_model.predict_proba(X)
lgb_pred_class  = np.argmax(lgb_probs, axis=1)
lgb_confidence  = np.max(lgb_probs, axis=1)
```

- `predict_proba(X)` returns probabilities for each class for each row
  - Example: `[0.01, 0.02, 0.91, 0.03, ...]` → 91% confident it's class 2
- `np.argmax(lgb_probs, axis=1)` → the class with the highest probability (predicted class)
- `np.max(lgb_probs, axis=1)` → the actual highest probability value (confidence score)

---

### Step 4 — Get Autoencoder Predictions

```python
X_scaled = scaler.transform(X)
X_recon  = autoencoder.predict(X_scaled)
recon_error = np.mean(np.square(X_scaled - X_recon), axis=1)
ae_pred  = (recon_error > threshold).astype(int)
```

- Same process as Notebook 03
- `ae_pred[i] = 1` if reconstruction error is high (anomaly), `0` if normal

---

### Step 5 — The Fusion Logic

```python
CONF_THRESHOLD = 0.90

final_pred = []

for i in range(len(X)):

    # If LightGBM is VERY confident it's NORMAL (class index 7)
    if lgb_pred_class[i] == 0 and lgb_confidence[i] >= CONF_THRESHOLD:
        final_pred.append(0)   # Normal

    else:
        # Otherwise rely on Autoencoder
        final_pred.append(ae_pred[i])

final_pred = np.array(final_pred)
```

**Decision Logic (plain English):**

```
For each network packet:
  IF LightGBM says "this is Normal traffic" AND is ≥90% confident:
      → Mark as NORMAL (trust LightGBM)
  ELSE:
      → Ask the Autoencoder (use reconstruction error threshold)
```

**Why 90% confidence threshold?**
- LightGBM has never seen zero-day attacks, but it will still try to classify them
- It might classify a zero-day attack as "Normal" with low confidence
- By requiring 90% confidence before trusting LightGBM's "Normal" verdict, we reduce the chance of missing zero-day attacks

**Why defer to the Autoencoder in uncertain cases?**
- The Autoencoder was trained only on normal traffic
- If traffic is at all unusual (even zero-day), it will have high reconstruction error
- So it naturally catches both known and unknown attacks

---

### Step 6 — Evaluation

```python
print(classification_report(y_true, final_pred))
```

**Results:**
```
              precision    recall  f1-score   support

           0       0.98      0.95      0.96     24152   ← Normal
           1       0.96      0.98      0.97     31096   ← Zero-Day Attacks

    accuracy                           0.97     55248
```

**Confusion Matrix:**
```
[[22913  1239]    ← Normal: 22,913 correct | 1,239 false alarms
 [  520 30576]]   ← Attacks: 30,576 caught | only 520 missed
```

**What does this mean?**
- **97% overall accuracy** on a dataset containing zero-day attacks the LightGBM had NEVER seen
- Only 520 zero-day attacks slipped through as "Normal" (1.7% miss rate)
- 1,239 normal packets were flagged as attacks (5.1% false alarm rate)

Compare to the baseline Isolation Forest: only **49% accuracy** on the same task.

---

### Step 7 — Save Results

```python
report = classification_report(y_true, final_pred, output_dict=True)
pd.DataFrame(report).transpose().to_csv(REPORT_PATH + "/fusion_model_metrics.csv")
```

---

### Notebook 04 Summary

| Input | Output |
|---|---|
| `lightgbm_known.pkl` | `fusion_model_metrics.csv` |
| `autoencoder.keras` | — |
| `ae_threshold.pkl` | — |
| `scaler.pkl` | — |
| `master_clean.parquet` + `zero_day_test.parquet` | — |

**Key Result: 97% accuracy detecting zero-day attacks the LightGBM had NEVER seen!**

---

## 6. Notebook 05 — Visualization & Comparison

**File:** `05_Visualization_And_Comparison.ipynb`

**Goal:** Create visual charts comparing all models, and generate the confusion matrix heatmaps seen in the screenshots folder.

---

### Step 1 — Imports

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
```

- `matplotlib.pyplot` — Python's core plotting library
- `seaborn` — built on matplotlib, creates nicer-looking charts with less code

---

### Step 2 — Model Comparison Table

```python
comparison_df = pd.DataFrame({
    "Model": ["Isolation Forest", "LightGBM", "Autoencoder", "Fusion Model"],
    "Accuracy": [0.49, 0.9999, 0.99, 0.97],
    "Purpose": [
        "Baseline Anomaly Detection",
        "Known Attack Classification",
        "Zero-Day Detection",
        "Hybrid Detection System"
    ]
})
```

**Why is Isolation Forest only 49%?**
- Isolation Forest is a classical anomaly detection algorithm
- It was used as a **baseline** — to show how poorly a simple model performs
- 49% is barely better than random guessing (50%)
- This justifies using the more sophisticated Autoencoder approach

---

### Step 3 — Accuracy Bar Chart

```python
plt.figure(figsize=(8, 5))
plt.bar(comparison_df["Model"], comparison_df["Accuracy"])
plt.title("Model Accuracy Comparison")
plt.ylabel("Accuracy")
plt.ylim(0, 1.05)
plt.xticks(rotation=10)
plt.show()
```

- `figsize=(8, 5)` → chart size in inches
- `plt.bar(...)` → creates a bar chart
- `plt.ylim(0, 1.05)` → y-axis goes from 0 to 1.05 (small space above 100%)
- `plt.xticks(rotation=10)` → rotate x-axis labels slightly so they don't overlap

**Output:** Bar chart showing all 4 models' accuracy — clearly shows LightGBM and Autoencoder dominate over Isolation Forest.

---

### Step 4 — Confusion Matrix Heatmap (Fusion Model)

```python
plt.figure(figsize=(6, 4))
sns.heatmap(
    cm_fusion,
    annot=True,
    fmt='d',
    cmap='Blues'
)
plt.title("Fusion Model Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()
```

**Reading a Confusion Matrix:**
```
             Predicted Normal   Predicted Attack
Actual Normal     22913             1239
Actual Attack      520             30576
```

- **Top-left (22913):** True Negatives — normal traffic correctly identified as normal
- **Top-right (1239):** False Positives — normal traffic wrongly flagged as attack
- **Bottom-left (520):** False Negatives — attacks that slipped through as "normal"
- **Bottom-right (30576):** True Positives — attacks correctly detected

`sns.heatmap` with `annot=True` shows the numbers inside the colored cells, making it easy to read.

---

### Step 5 — Performance Metrics Comparison

```python
metrics_df = pd.DataFrame({
    "Model": ["LightGBM", "Autoencoder", "Fusion"],
    "Precision": [...],
    "Recall": [...],
    "F1-Score": [...]
})
```

A grouped bar chart comparing Precision, Recall, and F1-Score across models.

---

### Notebook 05 Summary

| Input | Output |
|---|---|
| Metrics from previous notebooks | Bar charts (saved as PNGs in `/screenshots`) |
| — | Confusion matrix heatmaps |
| — | Performance metric comparison charts |
| — | `model_comparison.csv` |

---

## 7. How All Notebooks Connect

Here's the complete data flow showing how files pass between notebooks:

```
╔══════════════════════════════╗
║   01_Preprocessing           ║
║                              ║
║  CSV → clean → encode        ║
║      ↓           ↓           ║
╚═══════════════════════════════╝
        ↓           ↓
  known_train.parquet     master_clean.parquet
  zero_day_test.parquet   attack_type_mapping.csv
  scaler.pkl

        ↓                       ↓
╔═══════════════╗     ╔═════════════════════╗
║  02_LightGBM  ║     ║  03_Autoencoder     ║
║               ║     ║                     ║
║  Train on     ║     ║  Train on Normal    ║
║  known attacks║     ║  traffic only       ║
║               ║     ║                     ║
╚═══════════════╝     ╚═════════════════════╝
        ↓                       ↓
lightgbm_known.pkl      autoencoder.keras
lightgbm_metrics.csv    ae_threshold.pkl
feature_importance.csv  autoencoder_metrics.csv

        ↓                       ↓
        └──────────┬────────────┘
                   ↓
        ╔═══════════════════════╗
        ║   04_Fusion_Model     ║
        ║                       ║
        ║  LightGBM + AE logic  ║
        ║  Test on Zero-Day data║
        ╚═══════════════════════╝
                   ↓
         fusion_model_metrics.csv

                   ↓
        ╔═══════════════════════╗
        ║  05_Visualization     ║
        ║                       ║
        ║  Charts & Comparison  ║
        ╚═══════════════════════╝
                   ↓
             PNG screenshots
             model_comparison.csv
```

---

## 8. Key Concepts Glossary

| Term | Simple Explanation |
|---|---|
| **IoT** | Internet of Things — everyday devices connected to the internet (cameras, sensors, smart appliances) |
| **Zero-Day Attack** | A brand new attack type that has never been seen before; no existing signature to detect it |
| **DataFrame** | A table of data in Python (like an Excel sheet), provided by the pandas library |
| **Parquet** | A fast, compressed file format for storing large datasets — much better than CSV for ML |
| **StandardScaler** | Normalizes data so all features have mean=0 and std=1; helps neural networks train better |
| **LightGBM** | Microsoft's fast gradient boosting tree algorithm — great for tabular data classification |
| **Decision Tree** | A flowchart-like model that makes decisions by asking a series of yes/no questions |
| **Gradient Boosting** | Building many weak models (trees) in sequence, each fixing the errors of the previous one |
| **Autoencoder** | Neural network that compresses then reconstructs its input — used for anomaly detection |
| **Encoder** | The compression part of an autoencoder (reduces dimensions) |
| **Decoder** | The expansion part of an autoencoder (reconstructs original dimensions) |
| **Bottleneck** | The smallest layer in an autoencoder — forces the network to learn compact representations |
| **Reconstruction Error** | How different the autoencoder's output is from its input — high = anomaly |
| **Threshold** | A cutoff value; above it = attack, below it = normal |
| **95th Percentile** | The value below which 95% of normal traffic reconstruction errors fall |
| **Overfitting** | When a model memorizes training data but fails on new data |
| **Epoch** | One complete pass through the entire training dataset |
| **Batch Size** | Number of rows processed at once before updating model weights |
| **Early Stopping** | Automatically stop training when the model stops improving — prevents overfitting |
| **MSE** | Mean Squared Error — average of squared differences; used as loss function for autoencoder |
| **ReLU** | Rectified Linear Unit activation: f(x) = max(0, x) — adds non-linearity to neural nets |
| **Precision** | Of all predicted positives, how many were actually positive? (avoids false alarms) |
| **Recall** | Of all actual positives, how many were found? (avoids missing attacks) |
| **F1-Score** | Harmonic mean of precision and recall — the balanced overall performance metric |
| **Confusion Matrix** | A 2×2 table showing true positives, false positives, true negatives, false negatives |
| **Stratify** | Ensure train/test split has same class proportions as the original dataset |
| **joblib** | Python library for saving/loading large Python objects (models, scalers) efficiently |
| **predict_proba** | Returns probability scores for each class (instead of just the winning class) |
| **Fusion Model** | A hybrid system combining multiple models — uses each model's strengths |
| **Anomaly Detection** | Finding data points that don't follow the normal pattern |

---

## Final Results Summary

| Model | Accuracy | Task |
|---|---|---|
| Isolation Forest (baseline) | 49% | Anomaly detection (simple) |
| LightGBM | 99.99% | Classify 10 known attack types |
| Autoencoder | 99% | Detect ALL anomalies (including zero-day) |
| **Fusion Model** | **97%** | **Detect zero-day attacks never seen before** |

### Why 97% is actually the most impressive result:

The Fusion Model achieves 97% accuracy on the **hardest possible test** — detecting 5 types of attacks that the LightGBM component had **never seen during training**. This demonstrates the system's ability to generalize to truly novel threats, which is the core challenge in real-world cybersecurity.

---

*Document generated from the Zero-Day IoT Attack Detection Project notebooks.*
*For questions, refer to the individual notebook files in the `/notebooks` folder.*
