# gallery: skip
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`roku_engine`
====================================================

Roku External Control Protocol (ECP) client — no display, event, or UI imports.

Talks HTTP on port 8060 and discovers devices via SSDP (``ST: roku:ecp``).
Shared by the ``roku_remote`` graphics front end; designed so other UIs can
reuse the same engine later.

Requires the Roku setting **Control by mobile apps → Enabled**. WiFi must
already be associated on microcontroller targets; unix MicroPython uses the
host network.

Usage::

    from roku_engine import RokuEngine

    eng = RokuEngine()
    devices = eng.discover(timeout=3)
    if devices:
        eng.set_host(devices[0]["host"])
    eng.connect()
    eng.press("Home")
    apps = eng.query_apps()
"""

import socket
import sys

try:
    import time
except ImportError:  # pragma: no cover
    time = None

# Default host: empty → discover / set manually. Edit for a fixed target.
ROKU_HOST = ""
ROKU_PORT = 8060

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_ST = "roku:ecp"

# Documented ECP keypress names (remote + TV extras).
ECP_KEYS = (
    "Home",
    "Rev",
    "Fwd",
    "Play",
    "Select",
    "Left",
    "Right",
    "Down",
    "Up",
    "Back",
    "InstantReplay",
    "Info",
    "Backspace",
    "Search",
    "Enter",
    "FindRemote",
    "VolumeDown",
    "VolumeMute",
    "VolumeUp",
    "PowerOff",
    "PowerOn",
    "ChannelUp",
    "ChannelDown",
    "InputTuner",
    "InputHDMI1",
    "InputHDMI2",
    "InputHDMI3",
    "InputHDMI4",
    "InputAV1",
)

ECP_KEY_SET = frozenset(ECP_KEYS)


def _quote_lit(ch):
    """URL-encode one character for Lit_ keypresses (ASCII-safe on MP)."""
    o = ord(ch)
    if ch == " ":
        return "%20"
    if 0x21 <= o <= 0x7E and ch not in "/%?#&=+":
        return ch
    # UTF-8 percent-encode
    try:
        raw = ch.encode("utf-8")
    except (AttributeError, UnicodeEncodeError):
        raw = bytes([o & 0xFF])
    return "".join("%%%02X" % b for b in raw)


def _xml_tag(text, tag):
    """Return first inner text of <tag>...</tag>, or ''."""
    if not text:
        return ""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeError:
            text = str(text)
    open_tag = "<" + tag
    i = text.find(open_tag)
    if i < 0:
        # case-insensitive fallback
        lower = text.lower()
        i = lower.find(open_tag.lower())
        if i < 0:
            return ""
    gt = text.find(">", i)
    if gt < 0:
        return ""
    # self-closing
    if text[gt - 1] == "/":
        return ""
    close = "</" + tag + ">"
    j = text.find(close, gt + 1)
    if j < 0:
        close = "</" + tag.lower() + ">"
        j = text.lower().find(close, gt + 1)
        if j < 0:
            return ""
        # recover original slice end using length
        return text[gt + 1 : gt + 1 + (j - (gt + 1))].strip()
    return text[gt + 1 : j].strip()


def _xml_attrs(open_tag_src):
    """Parse key=\"value\" attributes from an opening tag string."""
    attrs = {}
    if not open_tag_src:
        return attrs
    i = 0
    s = open_tag_src
    while i < len(s):
        # find name=
        while i < len(s) and s[i] in " \t\r\n/<>":
            i += 1
        if i >= len(s) or s[i] == ">":
            break
        j = i
        while j < len(s) and s[j] not in "=\t\r\n />":
            j += 1
        name = s[i:j]
        while j < len(s) and s[j] in " \t":
            j += 1
        if j >= len(s) or s[j] != "=":
            i = j
            continue
        j += 1
        while j < len(s) and s[j] in " \t":
            j += 1
        if j >= len(s):
            break
        quote = s[j]
        if quote in "\"'":
            j += 1
            k = s.find(quote, j)
            if k < 0:
                break
            attrs[name] = s[j:k]
            i = k + 1
        else:
            k = j
            while k < len(s) and s[k] not in " \t>/":
                k += 1
            attrs[name] = s[j:k]
            i = k
    return attrs


def _parse_apps(xml_text):
    """Parse /query/apps XML into list of {id, name, type, version}."""
    if isinstance(xml_text, bytes):
        try:
            xml_text = xml_text.decode("utf-8")
        except UnicodeError:
            xml_text = str(xml_text)
    apps = []
    lower = xml_text.lower()
    pos = 0
    while True:
        i = lower.find("<app", pos)
        if i < 0:
            break
        # Avoid matching the wrapper <apps> tag.
        after = i + 4
        if after < len(lower) and lower[after] not in " \t\r\n/>":
            pos = after
            continue
        gt = xml_text.find(">", i)
        if gt < 0:
            break
        open_src = xml_text[i : gt + 1]
        if open_src.rstrip().endswith("/>"):
            pos = gt + 1
            continue
        close_i = lower.find("</app>", gt)
        if close_i < 0:
            break
        name = xml_text[gt + 1 : close_i].strip()
        attrs = _xml_attrs(open_src)
        apps.append(
            {
                "id": attrs.get("id", ""),
                "name": name,
                "type": attrs.get("type", ""),
                "version": attrs.get("version", ""),
            }
        )
        pos = close_i + 6
    return apps


def _parse_ssdp_headers(data):
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            text = data.decode("latin-1")
    else:
        text = data
    headers = {}
    for line in text.split("\r\n"):
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        headers[key.strip().lower()] = val.strip()
    return headers


def _host_from_location(location):
    """Extract host from http://host:8060/ LOCATION header."""
    if not location:
        return ""
    loc = location.strip()
    if "://" in loc:
        loc = loc.split("://", 1)[1]
    loc = loc.split("/", 1)[0]
    if loc.startswith("["):
        # ipv6 [addr]:port
        end = loc.find("]")
        if end > 0:
            return loc[1:end]
    if ":" in loc:
        # host:port — last split for ipv4
        parts = loc.rsplit(":", 1)
        try:
            int(parts[1])
            return parts[0]
        except (ValueError, IndexError):
            return loc
    return loc


def http_request(method, url, timeout=5.0, data=None):
    """
    Portable HTTP GET/POST → (status_code, body_bytes).

    Tries urllib, then urequests/requests. Raises RuntimeError if no client.
    """
    method = method.upper()
    body = data if data is not None else b""
    if isinstance(body, str):
        body = body.encode("utf-8")

    try:
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError, URLError

        req = Request(url, data=body if method != "GET" else None, method=method)
        if method != "GET":
            req.add_header("Content-Length", str(len(body)))
        try:
            with urlopen(req, timeout=timeout) as resp:
                return int(getattr(resp, "status", 200) or 200), resp.read()
        except HTTPError as e:
            raw = b""
            try:
                raw = e.read()
            except Exception:
                pass
            return int(getattr(e, "code", 0) or 0), raw
        except URLError as e:
            raise RuntimeError(str(getattr(e, "reason", e))) from e
    except ImportError:
        pass

    # MicroPython Request may not support method=; fall through
    except TypeError:
        try:
            from urllib.request import Request, urlopen
            from urllib.error import HTTPError, URLError

            req = Request(url, data=body if method != "GET" else None)
            if method != "GET":
                req.get_method = lambda: method  # type: ignore[attr-defined]
            try:
                with urlopen(req, timeout=timeout) as resp:
                    return int(getattr(resp, "status", 200) or 200), resp.read()
            except HTTPError as e:
                raw = b""
                try:
                    raw = e.read()
                except Exception:
                    pass
                return int(getattr(e, "code", 0) or 0), raw
            except URLError as e:
                raise RuntimeError(str(getattr(e, "reason", e))) from e
        except ImportError:
            pass

    for mod_name in ("urequests", "requests"):
        try:
            mod = __import__(mod_name)
        except ImportError:
            continue
        fn = getattr(mod, method.lower(), None)
        if fn is None and method == "GET":
            fn = getattr(mod, "get", None)
        if fn is None and method == "POST":
            fn = getattr(mod, "post", None)
        if fn is None:
            continue
        try:
            if method == "GET":
                resp = fn(url, timeout=timeout)
            else:
                resp = fn(url, data=body, timeout=timeout)
        except TypeError:
            # older urequests without timeout
            if method == "GET":
                resp = fn(url)
            else:
                resp = fn(url, data=body)
        try:
            if hasattr(resp, "content"):
                raw = resp.content
            elif hasattr(resp, "text"):
                text = resp.text
                raw = text.encode("utf-8") if isinstance(text, str) else text
            elif callable(getattr(resp, "read", None)):
                raw = resp.read()
            else:
                raw = bytes(resp) if resp is not None else b""
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            status = getattr(resp, "status_code", getattr(resp, "status", 200))
            return int(status or 200), raw or b""
        finally:
            close = getattr(resp, "close", None)
            if callable(close):
                close()

    raise RuntimeError("no HTTP client (need urllib, urequests, or requests)")


def discover_rokus(timeout=3.0, retries=2):
    """
    SSDP M-SEARCH for Roku ECP devices.

    Returns a list of dicts: ``{host, location, usn, st}``.
    """
    message = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: %s:%d\r\n"
        'MAN: "ssdp:discover"\r\n'
        "ST: %s\r\n"
        "MX: 2\r\n"
        "\r\n"
    ) % (SSDP_ADDR, SSDP_PORT, SSDP_ST)

    found = {}
    deadline = None
    if time is not None:
        deadline = time.time() + float(timeout)

    for _ in range(max(1, int(retries))):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except (OSError, AttributeError):
                pass
            try:
                # IPPROTO_IP=0, IP_MULTICAST_TTL=33 on many stacks
                sock.setsockopt(0, 33, 2)
            except (OSError, AttributeError):
                pass
            try:
                sock.settimeout(0.4)
            except OSError:
                pass

            payload = message.encode() if isinstance(message, str) else message
            try:
                sock.sendto(payload, (SSDP_ADDR, SSDP_PORT))
            except OSError as e:
                sock.close()
                raise RuntimeError("SSDP send failed: " + str(e)) from e

            while True:
                if deadline is not None and time.time() >= deadline:
                    break
                try:
                    data, _addr = sock.recvfrom(2048)
                except OSError:
                    if deadline is None:
                        break
                    # keep waiting until overall timeout
                    if time is not None and time.time() >= deadline:
                        break
                    continue
                headers = _parse_ssdp_headers(data)
                st = headers.get("st", "")
                location = headers.get("location", "")
                if "roku" not in st.lower() and "roku" not in location.lower():
                    # still accept LOCATION pointing at :8060
                    if ":8060" not in location:
                        continue
                host = _host_from_location(location)
                if not host:
                    continue
                found[host] = {
                    "host": host,
                    "location": location,
                    "usn": headers.get("usn", ""),
                    "st": st or SSDP_ST,
                }
                if deadline is None:
                    # single-response mode when no time module
                    break
        finally:
            try:
                sock.close()
            except OSError:
                pass

    return list(found.values())


class RokuEngine:
    """Stateful ECP client for one Roku target."""

    def __init__(self, host=None, port=ROKU_PORT, timeout=5.0):
        self.host = host if host is not None else ROKU_HOST
        self.port = int(port)
        self.timeout = float(timeout)
        self.last_error = ""
        self.connected = False
        self.device_info = {}
        self.apps = []
        self.active_app = {}
        self.media_player = ""
        self.discovered = []
        # Optional inject for tests: callable(method, url, timeout, data) -> (status, body)
        self._http = None

    def set_host(self, host, port=None):
        self.host = (host or "").strip()
        if port is not None:
            self.port = int(port)
        self.connected = False
        self.last_error = ""

    @property
    def base_url(self):
        return "http://%s:%d" % (self.host, self.port)

    @property
    def status(self):
        if self.last_error:
            return "err: " + self.last_error
        if not self.host:
            return "no host"
        if not self.connected:
            return "offline " + self.host
        name = self.device_info.get("user-device-name") or self.device_info.get(
            "model-name", ""
        )
        app = self.active_app.get("name", "")
        bits = [self.host]
        if name:
            bits.append(name)
        if app:
            bits.append(app)
        return " | ".join(bits)

    def _request(self, method, path, data=b""):
        if not self.host:
            self.last_error = "no host"
            return 0, b""
        url = self.base_url + path
        try:
            if self._http is not None:
                status, body = self._http(method, url, self.timeout, data)
            else:
                status, body = http_request(method, url, timeout=self.timeout, data=data)
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            return 0, b""
        if status and status >= 400:
            self.last_error = "HTTP %d %s" % (status, path)
        else:
            self.last_error = ""
        return status, body

    def discover(self, timeout=3.0, retries=2):
        try:
            self.discovered = discover_rokus(timeout=timeout, retries=retries)
            self.last_error = "" if self.discovered else "no Roku found"
        except Exception as e:
            self.discovered = []
            self.last_error = str(e)
        return self.discovered

    def connect(self, discover_if_empty=True):
        """Ping device-info. If host empty and discover_if_empty, SSDP first."""
        if not self.host and discover_if_empty:
            devices = self.discover()
            if devices:
                self.set_host(devices[0]["host"])
        if not self.host:
            self.last_error = "no host"
            self.connected = False
            return False
        info = self.query_device_info()
        self.connected = bool(info)
        if self.connected:
            try:
                self.query_active_app()
            except Exception:
                pass
        return self.connected

    def press(self, key):
        if key not in ECP_KEY_SET and not str(key).startswith("Lit_"):
            self.last_error = "unknown key: " + str(key)
            return False
        status, _ = self._request("POST", "/keypress/" + key, b"")
        return 200 <= status < 300 or status == 200

    def keydown(self, key):
        status, _ = self._request("POST", "/keydown/" + key, b"")
        return 200 <= status < 300

    def keyup(self, key):
        status, _ = self._request("POST", "/keyup/" + key, b"")
        return 200 <= status < 300

    def type_text(self, text):
        ok = True
        for ch in text:
            lit = "Lit_" + _quote_lit(ch)
            if not self.press(lit):
                ok = False
        return ok

    def launch(self, app_id, query=""):
        path = "/launch/" + str(app_id)
        if query:
            path += ("&" if "?" in query else "?") + query.lstrip("?&")
        status, _ = self._request("POST", path, b"")
        return 200 <= status < 300

    def install(self, app_id):
        status, _ = self._request("POST", "/install/" + str(app_id), b"")
        return 200 <= status < 300

    def input_params(self, params):
        """POST /input?k=v&... custom events to the current app."""
        if isinstance(params, dict):
            parts = []
            for k, v in params.items():
                parts.append("%s=%s" % (k, v))
            qs = "&".join(parts)
        else:
            qs = str(params).lstrip("?")
        status, _ = self._request("POST", "/input?" + qs, b"")
        return 200 <= status < 300

    def query_device_info(self):
        status, body = self._request("GET", "/query/device-info")
        if not body or status >= 400:
            self.device_info = {}
            return {}
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        info = {}
        for tag in (
            "udn",
            "serial-number",
            "device-id",
            "vendor-name",
            "model-name",
            "model-number",
            "model-region",
            "is-tv",
            "is-stick",
            "user-device-name",
            "software-version",
            "software-build",
            "power-mode",
            "network-type",
            "network-name",
            "supports-find-remote",
            "supports-audio-volume-control",
            "supports-tv-power-control",
            "supports-ethernet",
            "wifi-mac",
            "ethernet-mac",
        ):
            val = _xml_tag(text, tag)
            if val:
                info[tag] = val
        self.device_info = info
        return info

    def query_apps(self):
        status, body = self._request("GET", "/query/apps")
        if not body or status >= 400:
            self.apps = []
            return []
        self.apps = _parse_apps(body)
        return self.apps

    def query_active_app(self):
        status, body = self._request("GET", "/query/active-app")
        if not body or status >= 400:
            self.active_app = {}
            return {}
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        # <app id="12">Netflix</app> or screensaver sibling
        apps = _parse_apps(text)
        if apps:
            self.active_app = apps[0]
        else:
            name = _xml_tag(text, "app")
            self.active_app = {"id": "", "name": name} if name else {}
        return self.active_app

    def query_media_player(self):
        status, body = self._request("GET", "/query/media-player")
        if not body or status >= 400:
            self.media_player = ""
            return ""
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        self.media_player = text.strip()
        return self.media_player

    def query_tv_channels(self):
        status, body = self._request("GET", "/query/tv-channels")
        if not body or status >= 400:
            return ""
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def query_tv_active_channel(self):
        status, body = self._request("GET", "/query/tv-active-channel")
        if not body or status >= 400:
            return ""
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def query_icon(self, app_id):
        """Return raw icon bytes (PNG/JPEG) or b''."""
        status, body = self._request("GET", "/query/icon/" + str(app_id))
        if not body or status >= 400:
            return b""
        return body

    # --- Developer-mode helpers (engine API; light UI dump) ---

    def query_raw(self, path):
        """GET an arbitrary ECP path; return decoded text or ''."""
        if not path.startswith("/"):
            path = "/" + path
        status, body = self._request("GET", path)
        if not body:
            return ""
        if isinstance(body, bytes):
            try:
                return body.decode("utf-8")
            except UnicodeError:
                return repr(body[:80])
        return body

    def query_chanperf(self, duration_seconds=None):
        path = "/query/chanperf"
        if duration_seconds is not None:
            path += "?duration-seconds=" + str(duration_seconds)
        return self.query_raw(path)

    def query_sgnodes(self, which="all"):
        return self.query_raw("/query/sgnodes/" + which)

    def query_registry(self, channel_id="dev"):
        return self.query_raw("/query/registry/" + str(channel_id))

    def query_graphics_frame_rate(self):
        return self.query_raw("/query/graphics-frame-rate")

    def query_app_state(self, app_id):
        return self.query_raw("/query/app-state/" + str(app_id))

    def query_app_object_counts(self, app_id):
        return self.query_raw("/query/app-object-counts/" + str(app_id))

    def exit_app(self, force=False):
        path = "/exit-app"
        if force:
            path += "/true"
        status, _ = self._request("POST", path, b"")
        return 200 <= status < 300

    def fwbeacons_track(self, channel_id=None):
        path = "/fwbeacons/track"
        if channel_id:
            path += "/" + str(channel_id)
        status, _ = self._request("POST", path, b"")
        return 200 <= status < 300

    def fwbeacons_untrack(self):
        status, _ = self._request("POST", "/fwbeacons/untrack", b"")
        return 200 <= status < 300

    def query_fwbeacons(self):
        return self.query_raw("/query/fwbeacons")

    def sgrendezvous_track(self, channel_id=None):
        path = "/query/sgrendezvous/track"
        if channel_id:
            path += "/" + str(channel_id)
        status, _ = self._request("POST", path, b"")
        return 200 <= status < 300

    def sgrendezvous_untrack(self):
        status, _ = self._request("POST", "/query/sgrendezvous/untrack", b"")
        return 200 <= status < 300

    def query_sgrendezvous(self):
        return self.query_raw("/query/sgrendezvous")

    def query_r2d2_bitmaps(self):
        return self.query_raw("/query/r2d2-bitmaps")

    def is_tv(self):
        return str(self.device_info.get("is-tv", "")).lower() in ("true", "1")

    def supports_volume(self):
        return str(self.device_info.get("supports-audio-volume-control", "")).lower() in (
            "true",
            "1",
        ) or self.is_tv()


# MicroPython-friendly: avoid dataclass / typing
if __name__ == "__main__":
    eng = RokuEngine()
    print("discover:", eng.discover())
    if eng.discovered:
        eng.set_host(eng.discovered[0]["host"])
        print("connect:", eng.connect())
        print("status:", eng.status)
        print("apps:", len(eng.query_apps()))
    else:
        print("last_error:", eng.last_error, file=sys.stderr)
