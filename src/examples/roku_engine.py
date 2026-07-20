# gallery: skip
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`roku_engine`
====================================================

Roku External Control Protocol (ECP) client — no display, event, or UI imports.

Talks HTTP on port 8060 and discovers devices via SSDP (``ST: roku:ecp``),
with a portable unicast ``:8060`` / ``/query/device-info`` scan fallback when
multicast is blocked (common on WSL NAT and some host firewalls).
Shared by every Roku front end (``roku_graphics``, ``roku_widgets``,
``roku_lvgl``, and the ``roku_remote`` launcher): all UI-agnostic ECP,
discovery, and label/action helpers live here so the display layer is fully
replaceable.

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
    "ClosedCaption",
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


def _xml_unescape(text):
    """Decode common XML entities (``&amp;`` → ``&``, etc.)."""
    if not text:
        return ""
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&apos;", "'")
    return text


def ascii_label(text):
    """Unescape XML, then replace non-ASCII / control chars with spaces.

    UI-agnostic helper shared by the front ends for safe single-line labels on
    bitmap fonts. Kept in the engine so ``roku_graphics`` / ``roku_widgets`` /
    ``roku_lvgl`` render identical device / app text.
    """
    out = []
    for ch in _xml_unescape(text or ""):
        o = ord(ch)
        out.append(ch if 32 <= o <= 126 else " ")
    return "".join(out)


def _parse_media_player(text):
    """Parse ``/query/media-player`` XML into a small state dict."""
    if not text:
        return {}
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeError:
            text = str(text)
    i = text.find("<player")
    if i < 0:
        return {}
    gt = text.find(">", i)
    if gt < 0:
        return {}
    attrs = _xml_attrs(text[i : gt + 1])
    plugin = {}
    pi = text.find("<plugin", i)
    if pi >= 0:
        pgt = text.find(">", pi)
        if pgt >= 0:
            plugin = _xml_attrs(text[pi : pgt + 1])
    fmt = {}
    fi = text.find("<format", i)
    if fi >= 0:
        fgt = text.find(">", fi)
        if fgt >= 0:
            fmt = _xml_attrs(text[fi : fgt + 1])
    return {
        "state": attrs.get("state", "") or "",
        "error": attrs.get("error", "") or "",
        "app": _xml_unescape(plugin.get("name", "") or ""),
        "app_id": plugin.get("id", "") or "",
        "captions": (fmt.get("captions", "") or "").lower(),
        "video": (fmt.get("video", "") or "").lower(),
        "audio": (fmt.get("audio", "") or "").lower(),
        "drm": (fmt.get("drm", "") or "").lower(),
    }


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
        name = _xml_unescape(xml_text[gt + 1 : close_i].strip())
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


def _parse_http_url(url):
    """Split ``http://host[:port]/path`` → (host, port, path)."""
    u = url
    if "://" in u:
        scheme, u = u.split("://", 1)
        if scheme.lower() != "http":
            raise ValueError("only http:// URLs supported")
    hostport, path = (u.split("/", 1) + [""])[:2]
    path = "/" + path
    if hostport.startswith("["):
        end = hostport.find("]")
        if end < 0:
            raise ValueError("bad IPv6 URL host")
        host = hostport[1:end]
        rest = hostport[end + 1 :]
        port = int(rest[1:]) if rest.startswith(":") else 80
    elif ":" in hostport:
        host, port_s = hostport.rsplit(":", 1)
        port = int(port_s)
    else:
        host, port = hostport, 80
    return host, port, path


def _http_request_socket(method, url, timeout=5.0, data=b""):
    """Minimal HTTP/1.0 over ``socket`` (no urllib/urequests required)."""
    host, port, path = _parse_http_url(url)
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif data is None:
        data = b""
    req = "%s %s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n" % (
        method,
        path,
        host if port == 80 else "%s:%d" % (host, port),
    )
    if method != "GET" or data:
        req += "Content-Length: %d\r\n" % len(data)
    req += "\r\n"
    payload = req.encode("utf-8") + data

    addr = _sockaddr(host, port, socket.SOCK_STREAM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        try:
            sock.settimeout(timeout)
        except OSError:
            pass
        sock.connect(addr)
        view = memoryview(payload)
        sent = 0
        while sent < len(payload):
            n = sock.send(view[sent:])
            if n is None or n <= 0:
                break
            sent += n

        chunks = []
        while True:
            try:
                chunk = sock.recv(2048)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        try:
            sock.close()
        except OSError:
            pass

    raw = b"".join(chunks) if chunks else b""
    sep = raw.find(b"\r\n\r\n")
    if sep < 0:
        raise RuntimeError("HTTP response missing header separator")
    header_blob = raw[:sep]
    body = raw[sep + 4 :]
    status_line = header_blob.split(b"\r\n", 1)[0]
    parts = status_line.split(b" ", 2)
    try:
        status = int(parts[1]) if len(parts) >= 2 else 0
    except (ValueError, IndexError):
        status = 0
    # Honor Content-Length when present (ignore trailers / keep-alive noise).
    for line in header_blob.split(b"\r\n")[1:]:
        if line.lower().startswith(b"content-length:"):
            try:
                clen = int(line.split(b":", 1)[1].strip())
            except (ValueError, IndexError):
                break
            if clen >= 0:
                body = body[:clen]
            break
    return status, body


def http_request(method, url, timeout=5.0, data=None):
    """
    Portable HTTP GET/POST → (status_code, body_bytes).

    Tries urllib, then urequests/requests, then a minimal socket client
    (needed on Windows MicroPython where ``~`` in ``sys.path`` is not
    expanded and host ``urequests`` is often missing).
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

    try:
        return _http_request_socket(method, url, timeout=timeout, data=body)
    except Exception as e:
        raise RuntimeError("HTTP via socket failed: " + str(e)) from e


def _sockaddr(host, port, socktype=socket.SOCK_STREAM):
    """Resolve ``(host, port)`` to a stack sockaddr (tuple or buffer).

    MicroPython unix ``connect`` / ``sendto`` often require the sockaddr from
    ``getaddrinfo`` (a ``bytearray``), not a plain ``(host, port)`` tuple.
    """
    try:
        return socket.getaddrinfo(host, port, socket.AF_INET, socktype)[0][-1]
    except Exception:
        return (host, port)


def _local_ipv4_from_fib_trie():
    """Linux ``/proc/net/fib_trie`` host LOCAL addresses (MicroPython unix)."""
    try:
        f = open("/proc/net/fib_trie")
    except OSError:
        return ""
    try:
        lines = f.read().split("\n")
    finally:
        try:
            f.close()
        except Exception:
            pass
    in_local = False
    candidates = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Local:"):
            in_local = True
            i += 1
            continue
        if in_local and (line.startswith("Main:") or line.startswith("Id ")):
            break
        if in_local and "|--" in line:
            part = line.split("|--", 1)[-1].strip().split()[0]
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if "/32 host LOCAL" in nxt:
                bits = part.split(".")
                if len(bits) == 4:
                    try:
                        a = int(bits[0])
                        d = int(bits[3])
                    except ValueError:
                        i += 1
                        continue
                    # Skip loopback / network / broadcast; WSL DNS stub.
                    if a != 127 and d not in (0, 255) and part != "10.255.255.254":
                        candidates.append(part)
        i += 1
    for ip in candidates:
        if ip.startswith("192.168.") or ip.startswith("10."):
            return ip
        parts = ip.split(".")
        if len(parts) == 4:
            try:
                a, b = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if a == 172 and 16 <= b <= 31:
                return ip
    return candidates[0] if candidates else ""


def _prefix_from_default_route():
    """``/24`` of the default gateway from ``/proc/net/route`` (Linux)."""
    try:
        f = open("/proc/net/route")
    except OSError:
        return ""
    try:
        next(f)
        for line in f:
            parts = line.split()
            if len(parts) < 3 or parts[1] != "00000000":
                continue
            try:
                g = int(parts[2], 16)
            except ValueError:
                continue
            return "%d.%d.%d" % (g & 255, (g >> 8) & 255, (g >> 16) & 255)
    except Exception:
        return ""
    finally:
        try:
            f.close()
        except Exception:
            pass
    return ""


def _valid_station_ipv4(ip):
    """True for a usable unicast IPv4 (not empty / 0.0.0.0 / APIPA)."""
    if not ip or ip == "0.0.0.0" or str(ip).startswith("169.254"):
        return False
    parts = str(ip).split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _local_ipv4_from_wlan():
    """MicroPython STA ifconfig — works when UDP getsockname is empty (esp-hosted)."""
    try:
        import network
    except ImportError:
        return ""
    try:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.active() or not wlan.isconnected():
            return ""
        ip = wlan.ifconfig()[0]
        return ip if _valid_station_ipv4(ip) else ""
    except Exception:
        return ""


def _ipv4_from_sockname(name):
    """Extract dotted IPv4 from CPython ``(host, port)`` or MicroPython sockaddr bytes."""
    if isinstance(name, (tuple, list)) and name:
        host = name[0]
        if isinstance(host, str) and _valid_station_ipv4(host):
            return host
        # socket.sockaddr() → (AF_INET, addr_bytes, port)
        if (
            len(name) >= 2
            and isinstance(name[1], (bytes, bytearray))
            and len(name[1]) >= 4
        ):
            b = name[1]
            return "%d.%d.%d.%d" % (b[0], b[1], b[2], b[3])
    if isinstance(name, (bytes, bytearray)) and hasattr(socket, "sockaddr"):
        try:
            return _ipv4_from_sockname(socket.sockaddr(name))
        except (OSError, ValueError, TypeError, IndexError):
            pass
    return ""


def _local_ipv4():
    """Best-effort primary IPv4 (UDP connect + getsockname, WLAN, else Linux proc)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(_sockaddr("8.8.8.8", 80, socket.SOCK_DGRAM))
            if hasattr(s, "getsockname"):
                ip = _ipv4_from_sockname(s.getsockname())
                if _valid_station_ipv4(ip):
                    return ip
        finally:
            s.close()
    except (OSError, AttributeError, ValueError, TypeError, IndexError):
        pass
    ip = _local_ipv4_from_wlan()
    if ip:
        return ip
    return _local_ipv4_from_fib_trie()


def _prefix24(ip):
    parts = (ip or "").split(".")
    if len(parts) != 4:
        return ""
    return "%s.%s.%s" % (parts[0], parts[1], parts[2])


def _windows_lan_prefixes():
    """
    Extra /24 prefixes from the Windows host (WSL NAT is not the LAN).

    Uses powershell.exe when present; empty on MCU / plain Linux.
    """
    try:
        import subprocess
    except ImportError:
        return []
    try:
        out = subprocess.check_output(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "Get-NetIPAddress -AddressFamily IPv4 | "
                "Where-Object { $_.IPAddress -notlike '127.*' "
                "-and $_.InterfaceAlias -notmatch 'WSL|vEthernet|Loopback|Bluetooth' } | "
                "Select-Object -ExpandProperty IPAddress",
            ],
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
    except Exception:
        return []
    if isinstance(out, bytes):
        try:
            out = out.decode("utf-8", "replace")
        except Exception:
            out = out.decode("latin-1")
    prefixes = []
    for line in out.replace("\r", "\n").split("\n"):
        p = _prefix24(line.strip())
        # Skip APIPA / link-local — not useful for LAN Roku discovery.
        if not p or p.startswith("169.254"):
            continue
        if p not in prefixes:
            prefixes.append(p)
    return prefixes


def _is_wsl_nat_ipv4(ip):
    """True when this looks like Hyper-V WSL NAT (not mirrored LAN)."""
    parts = (ip or "").split(".")
    if len(parts) != 4:
        return False
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    # WSL2 NAT is commonly 172.16–31.x; mirrored mode uses the real LAN IP.
    if not (a == 172 and 16 <= b <= 31):
        return False
    try:
        with open("/proc/version") as f:
            ver = f.read().lower()
        return "microsoft" in ver or "wsl" in ver
    except Exception:
        return False


def _scan_prefixes():
    """IPv4 /24 bases to probe for ECP (LAN prefixes preferred over WSL NAT)."""
    prefixes = []
    local_ip = _local_ipv4()
    local = _prefix24(local_ip)
    if local and not local.startswith("169.254"):
        prefixes.append(local)
    route = _prefix_from_default_route()
    if route and route not in prefixes and not route.startswith("169.254"):
        prefixes.append(route)
    # Only shell out to Windows when still on WSL NAT — mirrored LAN already
    # shares the Wi-Fi /24 and powershell during discover blocks the UI.
    if _is_wsl_nat_ipv4(local_ip) or not prefixes:
        for p in _windows_lan_prefixes():
            if p not in prefixes:
                prefixes.insert(0, p)
    return prefixes


def _tcp_open(host, port, timeout=0.25):
    """True if TCP connect to host:port succeeds (MP/CPython portable)."""
    s = None
    try:
        addr = _sockaddr(host, port, socket.SOCK_STREAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(addr)
        return True
    except (OSError, TypeError, ValueError, IndexError):
        return False
    finally:
        if s is not None:
            try:
                s.close()
            except OSError:
                pass


def _tcp_open_retry(host, port, timeout=1.0, attempts=2):
    """Retry flaky ECP listeners (some Rokus miss a single short connect)."""
    for _ in range(max(1, int(attempts))):
        if _tcp_open(host, port, timeout):
            return True
    return False


def _ecp_device(host, port=ROKU_PORT, timeout=1.5):
    """Return discovery dict if host speaks Roku ECP, else None."""
    try:
        status, body = http_request(
            "GET", "http://%s:%d/query/device-info" % (host, port), timeout=timeout
        )
    except Exception:
        return None
    if not status or status >= 400 or not body:
        return None
    if b"device-info" not in body and b"<device-info" not in body:
        return None
    text = body
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeError:
            text = text.decode("latin-1")
    name = (
        _xml_tag(text, "user-device-name")
        or _xml_tag(text, "friendly-device-name")
        or _xml_tag(text, "model-name")
        or host
    )
    return {
        "host": host,
        "name": name,
        "location": "http://%s:%d/" % (host, port),
        "usn": "",
        "st": "scan:ecp",
    }


def _default_scan_workers():
    """Fewer parallel connects on ``network`` STA targets (esp-hosted / MCU)."""
    try:
        import network  # noqa: F401

        return 4
    except ImportError:
        return 24


def _probe_hosts_poll(hosts, port, connect_timeout, batch_size=32):
    """Parallel TCP probe via ``select.poll`` (no threads — Windows MP)."""
    import select

    if not hasattr(select, "poll"):
        raise ImportError("select.poll")
    timeout_ms = max(50, int(float(connect_timeout) * 1000))
    batch_size = max(1, int(batch_size))
    open_hosts = []
    poll_mask = select.POLLOUT
    for attr in ("POLLERR", "POLLHUP"):
        poll_mask |= getattr(select, attr, 0)

    for i in range(0, len(hosts), batch_size):
        batch = hosts[i : i + batch_size]
        poller = select.poll()
        socks = {}  # canonical key id(sock) -> (host, sock)
        fd_to_key = {}  # fileno -> id(sock): CPython poll() returns int fds
        for host in batch:
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.setblocking(False)
                except (OSError, AttributeError):
                    s.settimeout(0)
                addr = _sockaddr(host, port, socket.SOCK_STREAM)
                try:
                    s.connect(addr)
                    # Immediate success (rare)
                    if hasattr(s, "getpeername"):
                        s.getpeername()
                        open_hosts.append(host)
                        s.close()
                        continue
                except OSError:
                    pass
                socks[id(s)] = (host, s)
                try:
                    fd_to_key[s.fileno()] = id(s)
                except (AttributeError, OSError):
                    pass
                poller.register(s, poll_mask)
            except (OSError, TypeError, ValueError, IndexError):
                if s is not None:
                    try:
                        s.close()
                    except OSError:
                        pass

        pending = set(socks)
        # Portable per-batch deadline (ticks on MCU, wall clock on CPython).
        # Prior code only armed a deadline when ``time.ticks_ms`` existed, so on
        # CPython the loop had no timeout and filtered hosts (no RST, no connect)
        # kept ``pending`` non-empty forever, hanging the whole scan.
        deadline = _monotonic_deadline_ms(connect_timeout)
        # Fallback bound for runtimes with no clock at all.
        max_iters = max(1, timeout_ms // 50 + 2)
        iters = 0
        while pending:
            if deadline is not None:
                if _monotonic_expired(deadline):
                    break
            elif iters >= max_iters:
                break
            iters += 1
            try:
                ready = poller.poll(50)
            except OSError:
                break
            for item in ready:
                obj = item[0]
                # CPython poll() yields int fds; MicroPython yields the socket.
                if isinstance(obj, int):
                    key = fd_to_key.get(obj)
                else:
                    key = id(obj)
                if key is None or key not in socks:
                    continue
                host, s = socks[key]
                ok = False
                try:
                    if hasattr(s, "getpeername"):
                        s.getpeername()
                        ok = True
                except OSError:
                    ok = False
                if ok:
                    open_hosts.append(host)
                try:
                    poller.unregister(s)
                except (OSError, KeyError, ValueError):
                    pass
                try:
                    s.close()
                except OSError:
                    pass
                pending.discard(key)
                del socks[key]

        for key in list(pending):
            host, s = socks[key]
            try:
                poller.unregister(s)
            except (OSError, KeyError, ValueError):
                pass
            try:
                s.close()
            except OSError:
                pass
    return open_hosts


def _probe_hosts_parallel(hosts, port, connect_timeout, workers=None):
    """Return hosts with open TCP ``port``.

    Prefers ``select.poll`` (works without ``_thread`` — Windows MicroPython),
    then CPython futures / MP ``_thread``, then sequential connects.
    """
    if workers is None:
        workers = _default_scan_workers()
    n_workers = max(1, int(workers))

    # Non-threaded parallel path first — Windows MP has no ``_thread``.
    try:
        return _probe_hosts_poll(
            hosts, port, connect_timeout, batch_size=max(8, n_workers)
        )
    except (ImportError, AttributeError, OSError):
        pass

    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        open_hosts = []
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futs = {
                pool.submit(_tcp_open, host, port, connect_timeout): host
                for host in hosts
            }
            for fut in as_completed(futs):
                host = futs[fut]
                try:
                    ok = fut.result()
                except Exception:
                    ok = False
                if ok:
                    open_hosts.append(host)
        return open_hosts
    except ImportError:
        pass

    try:
        import _thread
    except ImportError:
        return [h for h in hosts if _tcp_open(h, port, connect_timeout)]

    # MicroPython: no concurrent.futures — small _thread pool.
    # Chunk large /24 lists; a single 254-host wait can hang on esp-hosted.
    chunk = 32
    if len(hosts) > chunk:
        open_all = []
        for i in range(0, len(hosts), chunk):
            open_all.extend(
                _probe_hosts_parallel(
                    hosts[i : i + chunk], port, connect_timeout, n_workers
                )
            )
        return open_all

    queue = list(hosts)
    qi = [0]
    qlock = _thread.allocate_lock()
    rlock = _thread.allocate_lock()
    open_hosts = []
    remaining = [len(queue)]

    def _worker():
        while True:
            with qlock:
                if qi[0] >= len(queue):
                    return
                host = queue[qi[0]]
                qi[0] += 1
            try:
                ok = _tcp_open(host, port, connect_timeout)
            except Exception:
                ok = False
            with rlock:
                if ok:
                    open_hosts.append(host)
                remaining[0] -= 1

    started = 0
    for _ in range(min(n_workers, max(1, len(queue)))):
        try:
            _thread.start_new_thread(_worker, ())
            started += 1
        except Exception:
            break
    if started == 0:
        return [h for h in hosts if _tcp_open(h, port, connect_timeout)]
    # Bound wait so a stuck connect cannot freeze discovery forever.
    deadline = None
    if time is not None and hasattr(time, "ticks_ms"):
        per = max(50, int(float(connect_timeout) * 1000))
        slack = ((len(queue) + started - 1) // started) * per + 5000
        deadline = time.ticks_add(time.ticks_ms(), slack)
    while remaining[0] > 0:
        if deadline is not None and time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            break
        if time is not None:
            try:
                time.sleep(0.05)
            except Exception:
                pass
    return open_hosts


def discover_rokus_scan(
    prefixes=None,
    port=ROKU_PORT,
    connect_timeout=1.0,
    priority_hosts=None,
    workers=None,
    on_device=None,
):
    """
    Unicast scan: TCP :8060 then GET /query/device-info.

    Portable fallback when SSDP multicast is blocked (WSL NAT, host firewall).
    No third-party dependency. Parallel via ``select.poll`` (no threads),
    ``concurrent.futures`` (CPython), or ``_thread``; sequential only if none.

    ``connect_timeout`` defaults to 1.0s. Keep ``workers`` modest — 64-way
    floods drop some Rokus that answer fine alone (seen with a 65" TCL).
    On MicroPython ``network`` targets the default is 4 workers.
    ``priority_hosts`` are probed first with a longer retry (rescans).
    ``on_device(info)`` is called as each ECP device is confirmed (progressive UI).
    Asleep sets typically close ECP and will not appear.
    """
    if workers is None:
        workers = _default_scan_workers()
    if prefixes is None:
        prefixes = _scan_prefixes()
    priority_hosts = tuple(priority_hosts or ())
    if not prefixes and not priority_hosts:
        return []

    hosts = []
    for prefix in prefixes:
        for i in range(1, 255):
            hosts.append("%s.%d" % (prefix, i))

    found = []
    found_hosts = {}

    def _accept(host):
        if host in found_hosts:
            return None
        info = _ecp_device(host, port=port)
        if not info:
            return None
        found_hosts[host] = True
        found.append(info)
        if on_device is not None:
            try:
                on_device(info)
            except Exception:
                pass
        return info

    seen = {}
    # Prefer previously-found IPs — full-subnet floods can miss flaky listeners.
    for host in priority_hosts:
        host = (host or "").strip()
        if not host or host in seen:
            continue
        seen[host] = True
        if _tcp_open_retry(host, port, max(connect_timeout, 1.5), 3):
            _accept(host)

    if found:
        return found

    rest = [h for h in hosts if h not in seen]
    # Probe in worker-sized chunks and confirm ECP between chunks so a present
    # Roku short-circuits the remaining /24 (fast discovery) without raising the
    # socket fan-out, which is known to drop real Rokus.
    step = max(8, int(workers))
    for i in range(0, len(rest), step):
        chunk = rest[i : i + step]
        for host in _probe_hosts_parallel(chunk, port, connect_timeout, workers):
            _accept(host)
        if found:
            break

    return found


def _monotonic_deadline_ms(seconds):
    """End tick for a relative wait (avoids SNTP steps breaking ``time.time()``)."""
    if time is None:
        return None
    ms = max(1, int(float(seconds) * 1000))
    if hasattr(time, "ticks_ms") and hasattr(time, "ticks_add"):
        return time.ticks_add(time.ticks_ms(), ms)
    # CPython: no ticks_ms — wall clock is normally fine there.
    return ("wall", time.time() + float(seconds))


def _monotonic_expired(deadline):
    if deadline is None:
        return False
    if isinstance(deadline, tuple) and deadline and deadline[0] == "wall":
        return time.time() >= deadline[1]
    if time is not None and hasattr(time, "ticks_diff"):
        return time.ticks_diff(deadline, time.ticks_ms()) <= 0
    return False


def discover_rokus(timeout=3.0, retries=2, scan_fallback=True, ssdp=True):
    """
    Discover Roku ECP devices.

    Returns a list of dicts: ``{host, location, usn, st[, name]}``.

    SSDP M-SEARCH when ``ssdp`` is true. If that finds nothing (or ``ssdp`` is
    false) and ``scan_fallback`` is true, unicast-scans /24 subnets for ECP on
    port 8060. SSDP wait uses a monotonic tick deadline — wall ``time.time()``
    is unsafe on MCU targets where SNTP steps the clock during discovery.
    Prefer ``ssdp=False`` from UI threads that share multimer soft timers if
    blocking ``recvfrom`` + timer re-entry deadlocks under librt.
    """
    devices = []
    if ssdp:
        message = (
            "M-SEARCH * HTTP/1.1\r\n"
            "HOST: %s:%d\r\n"
            'MAN: "ssdp:discover"\r\n'
            "ST: %s\r\n"
            "MX: 2\r\n"
            "\r\n"
        ) % (SSDP_ADDR, SSDP_PORT, SSDP_ST)

        found = {}
        deadline = _monotonic_deadline_ms(timeout)
        # Once a Roku replies, keep listening only a short grace window so
        # multicast discovery returns in ~1s instead of burning the full
        # timeout waiting for more replies that rarely come.
        grace_deadline = [None]
        grace_secs = 0.6

        for _ in range(max(1, int(retries))):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                except (OSError, AttributeError):
                    pass
                # Multicast TTL: Linux IP_MULTICAST_TTL=33; Winsock=10 (IPPROTO_IP=0).
                for ttl_opt in (
                    getattr(socket, "IP_MULTICAST_TTL", None),
                    33,
                    10,
                ):
                    if ttl_opt is None:
                        continue
                    try:
                        sock.setsockopt(0, ttl_opt, 2)
                        break
                    except (OSError, AttributeError):
                        pass
                try:
                    # Winsock often needs an explicit bind before multicast replies arrive.
                    sock.bind(_sockaddr("0.0.0.0", 0, socket.SOCK_DGRAM))
                except (OSError, AttributeError, TypeError):
                    pass
                try:
                    sock.settimeout(0.4)
                except OSError:
                    pass

                payload = message.encode("utf-8") if isinstance(message, str) else message
                try:
                    sock.sendto(
                        payload, _sockaddr(SSDP_ADDR, SSDP_PORT, socket.SOCK_DGRAM)
                    )
                except (OSError, TypeError) as e:
                    sock.close()
                    raise RuntimeError("SSDP send failed: " + str(e)) from e

                while True:
                    if _monotonic_expired(deadline):
                        break
                    if grace_deadline[0] is not None and _monotonic_expired(
                        grace_deadline[0]
                    ):
                        break
                    try:
                        data, _addr = sock.recvfrom(2048)
                    except OSError:
                        if deadline is None:
                            break
                        if _monotonic_expired(deadline):
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
                    if grace_deadline[0] is None:
                        grace_deadline[0] = _monotonic_deadline_ms(grace_secs)
                    if deadline is None:
                        # single-response mode when no time module
                        break
            finally:
                try:
                    sock.close()
                except OSError:
                    pass
            if (
                found
                and grace_deadline[0] is not None
                and _monotonic_expired(grace_deadline[0])
            ):
                break

        devices = list(found.values())
    if devices or not scan_fallback:
        return devices
    return discover_rokus_scan()


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
        self.active_screensaver = ""
        self.media_player = ""
        self.media_state = {}
        self.discovered = []
        # Optional inject for tests: callable(method, url, timeout, data) -> (status, body)
        self._http = None

    def set_host(self, host, port=None):
        self.host = (host or "").strip()
        if port is not None:
            self.port = int(port)
        self.connected = False
        self.last_error = ""
        # Host-specific caches must not survive a TV switch.
        self.apps = []
        self.active_app = {}
        self.active_screensaver = ""
        self.device_info = {}
        self.media_player = ""
        self.media_state = {}

    @property
    def base_url(self):
        return "http://%s:%d" % (self.host, self.port)

    def power_is_on(self):
        """True when ``power-mode`` from device-info is ``PowerOn``."""
        mode = (self.device_info or {}).get("power-mode") or ""
        return mode == "PowerOn"

    def inputs(self):
        """TV tuner / HDMI / AV entries from the last apps query (``type=tvin``)."""
        out = []
        for app in self.apps or []:
            if (app.get("type") or "").lower() == "tvin":
                out.append(app)
        return out

    def media_active(self):
        """True when media-player reports play / pause / buffer."""
        state = ((self.media_state or {}).get("state") or "").lower()
        return state in ("play", "pause", "buffer")

    def captions_track_hint(self):
        """True when format reports a captions value other than ``none``/empty."""
        cap = ((self.media_state or {}).get("captions") or "").lower()
        return bool(cap) and cap not in ("none", "off", "false")

    def playback_status(self):
        """Short ASCII status from active-app + media-player (for the UI banner)."""
        if self.last_error and not self.connected:
            return "err: " + self.last_error
        if not self.host:
            return "no host"
        if not self.connected:
            return "offline"
        if not self.power_is_on():
            return "OFF"
        ms = self.media_state or {}
        app = (
            (self.active_app or {}).get("name")
            or ms.get("app")
            or ""
        )
        saver = (self.active_screensaver or "").strip()
        state = (ms.get("state") or "").lower()
        bits = []
        if saver:
            # Screensaver sibling from active-app (home or over an app).
            app_l = app.lower()
            if not app or app_l in ("roku", "home"):
                bits.append("screensaver")
            else:
                bits.append(app)
                bits.append("screensaver")
            return " ".join(bits)
        if app:
            bits.append(app)
        if state and state not in ("", "close", "none", "stop"):
            bits.append(state)
        if bits:
            return " ".join(bits)
        name = self.device_info.get("user-device-name") or self.device_info.get(
            "model-name", ""
        )
        return name or "ready"

    def refresh_playback(self):
        """Query active-app + media-player; return ``playback_status()``."""
        try:
            self.query_active_app()
        except Exception:
            pass
        try:
            self.query_media_player()
        except Exception:
            pass
        return self.playback_status()

    # --- Presentation helpers (UI-agnostic strings from engine state) ------

    def play_label(self):
        """Transport Play/Pause caption from media-player state.

        ``PAUSE`` while playing/buffering, ``PLAY`` while paused, else ``P/PA``.
        """
        state = ((self.media_state or {}).get("state") or "").lower()
        if state in ("play", "buffer"):
            return "PAUSE"
        if state == "pause":
            return "PLAY"
        return "P/PA"

    def power_label(self):
        """``ON`` / ``OFF`` for the power key face, from ``power-mode``."""
        return "ON" if self.power_is_on() else "OFF"

    def power_key(self):
        """The ECP key that toggles power from the current state."""
        return "PowerOff" if self.power_is_on() else "PowerOn"

    def input_short_label(self, app, max_chars=4):
        """Short ASCII label for a ``type=tvin`` input (TV / H1 / H2 / AV / …)."""
        aid = (app.get("id") or "").lower()
        name = ascii_label(app.get("name") or "").strip()
        lab = ""
        if "dtv" in aid or "tuner" in aid or name.upper() in ("LIVE TV", "TV"):
            lab = "TV"
        elif "hdmi" in aid:
            for ch in aid:
                if ch.isdigit():
                    lab = "H" + ch
                    break
            if not lab:
                lab = "HDMI"
        elif "cvbs" in aid or "av" in aid:
            lab = "AV"
        elif name:
            up = name.upper()
            if "HDMI" in up:
                for ch in up:
                    if ch.isdigit():
                        lab = "H" + ch
                        break
                if not lab:
                    lab = "HDMI"
            elif "TV" in up:
                lab = "TV"
            elif "AV" in up or "COMPOSITE" in up:
                lab = "AV"
            else:
                lab = name
        else:
            lab = aid.split(".")[-1] if aid else "?"
        lab = ascii_label(lab).strip() or "?"
        if max_chars > 0 and len(lab) > max_chars:
            lab = lab[:max_chars]
        return lab

    # --- Composite actions (ECP + state, no drawing) -----------------------

    def press_refresh(self, key):
        """Send ``key`` then refresh playback state. Returns the press result."""
        ok = self.press(key)
        try:
            self.refresh_playback()
        except Exception:
            pass
        return ok

    def launch_refresh(self, app_id, query=""):
        """Launch ``app_id`` then refresh playback state. Returns the launch result."""
        ok = self.launch(app_id, query)
        try:
            self.refresh_playback()
        except Exception:
            pass
        return ok

    def mark_power_optimistic(self):
        """Flip cached ``power-mode`` for an immediate UI redraw; return the key.

        Lets a front end repaint the power face before the (blocking) ECP call
        runs on a worker. Pair with :meth:`press_refresh` on the returned key.
        """
        key = self.power_key()
        if not self.device_info:
            self.device_info = {}
        self.device_info["power-mode"] = "DisplayOff" if key == "PowerOff" else "PowerOn"
        return key

    def toggle_power(self):
        """Blocking convenience: flip power, send the key, resync device state.

        Returns the ECP key that was sent. Front ends that want an optimistic
        redraw should instead call :meth:`mark_power_optimistic` on the main
        thread and :meth:`press_refresh` on a worker.
        """
        key = self.mark_power_optimistic()
        self.press(key)
        try:
            self.query_device_info()
            self.refresh_playback()
        except Exception:
            pass
        return key

    @property
    def status(self):
        if self.last_error and not self.connected:
            return "err: " + self.last_error
        if not self.host:
            return "no host"
        if not self.connected:
            return "offline " + self.host
        return self.playback_status()

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

    def discover(
        self, timeout=1.5, retries=1, scan_fallback=True, ssdp=True, on_device=None
    ):
        try:
            priority = [d.get("host") for d in (self.discovered or []) if d.get("host")]
            found = []
            if ssdp:
                # Keep scan_fallback out of discover_rokus so on_device still runs
                # on the unicast path; enrich SSDP hits with ECP names for the UI.
                found = discover_rokus(
                    timeout=timeout,
                    retries=retries,
                    scan_fallback=False,
                    ssdp=True,
                )
                enriched = []
                for info in found:
                    named = _ecp_device(
                        info.get("host") or "", timeout=min(self.timeout, 1.5)
                    )
                    if named:
                        info = named
                    enriched.append(info)
                    if on_device is not None:
                        try:
                            on_device(info)
                        except Exception:
                            pass
                found = enriched
            if not found and scan_fallback:
                found = discover_rokus_scan(
                    priority_hosts=priority, on_device=on_device
                )
            self.discovered = found
            self.last_error = "" if self.discovered else "no Roku found"
        except Exception as e:
            self.discovered = []
            self.last_error = str(e)
        return self.discovered

    def connect(self, discover_if_empty=True):
        """Ping device-info. If host empty and discover_if_empty, discover first."""
        if not self.host and discover_if_empty:
            devices = self.discover(ssdp=True, scan_fallback=True)
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
                self.refresh_playback()
            except Exception:
                pass
            try:
                if not self.apps:
                    self.query_apps()
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
            self.active_screensaver = ""
            return {}
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        # Optional <screensaver id="…" name="…"/> sibling (ECP docs).
        saver = ""
        si = text.find("<screensaver")
        if si >= 0:
            sgt = text.find(">", si)
            if sgt >= 0:
                sattrs = _xml_attrs(text[si : sgt + 1])
                saver = _xml_unescape(
                    sattrs.get("name", "") or sattrs.get("id", "") or ""
                )
                if not saver:
                    saver = "screensaver"
        self.active_screensaver = saver
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
            self.media_state = {}
            return ""
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        self.media_player = text.strip()
        self.media_state = _parse_media_player(self.media_player)
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
