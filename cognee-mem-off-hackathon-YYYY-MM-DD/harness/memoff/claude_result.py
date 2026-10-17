"""Parse the JSON that ``claude -p --output-format json`` prints, into usage records."""

from __future__ import annotations

import json
from pathlib import Path

PRICES_FILE = Path(__file__).with_name("data") / "prices.json"


def load_prices() -> dict:
    return json.loads(PRICES_FILE.read_text(encoding="utf-8"))


def parse_result(stdout: str) -> dict:
    """Return the final ``result`` object. Accepts a single JSON object or stream-json lines."""
    text = stdout.strip()
    if not text:
        raise ValueError("claude printed nothing")
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            results = [o for o in obj if isinstance(o, dict) and o.get("type") == "result"]
            if results:
                return results[-1]
    except json.JSONDecodeError:
        pass
    last = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "result":
            last = obj
    if last is None:
        raise ValueError("no result object in claude output")
    return last


def token_fields(result: dict) -> dict:
    usage = result.get("usage") or {}
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens") or 0),
    }


def estimate_cost_usd(model: str, tokens: dict, prices: dict | None = None) -> tuple[float | None, str]:
    """Cost from the pinned price sheet when the CLI did not report one."""
    prices = prices or load_prices()
    sheet = prices.get("models", {}).get(model)
    if not sheet:
        for key, value in prices.get("models", {}).items():
            if model.startswith(key):
                sheet = value
                break
    if not sheet:
        return None, "unknown"
    per_m = 1_000_000
    cost = (
        tokens["input_tokens"] * sheet["input_usd_per_million"]
        + tokens["output_tokens"] * sheet["output_usd_per_million"]
        + tokens["cache_read_input_tokens"] * sheet.get("cache_read_usd_per_million", 0)
        + tokens["cache_creation_input_tokens"] * sheet.get("cache_write_usd_per_million", 0)
    ) / per_m
    return cost, "configured_rates"


def usage_record(result: dict, model: str, op_id: str) -> dict:
    tokens = token_fields(result)
    cost = result.get("total_cost_usd")
    basis = "provider_reported" if isinstance(cost, (int, float)) else None
    if basis is None:
        cost, basis = estimate_cost_usd(model, tokens)
    return {
        "id": op_id,
        "source": "client",
        "tokens_in": tokens["input_tokens"] + tokens["cache_read_input_tokens"] + tokens["cache_creation_input_tokens"],
        "tokens_out": tokens["output_tokens"],
        "cost_usd": cost,
        "token_basis": "provider_reported",
        "cost_basis": basis,
        "detail": tokens,
    }


def agent_metrics(result: dict) -> dict:
    """The per-issue runner metrics the plan's §6 table asks for (agent side)."""
    tokens = token_fields(result)
    return {
        "turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "duration_api_ms": result.get("duration_api_ms"),
        "total_cost_usd": result.get("total_cost_usd"),
        "is_error": bool(result.get("is_error")),
        "subtype": result.get("subtype"),
        "session_id": result.get("session_id"),
        "model_usage": result.get("modelUsage"),
        **tokens,
    }
