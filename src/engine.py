from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from uuid import uuid4

@dataclass
class Record:
    id: str
    title: str
    status: str = "open"
    meta: dict = field(default_factory=dict)

class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: list[dict]) -> None:
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def list(self) -> list[dict]:
        return self._read()

    def add(self, title: str, status: str = "open", **meta) -> dict:
        rows = self._read()
        rec = asdict(Record(id=str(uuid4())[:8], title=title, status=status, meta=meta))
        rows.append(rec)
        self._write(rows)
        return rec

    def set_status(self, rec_id: str, status: str) -> dict | None:
        rows = self._read()
        for r in rows:
            if r["id"] == rec_id:
                r["status"] = status
                self._write(rows)
                return r
        return None

    def summary(self) -> dict:
        rows = self._read()
        by: dict[str, int] = {}
        for r in rows:
            by[r["status"]] = by.get(r["status"], 0) + 1
        return {"total": len(rows), "by_status": by, "records": rows}

def seed(store: Store, seed_path: Path) -> None:
    if store.list():
        return
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))
    for s in seeds:
        store.add(s["title"], s.get("status", "open"), **s.get("meta", {}))

def run(data_dir: Path, out_dir: Path) -> dict:
    store = Store(out_dir / "records.json")
    seed(store, data_dir / "seed_records.json")
    rows = store.list()
    if rows:
        store.set_status(rows[0]["id"], "in_progress")
        if len(rows) > 1:
            store.set_status(rows[1]["id"], "done")
    summary = store.summary()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "service_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
