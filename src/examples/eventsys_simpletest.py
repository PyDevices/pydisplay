from board_config import broker
import asyncio


async def main():
    while True:
        if elist := broker.poll():
            for e in elist:
                print(e)
                if e == broker.events.QUIT:
                    break
        await asyncio.sleep(0.001)


loop = asyncio.get_event_loop()
main_task = loop.create_task(main())  # noqa: RUF006
if hasattr(loop, "run_forever"):
    loop.run_forever()
