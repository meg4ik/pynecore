import threading
_local = threading.local()

def set_sink(sink):
    _local.sink = sink

def clear_sink():
    if hasattr(_local, "sink"):
        _local.sink = None

def emit(action: str, **kwargs):
    sink = getattr(_local, "sink", None)
    if sink:
        try:
            sink(action, **kwargs)
        except Exception:
            pass