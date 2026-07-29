"""
Fraud Detection Pipeline with MinIO Integration
Handles data validation, cleaning, feature engineering, and model training.
Data is exchanged between Airflow tasks via MinIO object storage.
"""
import logging
import os
import tempfile
from pathlib import Path

import boto3
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from datetime import datetime
# --------------------------------------------------------------------------- #
# Logging Configuration
# --------------------------------------------------------------------------- #
class ColorFormatter(logging.Formatter):
    """Enhanced formatter with ANSI colors for console output."""
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def setup_logger() -> logging.Logger:
    """Configure logger with both console and file handlers."""
    log = logging.getLogger("FraudDetector")
    log.setLevel(logging.DEBUG)

    if not log.handlers:
        # Console handler with colors
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            ColorFormatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        # File handler for errors
        log_dir = Path("/opt/airflow/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / "fraud_pipeline.log", mode="a", encoding="utf-8"
        )
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        log.addHandler(console)
        log.addHandler(file_handler)

    return log


logger = setup_logger()

# --------------------------------------------------------------------------- #
# Constants and Configuration
# --------------------------------------------------------------------------- #
# Data path inside Docker container
PATH_DATA_FRAUD = os.getenv("DATA_PATH", "/opt/airflow/data/fraudTrain.csv")

# Columns to exclude from modeling
COLUMNS_TO_DROP = [
    "Unnamed: 0", "cc_num", "first", "last", "street",
    "zip", "trans_num", "unix_time", "city",
]

# Feature specifications
CATEGORICAL_FEATURES = ["category", "merchant", "state", "gender", "job"]
NUMERIC_FEATURES = [
    "amt", "city_pop", "age", "distance_km",
    "hour", "day_of_week", "month",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


# --------------------------------------------------------------------------- #
# Feature Engineering
# --------------------------------------------------------------------------- #
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (np.sin(dlat / 2) ** 2 +
         np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2)
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features from raw transaction data.
    Creates temporal features and distance calculation.
    """
    df = df.copy()

    # Parse datetime columns
    df["trans_date_trans_time"] = pd.to_datetime(
        df["trans_date_trans_time"], errors="coerce"
    )
    df["dob"] = pd.to_datetime(df["dob"], errors="coerce")

    # Temporal features
    df["hour"] = df["trans_date_trans_time"].dt.hour
    df["day_of_week"] = df["trans_date_trans_time"].dt.dayofweek
    df["month"] = df["trans_date_trans_time"].dt.month

    # Customer age at transaction time
    df["age"] = (
            (df["trans_date_trans_time"] - df["dob"]).dt.days // 365
    ).astype("float")

    # Distance between customer and merchant (key fraud indicator)
    df["distance_km"] = haversine_km(
        df["lat"], df["long"], df["merch_lat"], df["merch_long"]
    )

    return df[FEATURE_COLUMNS]


# --------------------------------------------------------------------------- #
# Fraud Detection Pipeline Class
# --------------------------------------------------------------------------- #
class FraudDetectionSupervised:
    """
    Orchestrates the fraud detection ML pipeline.
    Uses MinIO for data persistence between Airflow tasks.
    """

    def __init__(self, path_data: str = PATH_DATA_FRAUD):
        self.pathData = path_data

        # MinIO configuration from environment
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.minio_user = os.getenv("MINIO_ROOT_USER", "admin")
        self.minio_password = os.getenv("MINIO_ROOT_PASSWORD", "adminadminadmin")
        self.bucket = os.getenv("MINIO_BUCKET", "my-bucket")

        # Initialize MinIO client
        logger.info(f"Connecting to MinIO at {self.minio_endpoint}")
        self.s3 = boto3.client(
            "s3",
            endpoint_url=self.minio_endpoint,
            aws_access_key_id=self.minio_user,
            aws_secret_access_key=self.minio_password,
            region_name="us-east-1",  # MinIO doesn't require but boto3 does
        )

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create MinIO bucket if it doesn't exist."""
        try:
            buckets = [b["Name"] for b in self.s3.list_buckets()["Buckets"]]
            if self.bucket not in buckets:
                self.s3.create_bucket(Bucket=self.bucket)
                logger.info(f"Bucket '{self.bucket}' created")
            else:
                logger.info(f"Bucket '{self.bucket}' already exists")
        except Exception as e:
            logger.warning(f"Could not verify/create bucket: {e}")
            logger.warning("Continuing - bucket might already exist")

    def _upload_to_minio(self, local_path: str, s3_key: str):
        """Upload file to MinIO."""
        try:
            self.s3.upload_file(local_path, self.bucket, s3_key)
            logger.info(f"Uploaded {local_path} -> s3://{self.bucket}/{s3_key}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

    def _download_from_minio(self, s3_key: str, local_path: str):
        """Download file from MinIO."""
        try:
            self.s3.download_file(self.bucket, s3_key, local_path)
            logger.info(f"Downloaded s3://{self.bucket}/{s3_key} -> {local_path}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise

    # ------------------------------------------------------------------ #
    # Airflow Task Methods
    # ------------------------------------------------------------------ #
    def checkData(self, **context) -> bool:
        """
        Task 1: Validate raw dataset.
        Verifies file existence and basic data integrity.
        """
        logger.info("=" * 60)
        logger.info("TASK 1: Data Validation")
        logger.info("=" * 60)

        data_path = Path(self.pathData)

        if not data_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.pathData}")

        # Quick sanity check
        df = pd.read_csv(self.pathData, nrows=10)

        if df.empty:
            raise ValueError("Dataset is empty or corrupted")

        logger.info(f"Data file size: {data_path.stat().st_size / (1024 * 1024):.2f} MB")
        logger.info(f"Columns found: {df.columns.tolist()}")
        logger.info(f"Sample rows: {len(df)}")

        return True

    def cleanData(self, **context) -> str:
        """
        Task 2: Clean data, engineer features, upload to MinIO.
        Returns the S3 key for downstream tasks.
        """
        logger.info("=" * 60)
        logger.info("TASK 2: Data Cleaning & Feature Engineering")
        logger.info("=" * 60)

        # Load raw data
        logger.info(f"Loading data from {self.pathData}")
        raw = pd.read_csv(self.pathData)
        logger.info(f"Raw dataset shape: {raw.shape}")

        # Remove unnecessary columns
        df = raw.drop(columns=COLUMNS_TO_DROP, errors="ignore")

        # Parse dates
        df["trans_date_trans_time"] = pd.to_datetime(
            df["trans_date_trans_time"], errors="coerce"
        )
        df["dob"] = pd.to_datetime(df["dob"], errors="coerce")

        # Feature engineering
        features = prepare_features(df)
        features["is_fraud"] = df["is_fraud"].values

        # Remove rows with missing values
        initial_rows = len(features)
        features.dropna(subset=FEATURE_COLUMNS + ["is_fraud"], inplace=True)
        features.reset_index(drop=True, inplace=True)

        dropped_rows = initial_rows - len(features)
        logger.info(f"Cleaned dataset shape: {features.shape}")
        logger.info(f"Dropped {dropped_rows} rows with missing values")

        # Class distribution
        fraud_count = features["is_fraud"].sum()
        total = len(features)
        logger.info(f"Fraudulent transactions: {fraud_count} ({fraud_count / total:.2%})")
        logger.info(f"Legitimate transactions: {total - fraud_count} ({(total - fraud_count) / total:.2%})")

        # Save to temporary Parquet file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            local_parquet = tmp.name
        features.to_parquet(local_parquet, index=False)
        logger.info(f"Saved cleaned data to temporary file: {local_parquet}")

        # Upload to MinIO
        ts = context.get("ts_nodash", datetime.now().strftime("%Y%m%d%H%M%S"))
        s3_key = f"cleaned/fraud_cleaned_{ts}.parquet"
        self._upload_to_minio(local_parquet, s3_key)

        # Clean up temporary file
        Path(local_parquet).unlink()

        # Pass S3 key to next task via XCom
        context["ti"].xcom_push(key="cleaned_data_s3_key", value=s3_key)

        logger.info(f"Cleaned data uploaded to MinIO: {s3_key}")
        return s3_key

    def training(self, **context) -> float:
        """
        Task 3: Train model using cleaned data from MinIO.
        Downloads data, trains RandomForest, uploads model artifact.
        """
        logger.info("=" * 60)
        logger.info("TASK 3: Model Training")
        logger.info("=" * 60)

        # Retrieve S3 key from previous task
        ti = context["ti"]
        s3_key = ti.xcom_pull(
            task_ids="clean_data_task",
            key="cleaned_data_s3_key"
        )

        if not s3_key:
            raise ValueError("No cleaned data S3 key found in XCom. Did clean_data_task succeed?")

        logger.info(f"Fetching cleaned data from MinIO: {s3_key}")

        # Download cleaned data
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            local_data = tmp.name
        self._download_from_minio(s3_key, local_data)

        # Load data
        features = pd.read_parquet(local_data)
        Path(local_data).unlink()  # Clean up temp file

        X = features[FEATURE_COLUMNS]
        y = features["is_fraud"]

        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Fraud rate: {y.mean():.2%}")

        # Build preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ), CATEGORICAL_FEATURES),
                ("num", StandardScaler(), NUMERIC_FEATURES),
            ]
        )

        # Create full pipeline
        model = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=30,

                max_depth=6,
                min_samples_split=50,
                min_samples_leaf=25,
                class_weight="balanced",
                random_state=42,
                n_jobs=2,
                verbose=1
            )),
        ])

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")

        # Train model
        logger.info("Training RandomForest classifier...")
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"Model Accuracy: {accuracy:.4f}")
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(y_test, y_pred))

        # Save model artifact
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            model_local = tmp.name
        joblib.dump(model, model_local)

        # Upload model to MinIO
        ts = context.get("ts_nodash", datetime.now().strftime("%Y%m%d%H%M%S"))
        model_s3_key = f"models/fraud_rf_{ts}.joblib"
        self._upload_to_minio(model_local, model_s3_key)

        # Clean up
        Path(model_local).unlink()

        # Pass model location to downstream tasks
        ti.xcom_push(key="model_s3_key", value=model_s3_key)
        ti.xcom_push(key="model_accuracy", value=accuracy)

        logger.info(f"Model saved to MinIO: {model_s3_key}")
        logger.info(f"Training completed successfully with accuracy: {accuracy:.4f}")

        return accuracy


# --------------------------------------------------------------------------- #
# Local testing
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    """For local development and testing outside Airflow."""
    logger.info("Running in local/test mode")

    pipeline = FraudDetectionSupervised()

    # Simulate Airflow context
    fake_context = {
        "ts_nodash": "local_test",
        "ti": type('obj', (object,), {
            'xcom_push': lambda *args, **kwargs: None,
            'xcom_pull': lambda *args, **kwargs: "cleaned/fraud_cleaned_local_test.parquet"
        })()
    }

    # Test individual steps
    try:
        pipeline.checkData()
        pipeline.cleanData(**fake_context)
        pipeline.training(**fake_context)
        logger.info("Local test completed successfully!")
    except Exception as e:
        logger.error(f"Local test failed: {e}")
        raise