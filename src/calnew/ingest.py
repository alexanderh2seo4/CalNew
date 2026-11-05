"""Pinned data acquisition and explicit, source-specific ingestion adapters."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .chemistry import identify
from .io import digest, file_digest, read_json, write_json
from .schema import Endpoint, Evidence, Observation, Stimulus
from .store import EvidenceStore
from .units import inverse_log_ppm_to_log_ppbv


def download(url: str, destination: Path, expected_sha256: str | None = None) -> dict:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        temp = destination.with_suffix(destination.suffix + ".partial")
        try:
            with requests.get(url, stream=True, timeout=(15, 120)) as response:
                response.raise_for_status()
                with temp.open("wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        handle.write(chunk)
            if expected_sha256 and file_digest(temp) != expected_sha256:
                raise ValueError("Downloaded content checksum mismatch")
            temp.replace(destination)
        finally:
            temp.unlink(missing_ok=True)
    sha = file_digest(destination)
    if expected_sha256 and sha != expected_sha256:
        raise ValueError("Cached content checksum mismatch")
    return {"url": url, "sha256": sha, "bytes": destination.stat().st_size}


def fetch_source(registry_path: Path, source_id: str, data_root: Path) -> Path:
    registry = read_json(registry_path)
    source = registry["sources"][source_id]
    if source["kind"] != "pyrfume":
        raise ValueError("This source uses document/reviewed-record ingestion; see the source registry")
    revision = registry["pyrfume_revision"]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Pyrfume revision must be an immutable 40-character commit")
    root = Path(data_root) / "raw" / source_id / revision
    manifest_path = root / "download.json"
    previous = read_json(manifest_path) if manifest_path.exists() else {}
    files = {}
    for name in source["files"]:
        if Path(name).name != name:
            raise ValueError("Invalid source filename")
        url = f"https://raw.githubusercontent.com/pyrfume/pyrfume-data/{revision}/{source_id}/{name}"
        files[name] = download(url, root / name, previous.get("files", {}).get(name, {}).get("sha256"))
    manifest = {"source_id": source_id, "revision": revision, "registry_entry": source, "files": files}
    write_json(manifest_path, manifest)
    return root


def _cid(value) -> str:
    return str(int(float(value)))


def ingest_source(raw_root: Path, store: EvidenceStore) -> dict:
    manifest = read_json(Path(raw_root) / "download.json")
    source = manifest["registry_entry"]
    sid = manifest["source_id"]
    if source.get("permitted_use") not in ("research_only", "research_source_terms", "open"):
        raise ValueError(f"Source {sid} excluded: permitted use is {source.get('permitted_use')}; record verified terms in the registry before ingestion")
    for name, info in manifest["files"].items():
        if file_digest(Path(raw_root) / name) != info["sha256"]:
            raise ValueError(f"Raw source changed: {name}")
    molecules = pd.read_csv(Path(raw_root) / "molecules.csv")
    smiles_col = "IsomericSMILES" if "IsomericSMILES" in molecules else "CanonicalSMILES"
    mapping, rejected = {}, []
    for _, row in molecules.iterrows():
        try:
            molecule = identify(row[smiles_col])
            store.add(molecule)
            mapping[_cid(row["CID"])] = molecule
        except (ValueError, TypeError) as exc:
            rejected.append({"cid": str(row["CID"]), "reason": str(exc)})
    store.db.commit()
    if source["adapter"] == "ravia":
        return _ingest_ravia(Path(raw_root), store, manifest, mapping, rejected)
    stimulus_table = pd.read_csv(Path(raw_root) / "stimuli.csv")
    stimuli, unresolved_stimuli = {}, []
    for _, row in stimulus_table.iterrows():
        key = str(row["Stimulus"])
        if source["adapter"] != "catalogue_sparse":
            key = _cid(row["Stimulus"])
        try:
            cid = _cid(row["CID"] if "CID" in row else row["CIDs"])
        except (ValueError, TypeError):
            # Upstream occasionally stores a CAS number in the CID column; keep it out rather than guess.
            unresolved_stimuli.append({"stimulus": key, "identifier": str(row.get("CID", row.get("CIDs")))})
            continue
        if cid not in mapping:
            continue
        m = mapping[cid]
        is_keller = source["adapter"] == "keller"
        stimulus = Stimulus(stimulus_id=f"{sid}:{key}", molecule_id=m.molecule_id, source_id=sid,
                            matrix="paraffin_oil" if is_keller else ("air" if sid == "abraham_2012" else "unknown"),
                            solvent=str(row["Solvent"]) if is_keller else None,
                            nominal_concentration=float(row["Concentration"]) if is_keller else None,
                            concentration_unit="solution_fraction" if is_keller else None,
                            concentration_basis="reported_solution_dilution_not_gas" if is_keller else None,
                            metadata={"upstream_stimulus": key, "cid": cid})
        store.add(stimulus)
        stimuli[key] = stimulus
    store.db.commit()
    count, skipped = 0, 0
    behavior_path = Path(raw_root) / "behavior.csv"
    adapter = source["adapter"]
    for chunk in pd.read_csv(behavior_path, chunksize=20000, dtype=str):
        for row_number, row in chunk.iterrows():
            key = str(row["Stimulus"]) if adapter == "catalogue_sparse" else _cid(row["Stimulus"])
            if key not in stimuli:
                skipped += 1
                continue
            stimulus = stimuli[key]
            evid = f"{sid}:{manifest['revision'][:12]}:row:{row_number+2}"
            aggregate = adapter == "abraham" and float(row.get("Duplicates", 0)) > 0
            evidence = Evidence(evidence_id=evid, source_id=sid, source_url=manifest["files"]["behavior.csv"]["url"],
                                source_sha256=manifest["files"]["behavior.csv"]["sha256"], doi=source.get("doi"),
                                original_experiment_id=f"{sid}:compiled:{key}" if adapter == "abraham" else f"{sid}:row:{row_number+2}",
                                location=f"behavior.csv row {row_number+2}", review_status="upstream_curated",
                                permitted_use=source["permitted_use"], is_aggregate=aggregate,
                                metadata={"upstream_row": {k: (None if pd.isna(v) else v) for k,v in row.items()}})
            store.add(evidence)
            common = dict(molecule_id=stimulus.molecule_id, stimulus_id=stimulus.stimulus_id, evidence_id=evid, source_id=sid)
            observations = []
            if adapter == "catalogue_wide":
                for label, val in row.items():
                    if label == "Stimulus" or pd.isna(val):
                        continue
                    numeric = float(val)
                    if numeric not in (0, 1):
                        raise ValueError(f"Unexpected binary catalogue value: {val}")
                    observations.append(Observation(**common, observation_id=evid+":"+label, endpoint=Endpoint.CATALOGUE,
                                                    descriptor=label, raw_value=val, value=numeric, unit="annotation",
                                                    label_state="observed" if numeric else "not_reported"))
            elif adapter == "catalogue_sparse":
                # Only observed labels; no invented source-wide negative vocabulary.
                for label in str(row["Descriptors"]).split(";"):
                    observations.append(Observation(**common, observation_id=evid+":"+label, endpoint=Endpoint.CATALOGUE,
                                                    descriptor=label.strip(), raw_value=label, value=1, unit="annotation"))
            elif adapter == "abraham":
                raw = row["Log (1/ODT)"]
                observations.append(Observation(**common, observation_id=evid, endpoint=Endpoint.AIR, raw_value=raw,
                                                raw_unit="log10(1/ODT[ppmv])", value=inverse_log_ppm_to_log_ppbv(float(raw)),
                                                unit="log10(ppbv)", method="heterogeneous_compilation",
                                                value_origin="upstream_aggregate" if aggregate else "measured",
                                                metadata={"upstream_duplicates": int(float(row.get("Duplicates", 0))),
                                                          "method_indicators_are_aggregated": aggregate,
                                                          "original_experiment_lineage": "not_resolved_in_processed_table"}))
            elif adapter == "keller":
                label, raw = row["MeasurementValue"], row["Value"]
                if pd.isna(raw):
                    continue
                endpoint = {"HOW STRONG IS THE SMELL?": Endpoint.INTENSITY,
                            "HOW PLEASANT IS THE SMELL?": Endpoint.PLEASANTNESS}.get(label, Endpoint.PANEL)
                try:
                    val = float(raw)
                except ValueError:
                    continue  # Free text stays in raw/evidence, not a numerical response.
                observations.append(Observation(**common, observation_id=evid, endpoint=endpoint,
                                                descriptor=label.lower() if endpoint == Endpoint.PANEL else None,
                                                raw_value=raw, value=val, unit="rating_0_100", subject_id=f"{sid}:{row['Subject']}",
                                                method="solution_presentation", metadata={"missing_ratings_are_not_zero": True}))
            else:
                raise ValueError(f"Unsupported adapter {adapter}")
            for observation in observations:
                count += int(store.add(observation))
        store.db.commit()
    report = {"source": sid, "new_observations": count, "molecules_resolved": len(mapping), "rejected_molecules": rejected,
              "unresolved_stimuli": unresolved_stimuli, "unresolved_behavior_rows": skipped, "source_manifest": manifest}
    write_json(Path(raw_root) / "ingestion-report.json", report)
    return report


def _ravia_fraction(label) -> tuple[float | None, str]:
    text = "" if pd.isna(label) else str(label).strip()
    if text.endswith("%"):
        return float(text[:-1]) / 100, "reported_dilution_percent"
    if text.lower() == "solid":
        return None, "solid_undiluted"
    return None, "unreported"


def _ingest_ravia(raw_root: Path, store: EvidenceStore, manifest: dict, mapping: dict, rejected: list) -> dict:
    """Ravia et al. 2020: published group-mean intensity per mono-molecule stimulus and dilution.

    Only mono-molecule rows are ingested; mixtures stay in the raw files. Values are upstream
    aggregates (no per-subject ratings are distributed in the processed files).
    """
    sid, source = manifest["source_id"], manifest["registry_entry"]
    stimuli = pd.read_csv(raw_root / "stimuli.csv", dtype=str).set_index("Stimulus")
    behavior = pd.read_csv(raw_root / "behavior_1.csv", dtype=str)
    url, sha = manifest["files"]["behavior_1.csv"]["url"], manifest["files"]["behavior_1.csv"]["sha256"]
    count, skipped = 0, []
    for row_number, row in behavior.iterrows():
        key, dilution_index, raw = str(row["Stimulus"]), str(row["Dilution #"]), row["Intensity"]
        if pd.isna(raw):
            continue
        info = stimuli.loc[key]
        if info["Type"] != "mono-molecule":
            continue
        try:
            cid = _cid(info["CID"])
        except (ValueError, TypeError):
            skipped.append({"stimulus": key, "reason": f"unparseable CID {info['CID']}"})
            continue
        if cid not in mapping:
            skipped.append({"stimulus": key, "reason": f"CID {cid} not resolved to a structure"})
            continue
        molecule = mapping[cid]
        fraction, basis = _ravia_fraction(info.get(f"Dilution{dilution_index}"))
        stimulus = Stimulus(stimulus_id=f"{sid}:{key}:d{dilution_index}", molecule_id=molecule.molecule_id, source_id=sid,
                            nominal_concentration=fraction, concentration_unit="solution_fraction" if fraction is not None else None,
                            concentration_basis=basis, metadata={"upstream_stimulus": key, "cid": cid, "experiment": info["Experiment"],
                                                                 "dilution_label": info.get(f"Dilution{dilution_index}")})
        store.add(stimulus)
        evid = f"{sid}:{manifest['revision'][:12]}:behavior_1:row:{row_number + 2}"
        store.add(Evidence(evidence_id=evid, source_id=sid, source_url=url, source_sha256=sha, doi=source.get("doi"),
                           original_experiment_id=f"{sid}:{info['Experiment']}:{key}:d{dilution_index}", location=f"behavior_1.csv row {row_number + 2}",
                           review_status="upstream_curated", permitted_use=source["permitted_use"], is_aggregate=True,
                           metadata={"upstream_row": {k: (None if pd.isna(v) else v) for k, v in row.items()}}))
        count += int(store.add(Observation(observation_id=evid, molecule_id=molecule.molecule_id, stimulus_id=stimulus.stimulus_id,
                                           evidence_id=evid, source_id=sid, endpoint=Endpoint.INTENSITY, raw_value=str(raw),
                                           value=float(raw), unit="rating_0_100", method="solution_presentation_group_mean",
                                           value_origin="upstream_aggregate", metadata={"per_subject_ratings": "not distributed"})))
    store.db.commit()
    report = {"source": sid, "new_observations": count, "molecules_resolved": len(mapping), "rejected_molecules": rejected,
              "skipped_behavior_rows": skipped, "source_manifest": manifest}
    write_json(raw_root / "ingestion-report.json", report)
    return report


def import_reviewed(path: Path, store: EvidenceStore) -> int:
    """Import reviewed bundles in one transaction. The supplied observation is immutable."""
    count = 0
    with store.db:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            bundle = json.loads(line)
            mol = identify(bundle["smiles"])
            evidence = Evidence.model_validate(bundle["evidence"])
            if evidence.review_status != "accepted" or evidence.permitted_use in ("unverified", ""):
                raise ValueError("Only reviewed evidence with documented permitted use may enter training")
            stimulus = Stimulus.model_validate(bundle["stimulus"])
            obs = Observation.model_validate(bundle["observation"])
            if {obs.molecule_id, stimulus.molecule_id} != {mol.molecule_id}:
                raise ValueError("Bundle molecular identities disagree")
            if obs.evidence_id != evidence.evidence_id or obs.stimulus_id != stimulus.stimulus_id:
                raise ValueError("Bundle foreign keys disagree")
            if len({obs.source_id, stimulus.source_id, evidence.source_id}) != 1:
                raise ValueError("Bundle sources disagree")
            for record in (mol, evidence, stimulus):
                store.add(record)
            count += int(store.add(obs))
    return count

