Clone the examples, create a virtual environment, and install the published
product packages:

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay
python3 -m venv .venv
.venv/bin/pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ -r requirements.txt
cd src
../.venv/bin/python examples/pydisplay_demo.py
```

A window should open with the demo. Touch or click **Rotate** and **Color**;
the tips list scrolls. See the [pydisplay_demo guide](../examples/pydisplay_demo.md)
for a walkthrough or copy the [App starter](../examples/app-starter.md).

On Windows, use `.venv\Scripts\python.exe`. For source-checkout development,
clone `micropython-hardware` as a sibling and use `utils.path` or add its `lib`,
`utils`, and `drivers/display` directories to the interpreter path.
