"""
Tracking de costos de API (Claude y Azure).

Registra uso de tokens y costos estimados en archivo JSONL para auditoría.
"""

import json
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Costos por millón de tokens (USD) - actualizar si cambian los precios
MODEL_COSTS = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0, "cache_read": 0.30},
    "claude-haiku-4-20250514": {"input": 1.0, "output": 5.0, "cache_read": 0.10},
}

# Fallback para modelos no listados
DEFAULT_COSTS = {"input": 3.0, "output": 15.0, "cache_read": 0.30}


class CostTracker:
    """Registra costos de API en archivo JSONL."""

    def __init__(self, costs_file: Optional[Path] = None):
        self._lock = threading.Lock()
        if costs_file is None:
            costs_file = Path("data/costs.jsonl")
        self.costs_file = costs_file
        self.costs_file.parent.mkdir(parents=True, exist_ok=True)

    def log_claude_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        archivo: str,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ) -> dict:
        """
        Registra una llamada a Claude API con cálculo de costo.

        Returns:
            dict con el registro guardado (incluye costo estimado)
        """
        costs = MODEL_COSTS.get(model, DEFAULT_COSTS)

        cost_input = (input_tokens / 1_000_000) * costs["input"]
        cost_output = (output_tokens / 1_000_000) * costs["output"]
        cost_cache = (cache_read_tokens / 1_000_000) * costs["cache_read"]

        total_cost = cost_input + cost_output + cost_cache

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "claude",
            "model": model,
            "archivo": archivo,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "cost_usd": round(total_cost, 6),
        }

        self._append(record)

        logger.info(
            f"Costo Claude: ${total_cost:.4f} USD "
            f"({input_tokens} in + {output_tokens} out"
            f"{f' + {cache_read_tokens} cache' if cache_read_tokens else ''}) "
            f"- {archivo}"
        )

        return record

    def log_azure_usage(self, archivo: str, page_count: int) -> dict:
        """Registra una llamada a Azure Document Intelligence."""
        # Azure cobra ~$1.50 por 1000 páginas (S0 tier)
        cost = (page_count / 1000) * 1.50

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "azure",
            "archivo": archivo,
            "page_count": page_count,
            "cost_usd": round(cost, 6),
        }

        self._append(record)
        logger.info(f"Costo Azure: ${cost:.4f} USD ({page_count} páginas) - {archivo}")
        return record

    def get_daily_summary(self, target_date: Optional[date] = None) -> dict:
        """Resumen de costos del día."""
        if target_date is None:
            target_date = date.today()

        date_str = target_date.isoformat()
        total = 0.0
        claude_total = 0.0
        azure_total = 0.0
        request_count = 0

        for record in self._read_all():
            if record.get("timestamp", "").startswith(date_str):
                cost = record.get("cost_usd", 0)
                total += cost
                request_count += 1
                if record.get("service") == "claude":
                    claude_total += cost
                elif record.get("service") == "azure":
                    azure_total += cost

        return {
            "date": date_str,
            "total_usd": round(total, 4),
            "claude_usd": round(claude_total, 4),
            "azure_usd": round(azure_total, 4),
            "request_count": request_count,
        }

    def get_total(self) -> dict:
        """Costo total acumulado."""
        total = 0.0
        claude_total = 0.0
        azure_total = 0.0
        request_count = 0

        for record in self._read_all():
            cost = record.get("cost_usd", 0)
            total += cost
            request_count += 1
            if record.get("service") == "claude":
                claude_total += cost
            elif record.get("service") == "azure":
                azure_total += cost

        return {
            "total_usd": round(total, 4),
            "claude_usd": round(claude_total, 4),
            "azure_usd": round(azure_total, 4),
            "request_count": request_count,
        }

    def _append(self, record: dict):
        with self._lock:
            with open(self.costs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _read_all(self) -> list[dict]:
        if not self.costs_file.exists():
            return []
        records = []
        with open(self.costs_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records


# Singleton
_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
