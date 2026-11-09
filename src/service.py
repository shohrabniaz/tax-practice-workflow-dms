from __future__ import annotations
from pathlib import Path
from .engine import Store, seed

def build_service(data_dir: Path, out_dir: Path) -> Store:
    store = Store(out_dir / 'records.json')
    seed_path = data_dir / 'seed_records.json'
    if seed_path.exists():
        seed(store, seed_path)
    return store
