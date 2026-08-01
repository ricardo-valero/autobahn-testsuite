#!/usr/bin/env python3
"""
migrate-python3 differential validation (phase 5.1/5.2).

Drives a running fuzzingserver (either the frozen Docker reference or the py3
port) with a conformant echo testee, then emits the normalized index.json so
two runs can be diffed. Usage:

  # terminal A - reference (frozen Docker image):
  docker run -it --rm -v $PWD/config:/config -v $PWD/reports:/reports \
      -p 9001:9001 crossbario/autobahn-testsuite wstest -m fuzzingserver

  # terminal A' - py3 port:
  uv run wstest -m fuzzingserver -s fuzzingserver.json

  # terminal B - drive it and collect:
  python test/differential/run_fuzzingserver.py --url ws://127.0.0.1:9001 \
      --agent portcheck --out reports/py3

Then compare two collected index.json files with normalize_reports.py.
"""
import argparse, asyncio, json, os, sys

from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory


class Echo(WebSocketClientProtocol):
    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)
    def onClose(self, wasClean, code, reason):
        if not self.factory._d.done():
            self.factory._d.set_result(True)


async def _one(loop, host, port, path, proto=Echo, timeout=30):
    fac = WebSocketClientFactory("ws://%s:%d%s" % (host, port, path))
    fac.protocol = proto
    fac._d = loop.create_future()
    await loop.create_connection(lambda: fac(), host, port)
    try:
        await asyncio.wait_for(fac._d, timeout=timeout)
    except asyncio.TimeoutError:
        pass


async def main(url, agent, out):
    _, rest = url.split("://")
    host, port = rest.split(":")
    port = int(port)
    loop = asyncio.get_event_loop()

    got = {}
    class Count(Echo):
        def onMessage(self, payload, isBinary):
            got["n"] = json.loads(payload.decode())
    await _one(loop, host, port, "/getCaseCount", Count)
    n = got.get("n", 0)
    print("case count:", n)
    for i in range(1, n + 1):
        await _one(loop, host, port, "/runCase?case=%d&agent=%s" % (i, agent))
    await _one(loop, host, port, "/updateReports?agent=%s" % agent)
    print("ran %d cases; reports written by server to its outdir" % n)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="ws://127.0.0.1:9001")
    ap.add_argument("--agent", default="portcheck")
    ap.add_argument("--out", default=None, help="unused placeholder; server writes reports")
    a = ap.parse_args()
    asyncio.run(main(a.url, a.agent, a.out))
