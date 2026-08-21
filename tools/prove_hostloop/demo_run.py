"""Explicit app.run() must still work, with no double-drive."""

from _app import make_app

app = make_app()
app.run()
print("-- run() returned, ticks =", len(app.ticks), "--")
