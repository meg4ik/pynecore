from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
import types
import hashlib
import threading

from pynecore.lib import strategy, close as s_close, open as s_open, high as s_high, low as s_low, volume as s_volume

@dataclass
class Signal:
    time_unix_ms: int
    side: str           # "long"|"short"
    action: str         # "open"|"close"
    qty_pct: float
    price: Optional[float] = None
    label: Optional[str] = None

@dataclass
class InlineResult:
    signals: List[Signal]
    stats: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]


class _MemorySink:
    def __init__(self) -> None:
        self.signals: List[Signal] = []
        self.stats: Dict[str, Any] = {}
        self.equity_curve: List[Dict[str, Any]] = []


_compile_cache_lock = threading.Lock()
_compile_cache: Dict[str, types.ModuleType] = {}

def _compile_module(code: str) -> types.ModuleType:
    key = hashlib.sha256(code.encode("utf-8")).hexdigest()
    with _compile_cache_lock:
        mod = _compile_cache.get(key)
        if mod is not None:
            return mod
        mod = types.ModuleType(f"pynecore_user_{key[:16]}")
        mod.__file__ = f"<pynecore:{key[:8]}>"
        exec(compile(code, filename=mod.__file__, mode="exec"), mod.__dict__)
        _compile_cache[key] = mod
        return mod

class _StrategyCallRecorder:
    def __init__(self, sink: _MemorySink, bar_close_ts_ms: int, last_close_price: Optional[float]):
        self.sink = sink
        self.ts = bar_close_ts_ms
        self.last_close = last_close_price

    def entry(self, label: str, side: str, qty_type: Optional[str] = None, qty_value: Optional[float] = None, **kwargs):
        qty_pct = 0.0
        if qty_type == getattr(strategy, "percent_of_equity", None):
            qty_pct = float(qty_value or 0.0)
        self.sink.signals.append(Signal(
            time_unix_ms=self.ts,
            side=("long" if side == strategy.long else "short"),
            action="open",
            qty_pct=qty_pct,
            price=self.last_close,
            label=label,
        ))

    def close(self, label: str, **kwargs):
        self.sink.signals.append(Signal(
            time_unix_ms=self.ts,
            side="long",
            action="close",
            qty_pct=0.0,
            price=self.last_close,
            label=label,
        ))

def run_inline(
    *,
    script_code: str,
    ohlcv: Sequence[Dict[str, Any]],
    timeframe: str,
) -> InlineResult:

    if not ohlcv:
        return InlineResult(signals=[], stats={}, equity_curve=[])

    mod = _compile_module(script_code)

    last = ohlcv[-1]

    TF_MS = {
        "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
        "1h": 3_600_000, "4h": 14_400_000, "D": 86_400_000, "W": 604_800_000, "M": 2_592_000_000,
    }[timeframe]

    last_open = int(last["time_unix_ms"])
    last_close_ts = last_open + TF_MS

    sink = _MemorySink()
    rec = _StrategyCallRecorder(sink=sink, bar_close_ts_ms=last_close_ts, last_close_price=float(last["close"]))

    orig_entry = strategy.entry
    orig_close = strategy.close

    try:
        strategy.entry = rec.entry
        strategy.close = rec.close

        closes = [float(b["close"]) for b in ohlcv]
        opens  = [float(b["open"]) for b in ohlcv]
        highs  = [float(b["high"]) for b in ohlcv]
        lows   = [float(b["low"])  for b in ohlcv]
        vols   = [float(b["volume"]) for b in ohlcv]

        s_close.set(closes)
        s_open.set(opens)
        s_high.set(highs)
        s_low.set(lows)
        s_volume.set(vols)

        main = getattr(mod, "main", None)
        if not callable(main):
            return InlineResult(signals=[], stats={}, equity_curve=[])

        main()

        return InlineResult(
            signals=sink.signals,
            stats=sink.stats,
            equity_curve=sink.equity_curve,
        )

    finally:
        strategy.entry = orig_entry
        strategy.close = orig_close
