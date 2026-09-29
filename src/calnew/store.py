"""Relational provenance plus immutable, content-addressed Parquet snapshots."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .io import digest, write_json
from .schema import Evidence, Molecule, Observation, Stimulus


class EvidenceStore:
    def __init__(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS molecules (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, source_id TEXT NOT NULL, experiment_id TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stimuli (id TEXT PRIMARY KEY, molecule_id TEXT NOT NULL REFERENCES molecules(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, molecule_id TEXT NOT NULL REFERENCES molecules(id), stimulus_id TEXT NOT NULL REFERENCES stimuli(id), evidence_id TEXT NOT NULL REFERENCES evidence(id), source_id TEXT NOT NULL, endpoint TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS observation_endpoint ON observations(endpoint,source_id);
        CREATE INDEX IF NOT EXISTS experiment_lineage ON evidence(experiment_id);
        """)

    def close(self):
        self.db.close()

    def add(self, record):
        payload = record.model_dump_json()
        if isinstance(record, Molecule):
            table, key, values = "molecules", record.molecule_id, (record.molecule_id, payload)
        elif isinstance(record, Evidence):
            table, key, values = "evidence", record.evidence_id, (record.evidence_id, record.source_id, record.original_experiment_id, payload)
        elif isinstance(record, Stimulus):
            table, key, values = "stimuli", record.stimulus_id, (record.stimulus_id, record.molecule_id, payload)
        elif isinstance(record, Observation):
            table, key, values = "observations", record.observation_id, (record.observation_id, record.molecule_id, record.stimulus_id, record.evidence_id, record.source_id, record.endpoint.value, payload)
        else:
            raise TypeError(type(record))
        prior = self.db.execute(f"SELECT payload FROM {table} WHERE id=?", (key,)).fetchone()
        if prior:
            if table == "molecules":
                if json.loads(prior[0])["smiles"] != record.smiles:
                    raise ValueError("Molecular identifier collision")
                return False  # Source-specific identity remains in evidence metadata.
            if json.loads(prior[0]) != json.loads(payload):
                raise ValueError(f"Refusing to overwrite immutable {table} record {key}")
            return False
        self.db.execute(f"INSERT INTO {table} VALUES ({','.join('?' for _ in values)})", values)
        return True

    def frame(self, table: str) -> pd.DataFrame:
        if table not in {"molecules", "evidence", "stimuli", "observations"}:
            raise ValueError("Unknown evidence table")
        return pd.DataFrame([json.loads(row[0]) for row in self.db.execute(f"SELECT payload FROM {table} ORDER BY id")])

    def snapshot(self, destination: Path, source_manifests: dict) -> Path:
        tables = {name: self.frame(name) for name in ("molecules", "evidence", "stimuli", "observations")}
        hashes = {k: digest(v.to_dict("records")) for k, v in tables.items()}
        identity = digest({"schema": 1, "tables": hashes, "sources": source_manifests})
        root = Path(destination) / identity[:16]
        if (root / "manifest.json").exists():
            return root
        root.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            # Serialise metadata as JSON strings to support empty/heterogeneous dicts in Parquet.
            frame = frame.copy()
            for col in frame.columns:
                if frame[col].map(lambda x: isinstance(x, dict)).any():
                    frame[col] = frame[col].map(lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else x)
            frame.to_parquet(root / f"{name}.parquet", index=False)
        write_json(root / "manifest.json", {"schema_version": 1, "snapshot_id": identity, "table_hashes": hashes,
                                            "counts": {k: len(v) for k, v in tables.items()}, "sources": source_manifests})
        return root
