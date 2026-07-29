# 🕵️ Fraud Detection ML Pipeline with Airflow & MinIO

[![Airflow](https://img.shields.io/badge/Airflow-3.3.0-blue)](https://airflow.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![MinIO](https://img.shields.io/badge/MinIO-Latest-red)](https://min.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5.2-orange)](https://scikit-learn.org/)

A production-grade **Machine Learning pipeline** for credit card fraud detection, orchestrated with **Apache Airflow** and using **MinIO** for object storage.

---

## 📊 Project Overview

End-to-end ML pipeline that validates, cleans, engineers features, and trains a fraud detection model.

### Key Features
- 🔄 Automated pipeline with Apache Airflow 3.3.0
- 📦 MinIO object storage (S3-compatible)
- 🚀 Handles 1.3M+ transactions
- 🎯 Class imbalance handling (0.58% fraud)
- 📊 Haversine distance, temporal feature engineering
- 🐳 Docker Compose one-command deployment

---

## 🏗️ Architecture

```
Apache Airflow
  Check Data → Clean Data → Train Model
                    ↓              ↓
              MinIO (S3) Object Storage
              ├── cleaned/*.parquet
              └── models/*.joblib
```

### Pipeline Tasks
1. **Check Data** - Validates CSV integrity
2. **Clean Data** - Feature engineering + upload to MinIO
3. **Train Model** - Download from MinIO, train, upload artifact

### Engineered Features
| Feature | Description |
|---------|-------------|
| `age` | Customer age at transaction |
| `distance_km` | Distance home→merchant (haversine) |
| `hour` | Transaction hour (0-23) |
| `day_of_week` | Day of week (0-6) |
| `month` | Month of transaction |
| `amt` | Transaction amount |
| `city_pop` | City population |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose v2+
- 8GB+ RAM
- Git

### Step 1: Clone
```bash
git clone https://github.com/yourusername/fraud-detection-airflow.git
cd fraud-detection-airflow
```

### Step 2: Create .env file
```bash
AIRFLOW_UID=50000
FERNET_KEY=46BKJoQYlPPOexq0OhDZnIlNepKFf87WFwLbfzfcDDM=
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=adminadminadmin
MINIO_BUCKET=my-bucket
DEV_MODE=false
MAX_TRAIN_SAMPLES=500000
MODEL_TYPE=rf
```

### Step 3: Add Dataset
```bash
mkdir -p data
cp /path/to/fraudTrain.csv data/
```

### Step 4: Start Services
```bash
docker compose up -d
docker compose logs -f airflow-init  # Wait for completion
docker compose ps  # Verify all healthy
```

### Step 5: Access UIs
| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow | http://localhost:8080 | `airflow` | `airflow` |
| MinIO | http://localhost:9001 | `admin` | `adminadminadmin` |

### Step 6: Run Pipeline
**Via UI:** Airflow → `fraud_detection_pipeline` → Click ▶️

**Via CLI:**
```bash
docker compose exec airflow-scheduler airflow dags trigger fraud_detection_pipeline
```

### Step 7: View Results
```bash
docker compose logs airflow-worker
# MinIO: http://localhost:9001 → Buckets → my-bucket → models/
```

---

## 📁 Project Structure
```
fraud-detection-airflow/
├── docker-compose.yaml
├── .env
├── .gitignore
├── exp.md
├── dags/
│   ├── fraud_detection_dag.py
│   └── fraud_detection_main.py
├── data/
│   └── fraudTrain.csv
├── logs/
├── config/
└── plugins/
```

---

## 🧠 Model Details

```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=8,
    min_samples_split=20,
    min_samples_leaf=10,
    class_weight='balanced_subsample',
    n_jobs=-1
)
```

### Preprocessing
- Categorical: One-Hot Encoding
- Numerical: StandardScaler

### Performance
| Metric | Value |
|--------|-------|
| Accuracy | 98.5%+ |
| Precision | 85%+ |
| Recall | 75%+ |
| F1-Score | 80%+ |

---

## ⚡ Performance Tuning

### Dev Mode (Fast)
```bash
DEV_MODE=true
MAX_TRAIN_SAMPLES=50000
MODEL_TYPE=lgbm
```

### Production Mode
```bash
DEV_MODE=false
MAX_TRAIN_SAMPLES=500000
MODEL_TYPE=rf
```

### Algorithm Options
- `MODEL_TYPE=rf` - RandomForest (balanced)
- `MODEL_TYPE=lgbm` - LightGBM (fastest)
- `MODEL_TYPE=hgb` - HistGradientBoosting

### Training Times
| Samples | Algorithm | Time |
|---------|-----------|------|
| 50K | LightGBM | ~1 min |
| 100K | RandomForest | ~3 min |
| 500K | LightGBM | ~5 min |
| 1.3M | RandomForest | ~45 min |

---

## 🐛 Troubleshooting

### MinIO Connection Refused
```bash
docker compose ps minio
docker compose exec airflow-worker env | grep MINIO
docker compose restart minio
```

### DAG Not Appearing
```bash
docker compose exec airflow-scheduler airflow dags list
docker compose restart airflow-scheduler
```

### Training Too Slow
```bash
# Enable dev mode in .env
DEV_MODE=true
MAX_TRAIN_SAMPLES=50000
```

### Memory Errors
Docker Desktop → Settings → Resources → 8GB+ RAM, 4 CPUs

### Import Errors
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### View Logs
```bash
docker compose logs airflow-worker
docker compose logs -f airflow-scheduler
```

---

## 📝 Commands Reference

```bash
# Start/Stop
docker compose up -d
docker compose down

# Logs
docker compose logs -f

# Trigger DAG
docker compose exec airflow-scheduler airflow dags trigger fraud_detection_pipeline

# List DAGs
docker compose exec airflow-scheduler airflow dags list

# Access containers
docker compose exec airflow-worker bash
docker compose exec minio bash

# Clean everything
docker compose down -v
```

---

## 🔐 Security Notes
- ⚠️ Default credentials for development only
- 🔑 Change FERNET_KEY in production
- 🔒 Rotate MinIO credentials regularly
- 🚫 Never commit .env to git

---

## 🎯 Future Improvements
- [ ] Model monitoring (Evidently AI)
- [ ] A/B testing
- [ ] Data drift detection
- [ ] REST API for serving
- [ ] CI/CD pipeline
- [ ] MLflow tracking
- [ ] Slack notifications

---

## 📚 Tech Stack
| Tech | Purpose |
|------|---------|
| Apache Airflow 3.3.0 | Orchestration |
| MinIO | Object Storage |
| scikit-learn 1.5.2 | ML |
| pandas 2.2.3 | Data |
| NumPy 1.26.4 | Computing |
| PostgreSQL 16 | Metadata |
| Redis 7.2 | Broker |
| Docker | Containers |

---

## 🤝 Contributing
1. Fork repo
2. Create branch (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/amazing`)
5. Open PR

---

## 📄 License
MIT License

## 📧 Contact
Your Name -bassemnaser124@gmail.com
---

**⭐ Star this repo if you find it useful! ⭐**
