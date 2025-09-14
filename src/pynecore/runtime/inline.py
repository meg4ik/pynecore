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

def run_inline(*, script_code: str, ohlcv: Sequence[Dict[str, Any]], timeframe: str) -> InlineResult:
    if not ohlcv:
        return InlineResult(signals=[], stats={}, equity_curve=[])

    last = ohlcv[-1]
    TF_MS = {
        "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
        "1h": 3_600_000, "4h": 14_400_000, "D": 86_400_000, "W": 604_800_000, "M": 2_592_000_000,
    }[timeframe]

    last_open = int(last["time_unix_ms"])
    last_close_ts = last_open + TF_MS

    sink = _MemorySink()
    rec = _StrategyCallRecorder(sink=sink, bar_close_ts_ms=last_close_ts, last_close_price=float(last["close"]))

    closes = [float(b["close"])  for b in ohlcv]
    opens  = [float(b["open"])   for b in ohlcv]
    highs  = [float(b["high"])   for b in ohlcv]
    lows   = [float(b["low"])    for b in ohlcv]
    vols   = [float(b["volume"]) for b in ohlcv]

    old_close  = getattr(_lib, "close",  None)
    old_open   = getattr(_lib, "open",   None)
    old_high   = getattr(_lib, "high",   None)
    old_low    = getattr(_lib, "low",    None)
    old_volume = getattr(_lib, "volume", None)

    def _set_or_series(name: str, values):
        obj = getattr(_lib, name, None)
        if obj is not None and hasattr(obj, "set"):
            obj.set(values)
        else:
            setattr(_lib, name, Series(values))

    _set_or_series("close",  closes)
    _set_or_series("open",   opens)
    _set_or_series("high",   highs)
    _set_or_series("low",    lows)
    _set_or_series("volume", vols)

    orig_entry = strategy.entry
    orig_close = strategy.close

    try:
        strategy.entry = rec.entry
        strategy.close = rec.close

        mod = _compile_module(script_code)

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

        setattr(_lib, "close",  old_close)
        setattr(_lib, "open",   old_open)
        setattr(_lib, "high",   old_high)
        setattr(_lib, "low",    old_low)
        setattr(_lib, "volume", old_volume)
