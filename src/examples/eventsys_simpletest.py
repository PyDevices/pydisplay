# multimer types: async
from board_config import broker
from multimer import dual_main, periodic, run_forever


def _heartbeat(_=None):
    print("eventsys_simpletest: polling… (click the canvas)")


def _poll_events():
    if elist := broker.poll():
        for e in elist:
            print(e)
            if e.type == broker.events.QUIT:
                print("eventsys_simpletest: quit")
                return True
    return False


def main_sync():
    print("eventsys_simpletest: started — click the canvas to see pointer events")
    periodic(_heartbeat, period=2000)
    run_forever(_poll_events, delay_ms=20)


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
        if elist := broker.poll():
            for e in elist:
                print(e)
                if e.type == broker.events.QUIT:
                    print("eventsys_simpletest: quit")
                    return
        await asyncio.sleep(0.02)


from board_config import TIMER_ASYNC

dual_main(main_sync, main_async, async_mode=TIMER_ASYNC)
