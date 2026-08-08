from _typeshed import Incomplete

Timer: Incomplete
AUTO_BACKENDS: Incomplete
BACKENDS: Incomplete

class _BoundBackend:
    Timer: Incomplete
    def __init__(self, name, timer_cls, *, uses_signals: bool = False, sleep_ms=None, drain=None) -> None: ...

def load_backend(name) -> None: ...
def backends_available(): ...
