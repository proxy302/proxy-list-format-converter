#!/usr/bin/env python3
"""convert-proxies: turn a proxy list from one common format into another.

Reads lines such as
  host:port:user:pass
  user:pass@host:port
  host:port@user:pass
  http://user:pass@host:port   (or socks5:// / socks5h://)
  host:port
and writes them in the format you choose. Credentials are percent-encoded in
URL output, so passwords containing @ : / # ? % are safe. Standard library only.
"""
import argparse
import json
import re
import sys
import urllib.parse

HOSTPORT = re.compile(r"^(?P<host>\[[0-9a-fA-F:]+\]|[A-Za-z0-9.-]+):(?P<port>\d{1,5})$")


def parse(line, default_scheme):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    scheme = default_scheme
    m = re.match(r"^(https?|socks5h?|socks4a?)://(.+)$", line, re.I)
    if m:
        scheme, line = m.group(1).lower(), m.group(2)
        if "@" in line:
            cred, hp = line.rsplit("@", 1)
            user, _, pw = cred.partition(":")
            user, pw = urllib.parse.unquote(user), urllib.parse.unquote(pw)
        else:
            user = pw = ""
            hp = line
        hp = hp.rstrip("/")
    elif "@" in line and (HOSTPORT.match(line.rsplit("@", 1)[1]) or HOSTPORT.match(line.split("@", 1)[0])):
        if HOSTPORT.match(line.rsplit("@", 1)[1]):     # user:pass@host:port
            left, hp = line.rsplit("@", 1)
            user, _, pw = left.partition(":")
        else:                                          # host:port@user:pass
            hp, right = line.split("@", 1)
            user, _, pw = right.partition(":")
    else:                                              # host:port or host:port:user:pass
        parts = line.split(":")
        if len(parts) == 2:
            hp, user, pw = line, "", ""
        elif len(parts) >= 4:                # host:port:user:pass (pass may contain ':')
            hp = ":".join(parts[:2])
            user, pw = parts[2], ":".join(parts[3:])
        else:
            raise ValueError("expected host:port or host:port:user:pass")
    m = HOSTPORT.match(hp)
    if not m or not (0 < int(m.group("port")) < 65536):
        raise ValueError(f"bad host:port {hp!r}")
    return {"scheme": scheme, "host": m.group("host"), "port": int(m.group("port")), "user": user, "pass": pw}


def render(p, fmt):
    q = lambda s: urllib.parse.quote(s, safe="")
    auth_url = f"{q(p['user'])}:{q(p['pass'])}@" if p["user"] else ""
    url = f"{p['scheme']}://{auth_url}{p['host']}:{p['port']}"
    if fmt == "url":
        return url
    if fmt == "curl":
        return f"curl -x '{url}' https://api.ipify.org"
    if fmt == "hpup":
        return f"{p['host']}:{p['port']}:{p['user']}:{p['pass']}" if p["user"] else f"{p['host']}:{p['port']}"
    if fmt == "upah":
        return f"{p['user']}:{p['pass']}@{p['host']}:{p['port']}" if p["user"] else f"{p['host']}:{p['port']}"
    if fmt == "json":
        return json.dumps(p)
    raise ValueError(fmt)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="input file (default: stdin)")
    ap.add_argument("--to", choices=["url", "curl", "hpup", "upah", "json"], default="url",
                    help="url: scheme://user:pass@host:port (default); hpup: host:port:user:pass; "
                         "upah: user:pass@host:port; curl: a test command; json: one object per line")
    ap.add_argument("--scheme", default="http", help="scheme for lines that have none: http, socks5h ... (default http)")
    a = ap.parse_args()
    src = open(a.file, encoding="utf-8") if a.file else sys.stdin
    bad = 0
    for n, line in enumerate(src, 1):
        try:
            p = parse(line, a.scheme)
        except ValueError as e:
            print(f"line {n}: {e}", file=sys.stderr)
            bad += 1
            continue
        if p:
            print(render(p, a.to))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
