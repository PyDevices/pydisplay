from board_config import runtime


def _heartbeat(_=None):
    print("eventsys_simpletest: polling… (click the canvas)")


def _on_event(e):
    print(e)


print("eventsys_simpletest: started — click the canvas to see pointer events")
runtime.on_tick(_heartbeat, period=2000, async_=runtime.timer_async)

# Subscribe broadly via device type so any pointer/key event prints.
for et in (
    runtime.events.MOUSEBUTTONDOWN,
    runtime.events.MOUSEBUTTONUP,
    runtime.events.MOUSEMOTION,
    runtime.events.KEYDOWN,
    runtime.events.KEYUP,
):
    runtime.on(et, _on_event)

runtime.run_forever()
