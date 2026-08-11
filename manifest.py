"""Freeze pydisplay packages for MicroPython (included by cmods/manifest.py)."""

if 0:

    def include(*args, **kwargs):
        pass

    def package(*args, **kwargs):
        pass

    def module(*args, **kwargs):
        pass

    def require(*args, **kwargs):
        pass


package("displaydev", base_path="./src/lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
package("eventsys", base_path="./src/lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
package("multimer", base_path="./src/lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
