# Differential driver: plain /getCaseCount (works against the 2015 py2 server),
# permessage-deflate on /runCase (exercises the compression cases).
import argparse, asyncio, json
from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
from autobahn.websocket.compress import (PerMessageDeflateOffer,
    PerMessageDeflateResponse, PerMessageDeflateResponseAccept)

class Echo(WebSocketClientProtocol):
    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)          # echo (with negotiated compression)
    def onClose(self, wasClean, code, reason):
        if not self.factory._d.done(): self.factory._d.set_result(True)

def _accept(response):
    if isinstance(response, PerMessageDeflateResponse):
        return PerMessageDeflateResponseAccept(response)

async def _conn(loop, host, port, path, deflate, proto=Echo, timeout=60):
    fac = WebSocketClientFactory("ws://%s:%d%s" % (host, port, path))
    fac.protocol = proto
    if deflate:
        fac.setProtocolOptions(perMessageCompressionOffers=[PerMessageDeflateOffer()],
                               perMessageCompressionAccept=_accept)
    fac._d = loop.create_future()
    await loop.create_connection(lambda: fac(), host, port)
    try: await asyncio.wait_for(fac._d, timeout=timeout)
    except asyncio.TimeoutError: pass

async def main(url, agent):
    _, rest = url.split("://"); host, port = rest.split(":"); port = int(port)
    loop = asyncio.get_event_loop()
    got = {}
    class Count(Echo):
        def onMessage(self, payload, isBinary): got["n"] = json.loads(payload.decode())
    await _conn(loop, host, port, "/getCaseCount", deflate=False, proto=Count)  # PLAIN
    n = got.get("n", 0); print("case count:", n, flush=True)
    for i in range(1, n + 1):
        await _conn(loop, host, port, "/runCase?case=%d&agent=%s" % (i, agent), deflate=True)
    await _conn(loop, host, port, "/updateReports?agent=%s" % agent, deflate=False)
    print("ran", n, "cases", flush=True)

ap = argparse.ArgumentParser(); ap.add_argument("--url"); ap.add_argument("--agent", default="diffcheck")
a = ap.parse_args(); asyncio.run(main(a.url, a.agent))
