"""Strict interchange records; missing data and censoring are never guessed."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Endpoint(str, Enum):
    CATALOGUE = "catalogue_descriptor"
    PANEL = "panel_descriptor"
    AIR = "air_detection_threshold"
    WATER = "water_detection_threshold"
    RECOGNITION = "recognition_threshold"
    INTENSITY = "intensity"
    PLEASANTNESS = "pleasantness"
    DETECTION = "detection_response"
    RECEPTOR = "receptor_activation"
    EC50 = "receptor_ec50"
    PROPERTY = "physical_property"


class Molecule(Record):
    molecule_id: str
    original_smiles: str
    smiles: str
    inchikey: str
    connectivity_id: str
    molecular_weight: float = Field(gt=0)
    stereo_status: Literal["specified", "unspecified", "achiral"]
    material_type: Literal["single_compound", "isomer_mixture", "mixture"] = "single_compound"
    identifiers: dict[str, str] = Field(default_factory=dict)


class Stimulus(Record):
    stimulus_id: str
    molecule_id: str
    source_id: str
    matrix: str = "unknown"
    solvent: str | None = None
    batch: str | None = None
    purity: float | None = Field(default=None, gt=0, le=1)
    nominal_concentration: float | None = Field(default=None, ge=0)
    delivered_concentration: float | None = Field(default=None, ge=0)
    concentration_unit: str | None = None
    concentration_basis: str | None = None
    temperature_k: float | None = Field(default=None, gt=0)
    pressure_pa: float | None = Field(default=None, gt=0)
    delivery_method: str | None = None
    exposure_seconds: float | None = Field(default=None, gt=0)
    metadata: dict = Field(default_factory=dict)


class Evidence(Record):
    evidence_id: str
    source_id: str
    source_url: str
    original_experiment_id: str
    location: str
    source_sha256: str | None = None
    doi: str | None = None
    patent_family: str | None = None
    supporting_text: str | None = None
    review_status: Literal["upstream_curated", "pending", "accepted", "rejected"] = "pending"
    permitted_use: str = "unverified"
    extraction_version: str = "calnew-v1"
    is_aggregate: bool = False
    metadata: dict = Field(default_factory=dict)


class Observation(Record):
    observation_id: str
    molecule_id: str
    stimulus_id: str
    evidence_id: str
    source_id: str
    endpoint: Endpoint
    descriptor: str | None = None
    raw_value: str
    raw_unit: str | None = None
    value: float | None = None
    unit: str | None = None
    censoring: Literal["exact", "left", "right", "interval", "missing"] = "exact"
    lower: float | None = None
    upper: float | None = None
    subject_id: str | None = None
    panel_id: str | None = None
    replicate: str | None = None
    method: str = "unknown"
    label_state: Literal["observed", "not_reported", "not_assessed", "assessed_absent"] = "observed"
    value_origin: Literal["measured", "upstream_aggregate", "predicted", "calculated"] = "measured"
    uncertainty: float | None = Field(default=None, ge=0)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_bounds(self):
        if self.censoring == "exact" and self.value is None:
            raise ValueError("Exact observations require a value")
        if self.censoring == "left" and self.upper is None:
            raise ValueError("Left-censored observations require an upper bound")
        if self.censoring == "right" and self.lower is None:
            raise ValueError("Right-censored observations require a lower bound")
        if self.censoring == "interval" and (self.lower is None or self.upper is None or self.lower >= self.upper):
            raise ValueError("Interval censoring requires lower < upper")
        if self.censoring not in ("exact", "missing") and self.value is not None:
            raise ValueError("Censored observations must not carry an exact point value")
        if self.censoring == "missing" and (self.value is not None or self.lower is not None or self.upper is not None):
            raise ValueError("Missing observation cannot contain numerical outcomes")
        if self.endpoint in (Endpoint.AIR, Endpoint.WATER) and self.unit is not None:
            expected = "log10(ppbv)" if self.endpoint == Endpoint.AIR else "log10(mg/L)"
            if self.unit != expected:
                raise ValueError(f"{self.endpoint.value} requires normalised unit {expected}")
        return self


class PredictionRecord(Record):
    molecule_id: str | None
    smiles: str
    endpoint: str
    status: Literal["available", "unavailable"]
    reason: str | None = None
    context: dict = Field(default_factory=dict)
    estimates: dict = Field(default_factory=dict)
    uncertainty: dict = Field(default_factory=dict)
    applicability: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)

