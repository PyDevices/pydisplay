# pyscript gallery: async
from board_config import runtime
from multimer import Timer
from multimer.loop import dual_main, run_forever


def _heartbeat(_=None):
    print("eventsys_simpletest: polling… (click the canvas)")


def _poll_events():
    elist = runtime.poll() if runtime else []
    if runtime.quit_requested if runtime else False:
        print("eventsys_simpletest: quit")
        return True
    for e in elist:
        print(e)
        if e.type == runtime.events.QUIT:
            print("eventsys_simpletest: quit")
            return True
    return False


def main_sync():
    print("eventsys_simpletest: started — click the canvas to see pointer events")
    timer = Timer(-1)
    timer.init(mode=Timer.PERIODIC, period=2000, callback=_heartbeat)
    try:
        run_forever(_poll_events, delay_ms=20)
    finally:
        timer.deinit()


async def main_async():
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    async def _heartbeat():
        while True:
            await asyncio.sleep(2)
            print("eventsys_simpletest: polling… (click the canvas)")

    print("eventsys_simpletest: started — click the canvas to see pointer events")
    asyncio.create_task(_heartbeat())
    while True:
        elist = runtime.poll() if runtime else []
        if runtime.quit_requested if runtime else False:
            print("eventsys_simpletest: quit")
            return
        for e in elist:
            print(e)
            if e.type == runtime.events.QUIT:
                print("eventsys_simpletest: quit")
                return
        await asyncio.sleep(0.02)


dual_main(main_sync, main_async, async_mode=runtime.timer_async)
