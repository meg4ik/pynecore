from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
import hashlib, threading, types, sys, importlib.machinery

from pynecore.lib import strategy
import pynecore.lib as _lib
from pynecore.types.series import Series

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

        module_name = f"pynecore_user_{key[:16]}"
        mod = types.ModuleType(module_name)

        virtual_file = f"/virtual/{module_name}.py"
        mod.__file__ = virtual_file
        mod.__package__ = None
        mod.__spec__ = importlib.machinery.ModuleSpec(
            name=module_name,
            loader=None,
            is_package=False,
        )

        sys.modules[module_name] = mod

        d = mod.__dict__
        d.setdefault("__name__", module_name)
        d.setdefault("__file__", virtual_file)
        d.setdefault("__package__", None)
        d.setdefault("__spec__", mod.__spec__)

        code_obj = compile(code, filename=virtual_file, mode="exec")

        exec(code_obj, d)

        _compile_cache[key] = mod
        return mod

class _StrategyCallRecorder:
    def __init__(self, sink: _MemorySink):
        self.sink = sink
        self.ts: int | None = None
        self.last_close: float | None = None

    def set_context(self, bar_close_ts_ms: int, last_close_price: float) -> None:
        self.ts = bar_close_ts_ms
        self.last_close = last_close_price

    def entry(self, label: str, side: str, qty_type: Optional[str] = None, qty_value: Optional[float] = None, **kwargs):
        qty_pct = 0.0
        if qty_type == getattr(strategy, "percent_of_equity", None):
            qty_pct = float(qty_value or 0.0)
        self.sink.signals.append(Signal(
            time_unix_ms=int(self.ts or 0),
            side=("long" if side == strategy.long else "short"),
            action="open",
            qty_pct=qty_pct,
            price=self.last_close,
            label=label,
        ))

    def close(self, label: str, **kwargs):
        self.sink.signals.append(Signal(
            time_unix_ms=int(self.ts or 0),
            side="long",
            action="close",
            qty_pct=0.0,
            price=self.last_close,
            label=label,
        ))

def run_inline(*, script_code: str, ohlcv: Sequence[Dict[str, Any]], timeframe: str) -> InlineResult:
    if not ohlcv:
        return InlineResult(signals=[], stats={}, equity_curve=[])

    TF_MS = {"1m": 60000, "5m": 300000, "15m": 900000, "30m": 1800000,
             "1h": 3600000, "4h": 14400000, "D": 86400000, "W": 604800000, "M": 2592000000}[timeframe]

    sink = _MemorySink()
    rec = _StrategyCallRecorder(sink=sink)

    orig_entry = strategy.entry
    orig_close = strategy.close

    old_close  = getattr(_lib, "close",  None)
    old_open   = getattr(_lib, "open",   None)
    old_high   = getattr(_lib, "high",   None)
    old_low    = getattr(_lib, "low",    None)
    old_volume = getattr(_lib, "volume", None)

    try:
        strategy.entry = rec.entry
        strategy.close = rec.close

        mod = _compile_module(script_code)
        main = getattr(mod, "main", None)
        if not callable(main):
            return InlineResult(signals=[], stats={}, equity_curve=[])

        for b in ohlcv:
            _lib.open   = float(b["open"])
            _lib.high   = float(b["high"])
            _lib.low    = float(b["low"])
            _lib.close  = float(b["close"])
            _lib.volume = float(b["volume"])

            bar_open_ms   = int(b["time_unix_ms"])
            bar_close_ms  = bar_open_ms + TF_MS
            rec.set_context(bar_close_ms, float(b["close"]))

            main()

        return InlineResult(signals=sink.signals, stats=sink.stats, equity_curve=sink.equity_curve)

    finally:
        strategy.entry = orig_entry
        strategy.close = orig_close

        if old_close  is not None:  _lib.close  = old_close
        if old_open   is not None:  _lib.open   = old_open
        if old_high   is not None:  _lib.high   = old_high
        if old_low    is not None:  _lib.low    = old_low
        if old_volume is not None:  _lib.volume = old_volume
