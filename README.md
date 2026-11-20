# proxy-list-format-converter: convert host:port:user:pass to a proxy URL (and back)

Most tools want a proxy as a URL, `http://USER:PASS@HOST:PORT`, while providers and marketplaces often hand out lists as `host:port:user:pass` or `user:pass@host:port`. Converting by hand breaks as soon as a password contains `@`, `:`, `#` or `/`, because those characters have a meaning inside a URL. `convert-proxies.py` reads a list in any of the common formats, detects the format per line, and writes the format you ask for, percent-encoding the username and password in URL output so they survive.

Proxy302 maintains this tool and sells proxies. Our console gives connection details as host, port, username and password; a single static residential (ISP) IP for one day costs $0.50 if you want something to test with ([prices](https://proxy302.com/pricing/)). The converter works with any provider's lists and never connects anywhere.

## Usage

```bash
git clone https://github.com/proxy302/proxy-list-format-converter
cd proxy-list-format-converter
python3 convert-proxies.py examples.txt                 # to URLs (default)
python3 convert-proxies.py list.txt --to hpup           # to host:port:user:pass
python3 convert-proxies.py list.txt --to upah           # to user:pass@host:port
python3 convert-proxies.py list.txt --to curl           # one curl test command per proxy
python3 convert-proxies.py list.txt --scheme socks5h    # lines without a scheme are SOCKS5
cat list.txt | python3 convert-proxies.py --to json     # one JSON object per line
```

Python 3.8 or later, standard library only. Lines starting with `#` are skipped. Lines that cannot be parsed are reported on stderr with their line number, and the exit code is 1.

## Formats it reads

- `host:port:user:pass` (a password may itself contain `:` or `@`)
- `user:pass@host:port`
- `host:port@user:pass`
- `http://user:pass@host:port`, `socks5://...`, `socks5h://...` (already-encoded credentials are decoded first)
- `host:port` with no login (IP-allowlisted proxies)

## Example

Input (`examples.txt` in this repo, documentation addresses only):

```
203.0.113.10:8000:user-1:p@ss:word
user-2:secret#1@203.0.113.11:8001
203.0.113.12:8002@user-3:plain
socks5h://user-4:a%2Fb@203.0.113.13:1080
203.0.113.14:3128
```

Output with the default `--to url`:

```
http://user-1:p%40ss%3Aword@203.0.113.10:8000
http://user-2:secret%231@203.0.113.11:8001
http://user-3:plain@203.0.113.12:8002
socks5h://user-4:a%2Fb@203.0.113.13:1080
http://203.0.113.14:3128
```

## FAQ

**Why are there `%40` and `%3A` in the password?** That is `@` and `:` encoded. curl, Python requests, Node and Playwright all decode them before logging in, so the proxy receives the original password.

**HTTP or SOCKS5?** The list format does not say. Use `--scheme` to match what you bought; a wrong scheme fails with an error rather than a wrong IP.

**`socks5` or `socks5h`?** `socks5h` resolves host names through the proxy, which is usually what you want. Some tools only accept `socks5`; convert, then edit.

**Is `host:port:user:pass` ambiguous?** Only if the username contains `:`, which providers avoid. The converter treats the first two fields as host and port, the third as the username and everything after as the password.

More on special characters in passwords: [proxy-password-special-characters](https://github.com/proxy302/proxy-password-special-characters).

*Facts checked 20 November 2026.*
