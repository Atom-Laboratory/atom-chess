"""Loopback-only JSON API. No mutations, shell commands or robot imports."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlsplit
from .generation import ask


def make_server(retriever, host="127.0.0.1", port=8765, generator=None, default_mode="hybrid", default_k=5):
    if host not in {"127.0.0.1","localhost"}: raise ValueError("API is restricted to IPv4 loopback")
    if default_mode not in {"lexical","semantic","hybrid"} or not 1<=default_k<=50: raise ValueError("Invalid retrieval defaults")
    class Handler(BaseHTTPRequestHandler):
        server_version = "AtomKnowledge/0.1"
        def log_message(self,*args): pass  # Do not persist potentially private queries.
        def reply(self,status,value):
            raw = json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(raw))); self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
        def do_GET(self): self.dispatch(False)
        def do_POST(self): self.dispatch(True)
        def dispatch(self,post):
            # Reject browser-origin and DNS-rebinding requests; no CORS support.
            hostname = self.headers.get("Host","").split(":")[0]
            if self.headers.get("Origin") or hostname not in {"127.0.0.1","localhost"}:
                return self.reply(403,{"error":"Local non-browser client required"})
            try:
                url = urlsplit(self.path)
                if post:
                    length = int(self.headers.get("Content-Length","0"))
                    if length<=0 or length>16384: return self.reply(413,{"error":"Request body limit is 16 KiB"})
                    if self.headers.get("Content-Type","").split(";")[0]!="application/json": return self.reply(415,{"error":"Use application/json"})
                    self.connection.settimeout(10)
                    params = json.loads(self.rfile.read(length))
                    if not isinstance(params,dict): raise ValueError("Expected JSON object")
                else:
                    params = {k:v[-1] for k,v in parse_qs(url.query).items()}
                if url.path=="/health" and not post:
                    return self.reply(200,{"status":"ok","read_only":True,"embedding":retriever.store.get("embedding")})
                if url.path=="/inventory" and not post:
                    return self.reply(200,retriever.store.inventory())
                if url.path=="/experiments" and not post:
                    limit,offset = int(params.get("limit",1000)),int(params.get("offset",0))
                    if not 1<=limit<=10000 or offset<0: raise ValueError("Invalid pagination")
                    return self.reply(200,retriever.store.observations(params.get("experiment"),params.get("metric"),limit,offset))
                if url.path not in {"/search","/ask"}: return self.reply(404,{"error":"Unknown read endpoint"})
                known = {"q","mode","k","filters","context_chars"}
                if set(params)-known: raise ValueError("Unknown query field")
                question = params.get("q","")
                mode,k = params.get("mode",default_mode),int(params.get("k",default_k))
                filters = params.get("filters")
                if filters is not None and not isinstance(filters,dict): raise ValueError("filters must be a JSON object")
                result = (retriever.search(question,mode,k,filters) if url.path=="/search" else
                          ask(retriever,question,mode,k,filters,params.get("context_chars"),generator))
                self.reply(200,result)
            except (ValueError,TypeError,KeyError) as error:
                self.reply(400,{"error":str(error)})
            except Exception:
                self.reply(503,{"error":"Knowledge provider unavailable; no action was executed"})
    return HTTPServer((host,port),Handler)
