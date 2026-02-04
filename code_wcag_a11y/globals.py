from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMADB_WCAG_PATH = DATA_DIR / "wcag_local_index"
COLLECTION_NAME = "wcag_rules"
