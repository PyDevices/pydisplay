# multimer types: async
import board_config

board_config.TIMER_ASYNC = True

from board_config import broker

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

from multimer.aio import run


async def _heartbeat():
    while True:
        await asyncio.sleep(2)
        print("eventsys_simpletest: polling… (click the canvas)")


async def main():
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


run(main)
