"""A script that raises must surface the error, not enter the loop."""

from _app import make_app

app = make_app()
raise ValueError("boom")
