from ._async_timer import AsyncTimer as AsyncTimer
from ._backends import librt as librt, polling as polling, sdl2 as sdl2, threading as threading
from _typeshed import Incomplete

Timer: Incomplete
Timer = AsyncTimer
Timer = AsyncTimer
