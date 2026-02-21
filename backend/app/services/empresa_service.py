from __future__ import annotations

import json
import threading
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional


# Ruta base del repo: /Users/.../Agente-ocupacional
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "config" / "empresas" / "data.json"

_lock = threading.Lock()
ALLOWED_SVE_TYPES = {
    "voz",
    "auditivo",
    "quimico",
    "cardiovascular",
    "psicosocial",
    "osteomuscular",
    "btx",
    "biologico",
    "dme",
    "radiaciones ionizantes",
}


def _load_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"empresas": [], "ges": [], "sve": []}

    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_PATH.with_suffix(".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    tmp_path.replace(DATA_PATH)


def get_all_empresas() -> List[Dict[str, Any]]:
    """
    Devuelve todas las empresas con conteos de GES y SVE.
    """
    with _lock:
        data = _load_data()

    empresas = data.get("empresas", [])
    ges = data.get("ges", [])
    sve = data.get("sve", [])

    ges_by_empresa = {}
    for g in ges:
        eid = g.get("empresa_id")
        ges_by_empresa[eid] = ges_by_empresa.get(eid, 0) + 1

    sve_by_empresa = {}
    for s in sve:
        eid = s.get("empresa_id")
        sve_by_empresa[eid] = sve_by_empresa.get(eid, 0) + 1

    result = []
    for e in empresas:
        eid = e.get("id")
        e = e.copy()
        e["ges_count"] = ges_by_empresa.get(eid, 0)
        e["sve_count"] = sve_by_empresa.get(eid, 0)
        result.append(e)

    return result


def get_empresa(empresa_id: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve una empresa con sus GES y SVE asociados.
    """
    with _lock:
        data = _load_data()

    empresas = data.get("empresas", [])
    ges = data.get("ges", [])
    sve = data.get("sve", [])

    empresa = next((e for e in empresas if e.get("id") == empresa_id), None)
    if not empresa:
        return None

    empresa = empresa.copy()
    empresa["ges"] = [g for g in ges if g.get("empresa_id") == empresa_id]
    empresa["sve"] = [s for s in sve if s.get("empresa_id") == empresa_id]
    return empresa


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def create_empresa(data_in: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea una nueva empresa. Requiere al menos nombre y responsable SST.
    """
    required = ["nombre", "responsable_sst_nombre", "responsable_sst_email", "responsable_sst_telefono"]
    for field in required:
        if not data_in.get(field):
            raise ValueError(f"Campo requerido faltante: {field}")

    empresa = data_in.copy()

    with _lock:
        data = _load_data()
        empresas = data.setdefault("empresas", [])

        empresa_id = empresa.get("id") or _generate_id("emp")
        if any(e.get("id") == empresa_id for e in empresas):
            raise ValueError(f"Ya existe una empresa con id={empresa_id}")

        empresa["id"] = empresa_id
        empresas.append(empresa)
        _save_data(data)

    return empresa


def update_empresa(empresa_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza campos básicos de la empresa.
    """
    with _lock:
        data = _load_data()
        empresas = data.setdefault("empresas", [])

        for idx, e in enumerate(empresas):
            if e.get("id") == empresa_id:
                new_e = e.copy()
                new_e.update(updates)
                empresas[idx] = new_e
                _save_data(data)
                return new_e

    return None


def add_ges(empresa_id: str, ges_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega un GES (grupo de exposición similar) a una empresa.
    """
    with _lock:
        data = _load_data()
        empresas = data.setdefault("empresas", [])
        ges_list = data.setdefault("ges", [])

        if not any(e.get("id") == empresa_id for e in empresas):
            raise ValueError(f"No existe empresa con id={empresa_id}")

        payload = ges_data.copy()
        payload["empresa_id"] = empresa_id

        if "id" not in payload or not payload["id"]:
            payload["id"] = f"{empresa_id}-ges-{len(ges_list) + 1}"

        payload["cargos"] = payload.get("cargos") or []
        payload["peligros_principales"] = payload.get("peligros_principales") or payload.get("riesgos_principales") or []
        payload["examenes_incluidos"] = payload.get("examenes_incluidos") or []
        payload["criterios_clinicos"] = payload.get("criterios_clinicos")
        payload["relacion_examenes"] = payload.get("relacion_examenes")

        ges_list.append(payload)
        _save_data(data)

    return payload


def update_ges(empresa_id: str, ges_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza un GES existente de la empresa.
    """
    with _lock:
        data = _load_data()
        ges_list = data.setdefault("ges", [])

        for idx, ges in enumerate(ges_list):
            if ges.get("id") == ges_id and ges.get("empresa_id") == empresa_id:
                updated = ges.copy()
                updated.update(updates or {})
                updated["cargos"] = updated.get("cargos") or []
                updated["peligros_principales"] = updated.get("peligros_principales") or []
                updated["examenes_incluidos"] = updated.get("examenes_incluidos") or []
                updated["criterios_clinicos"] = updated.get("criterios_clinicos")
                updated["relacion_examenes"] = updated.get("relacion_examenes")
                ges_list[idx] = updated
                _save_data(data)
                return updated

    return None


def add_sve(empresa_id: str, sve_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega un SVE (sistema de vigilancia epidemiológica) a una empresa.
    """
    with _lock:
        data = _load_data()
        empresas = data.setdefault("empresas", [])
        sve_list = data.setdefault("sve", [])

        if not any(e.get("id") == empresa_id for e in empresas):
            raise ValueError(f"No existe empresa con id={empresa_id}")

        payload = sve_data.copy()
        payload["empresa_id"] = empresa_id

        tipo = (payload.get("tipo") or payload.get("nombre") or "").strip().lower()
        if not tipo:
            raise ValueError("El SVE debe tener un tipo válido")
        if tipo not in ALLOWED_SVE_TYPES:
            raise ValueError(f"Tipo de SVE no permitido. Debe ser uno de: {', '.join(sorted(ALLOWED_SVE_TYPES))}")

        payload["tipo"] = tipo

        if not payload.get("nombre"):
            payload["nombre"] = tipo.capitalize()

        if "id" not in payload or not payload["id"]:
            payload["id"] = f"{empresa_id}-sve-{len(sve_list) + 1}"

        payload["descripcion"] = payload.get("descripcion")
        payload["objetivo"] = payload.get("objetivo")
        payload["estado"] = payload.get("estado")
        payload["diagnosticos_cie10"] = payload.get("diagnosticos_cie10") or []

        sve_list.append(payload)
        _save_data(data)

    return payload


def set_sve_list(empresa_id: str, tipos: List[str]) -> List[Dict[str, Any]]:
    """
    Reemplaza por completo los SVE activos para una empresa, usando la lista de tipos permitidos.
    """
    cleaned: List[str] = []
    for tipo in tipos:
        tipo_clean = (tipo or "").strip().lower()
        if not tipo_clean:
            continue
        if tipo_clean not in ALLOWED_SVE_TYPES:
            raise ValueError(f"Tipo de SVE no permitido: {tipo_clean}")
        if tipo_clean not in cleaned:
            cleaned.append(tipo_clean)

    with _lock:
        data = _load_data()
        empresas = data.setdefault("empresas", [])
        if not any(e.get("id") == empresa_id for e in empresas):
            raise ValueError(f"No existe empresa con id={empresa_id}")

        sve_list = data.setdefault("sve", [])
        sve_list[:] = [s for s in sve_list if s.get("empresa_id") != empresa_id]

        for index, tipo in enumerate(cleaned, start=1):
            sve_list.append(
                {
                    "id": f"{empresa_id}-sve-{index}",
                    "empresa_id": empresa_id,
                    "tipo": tipo,
                    "nombre": tipo.capitalize(),
                    "descripcion": "",
                    "objetivo": "",
                    "estado": "activo",
                    "diagnosticos_cie10": [],
                }
            )

        _save_data(data)

    with _lock:
        data = _load_data()
        return [s for s in data.get("sve", []) if s.get("empresa_id") == empresa_id]
