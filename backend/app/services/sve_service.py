"""
Servicio para evaluar SVE usando el catálogo global de config/empresas/sve_catalog.json
"""
from __future__ import annotations

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parents[3] / "config" / "empresas" / "sve_catalog.json"

DEFAULT_SPECIALIST = "Medicina General / EPS"
SVE_SPECIALISTS = {
    "sve-visual": "Oftalmología",
    "sve-auditivo": "Otorrinolaringología",
    "sve-voz": "Fonoaudiología / Otorrinolaringología",
    "sve-osteomuscular": "Fisiatría / Ortopedia",
    "sve-dme": "Medicina Física y Rehabilitación",
    "sve-cardiovascular": "Medicina Interna / Cardiología",
    "sve-biologico": "Medicina Laboral / Epidemiología",
    "sve-psicosocial": "Psicología / Psiquiatría",
    "sve-quimico": "Toxicología / Medicina Interna",
    "sve-btx": "Toxicología",
}


def _normalize_token(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    for char in (" ", "_", "/", ".", ","):
        text = text.replace(char, "-")
    while "--" in text:
        text = text.replace("--", "-")
    return text


def canonicalize_sve_id(value: Any) -> str:
    token = _normalize_token(value)
    if not token:
        return ""
    if token.startswith("sve-"):
        return token
    return f"sve-{token}"


def canonicalize_sve_tokens(value: Any) -> Set[str]:
    canonical = canonicalize_sve_id(value)
    if not canonical:
        return set()
    tokens = {canonical}
    if canonical.startswith("sve-"):
        tokens.add(canonical[4:])
    return {token for token in tokens if token}


def _code_variants(code: str) -> Set[str]:
    variants: Set[str] = set()
    if not code:
        return variants
    variants.add(code)
    compact = code.replace(".", "")
    if compact:
        variants.add(compact)
    if "." in code:
        base = code.split(".")[0]
        if base:
            variants.add(base)
            base_compact = base.replace(".", "")
            if base_compact:
                variants.add(base_compact)
    return variants


@lru_cache()
def _load_entries() -> List[Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        logger.warning("Catálogo de SVE no encontrado en %s", CATALOG_PATH)
        return []
    try:
        with CATALOG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        logger.exception("Error cargando catálogo de SVE")
    return []


@lru_cache()
def _catalog_indexes() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    by_identifier: Dict[str, Dict[str, Any]] = {}
    by_code: Dict[str, List[Dict[str, Any]]] = {}

    for entry in _load_entries():
        canonical = canonicalize_sve_id(entry.get("sve_id") or entry.get("nombre"))
        if not canonical:
            continue

        for token in canonicalize_sve_tokens(entry.get("sve_id")) | canonicalize_sve_tokens(entry.get("nombre")) | {canonical}:
            by_identifier[token] = {"canonical_id": canonical, "entry": entry}

        for dx in entry.get("dx_cie10", []):
            code = (dx.get("codigo") or "").strip().upper()
            if not code:
                continue
            for variant in _code_variants(code):
                by_code.setdefault(variant, []).append(
                    {
                        "canonical_id": canonical,
                        "entry": entry,
                        "diagnostico": dx.get("diagnostico") or "",
                    }
                )

    return by_identifier, by_code


def evaluate_sve(diagnosticos_cie10: List[str], empresa_sve_ids: List[str]) -> Dict[str, Any]:
    catalog_by_id, code_map = _catalog_indexes()

    empresa_canonicals: Set[str] = set()
    for raw in empresa_sve_ids or []:
        for token in canonicalize_sve_tokens(raw):
            info = catalog_by_id.get(token)
            if info:
                empresa_canonicals.add(info["canonical_id"])

    alertas: Dict[str, Dict[str, Any]] = {}
    derivar_eps_groups: Dict[str, Dict[str, Any]] = {}

    def _derive_entry(target_id: str, entry_meta: Dict[str, Any]) -> Dict[str, Any]:
        if target_id:
            specialist = SVE_SPECIALISTS.get(target_id) or entry_meta.get("nombre") or DEFAULT_SPECIALIST
            key = target_id
        else:
            specialist = DEFAULT_SPECIALIST
            key = f"general-{specialist}"

        group = derivar_eps_groups.setdefault(
            key,
            {
                "sve_id": target_id,
                "especialista": specialist,
                "diagnosticos": [],
            },
        )
        return group

    for raw_code in diagnosticos_cie10 or []:
        code = (raw_code or "").strip().upper()
        if not code:
            continue

        catalog_entries: List[Dict[str, Any]] = []
        seen = set()
        for variant in _code_variants(code) | {code}:
            for entry in code_map.get(variant, []):
                key = (entry["canonical_id"], entry["diagnostico"])
                if key in seen:
                    continue
                seen.add(key)
                catalog_entries.append(entry)

        matched = False
        for entry in catalog_entries:
            canonical_id = entry["canonical_id"]
            if empresa_canonicals and canonical_id not in empresa_canonicals:
                continue
            matched = True
            catalog_entry = entry["entry"]
            alerta = alertas.setdefault(
                canonical_id,
                {
                    "sve_target_id": canonical_id,
                    "nombre": catalog_entry.get("nombre") or canonical_id,
                    "descripcion": catalog_entry.get("descripcion") or "",
                    "diagnosticos": [],
                },
            )
            alerta["diagnosticos"].append(
                {
                    "codigo": code,
                    "descripcion": entry.get("diagnostico"),
                }
            )

        if not matched:
            if catalog_entries:
                base_entry = catalog_entries[0]
                target_id = base_entry["canonical_id"]
                entry_meta = base_entry["entry"]
                descripcion = base_entry.get("diagnostico") or ""
            else:
                target_id = ""
                entry_meta = {}
                descripcion = ""

            group = _derive_entry(target_id, entry_meta)
            group["diagnosticos"].append({"codigo": code, "descripcion": descripcion})

    return {
        "alertas_sve": list(alertas.values()),
        "derivar_eps": list(derivar_eps_groups.values()),
    }


__all__ = ["evaluate_sve", "canonicalize_sve_tokens", "canonicalize_sve_id"]
