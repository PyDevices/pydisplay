"""Async timers, no app.run(). Needs hostloop's drive path."""

from _app import make_app

app = make_app(timer_async=True)
print("-- script body ends here --")
