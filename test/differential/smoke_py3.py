#!/usr/bin/env python3
"""
CI smoke test (migrate-python3, task 7.1).

Boots the py3 fuzzingserver, drives sections 1-2 with an asyncio echo testee,
and asserts every reported case passes (OK / informational) with no server-side
exceptions. Exits non-zero on any failure. Self-contained; no Docker.
"""
import asyncio, json, os, signal, subprocess, sys, time, socket, tempfile

HOST, PORT = "127.0.0.1", 9101
SPEC = {"url": "ws://%s:%d" % (HOST, PORT), "outdir": "./reports/clients",
        "cases": ["1.*", "2.*"], "exclude-cases": [], "exclude-agent-cases": {}}


def wait_port(host, port, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((host, port), 1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


async def _drive():
    from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
    loop = asyncio.get_event_loop()

    class Echo(WebSocketClientProtocol):
        def onMessage(self, payload, isBinary):
            self.sendMessage(payload, isBinary)
        def onClose(self, *a):
            if not self.factory._d.done():
                self.factory._d.set_result(True)

    async def one(path, proto=Echo, timeout=20):
        fac = WebSocketClientFactory("ws://%s:%d%s" % (HOST, PORT, path))
        fac.protocol = proto
        fac._d = loop.create_future()
        await loop.create_connection(lambda: fac(), HOST, PORT)
        try:
            await asyncio.wait_for(fac._d, timeout=timeout)
        except asyncio.TimeoutError:
            pass

    got = {}
    class Count(Echo):
        def onMessage(self, payload, isBinary):
            got["n"] = json.loads(payload.decode())
    await one("/getCaseCount", Count)
    n = got.get("n", 0)
    for i in range(1, n + 1):
        await one("/runCase?case=%d&agent=ci" % i)
    await one("/updateReports?agent=ci")
    return n


def main():
    workdir = tempfile.mkdtemp(prefix="wstest-ci-")
    with open(os.path.join(workdir, "fuzzingserver.json"), "w") as f:
        json.dump(SPEC, f)
    logf = open(os.path.join(workdir, "server.log"), "w")
    # resolve wstest next to the running interpreter (works under `uv run` and .venv)
    wstest = os.path.join(os.path.dirname(sys.executable), "wstest")
    if not os.path.exists(wstest):
        wstest = "wstest"
    proc = subprocess.Popen(
        [wstest, "-m", "fuzzingserver", "-s", "fuzzingserver.json",
         "-w", "ws://%s:%d" % (HOST, PORT), "-u", "0"],
        cwd=workdir, stdout=logf, stderr=subprocess.STDOUT)
    try:
        assert wait_port(HOST, PORT), "fuzzingserver did not start"
        n = asyncio.run(_drive())
        time.sleep(1)
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()

    log = open(os.path.join(workdir, "server.log")).read()
    if "Traceback" in log:
        sys.stderr.write("SERVER EXCEPTION:\n")
        sys.stderr.write(log)
        sys.exit(1)

    idx = json.load(open(os.path.join(workdir, "reports", "clients", "index.json")))
    agent = list(idx.keys())[0]
    bad = {cid: c["behavior"] for cid, c in idx[agent].items()
           if c["behavior"] not in ("OK", "INFORMATIONAL")}
    print("ran %d cases; %d reported; non-passing: %s" % (n, len(idx[agent]), bad or "none"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
