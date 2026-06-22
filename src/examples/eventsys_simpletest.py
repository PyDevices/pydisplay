# multimer types: async
import board_config

board_config.TIMER_ASYNC = True

from board_config import broker

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio


async def main():
    while True:
        if elist := broker.poll():
            for e in elist:
                print(e)
                if e.type == broker.events.QUIT:
                    return
        await asyncio.sleep(0)


if hasattr(asyncio, "run"):
    asyncio.run(main())
else:
    asyncio.get_event_loop().run_until_complete(main())
