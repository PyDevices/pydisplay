Clone the examples, create a virtual environment, and install the published
product packages:

```bash
git clone https://github.com/PyDevices/pydevices-examples.git
cd pydevices-examples
python3 -m venv .venv
.venv/bin/pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ -r requirements.txt
cd src
../.venv/bin/python examples/pydevices_demo.py
```

A window should open with the demo. Touch or click **Rotate** and **Color**;
the tips list scrolls. See the [pydevices_demo guide](../examples/pydevices-demo.md)
for a walkthrough or copy the [App starter](../examples/app-starter.md).

On Windows, use `.venv\Scripts\python.exe`. For source-checkout development,
clone `pydevices` as a sibling and use `utils.path` or add its `lib`,
`utils`, and `drivers/display` directories to the interpreter path.
