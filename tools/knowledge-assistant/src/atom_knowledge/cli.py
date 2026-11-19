"""Run from repository root: python -m atom_knowledge --help."""
import argparse
import json
import os
import sqlite3
import sys
from .api import make_server
from .config import Config
from .evaluation import evaluate
from .generation import ask
from .ingestion import ingest
from .providers import FastEmbedProvider, OllamaGenerator, file_hash
from .retrieval import Retriever
from .storage import Store
from .rendering import render_answer


def parser():
    p = argparse.ArgumentParser(description="Read-only ATOM engineering knowledge assistant")
    p.add_argument("--root"); p.add_argument("--data"); p.add_argument("--config")
    commands = p.add_subparsers(dest="command",required=True)
    for name in ["index","update"]:
        sub = commands.add_parser(name); sub.add_argument("--full",action="store_true"); sub.add_argument("--lexical-only",action="store_true")
    commands.add_parser("inventory")
    check = commands.add_parser("integrity"); check.add_argument("--sources",action="store_true")
    for name in ["remove","restore"]:
        commands.add_parser(name).add_argument("source_path")
    for name in ["search","ask","evaluate","serve"]:
        sub = commands.add_parser(name)
        sub.add_argument("--mode",choices=["lexical","semantic","hybrid"],default="hybrid")
        sub.add_argument("--k",type=int,default=5)
        if name in {"search","ask"}:
            sub.add_argument("question")
            for key in ["module","source-type","experiment","after","before"]: sub.add_argument("--"+key)
        if name in {"ask","serve"}:
            sub.add_argument("--generator",choices=["extractive","ollama"],default="extractive")
            sub.add_argument("--llm-model",default=os.getenv("ATOM_KNOWLEDGE_LLM_MODEL"))
            sub.add_argument("--ollama-url",default=os.getenv("ATOM_KNOWLEDGE_OLLAMA_URL","http://127.0.0.1:11434"))
        if name=="ask":
            sub.add_argument("--context-chars",type=int)
            sub.add_argument("--format",choices=["text","json"],default="text")
        if name=="evaluate":
            sub.add_argument("--dataset",default="knowledge/datasets/engineering-v1.json"); sub.add_argument("--output",required=True)
        if name=="serve": sub.add_argument("--port",type=int,default=8765)
    sub = commands.add_parser("experiments")
    sub.add_argument("--experiment"); sub.add_argument("--metric"); sub.add_argument("--limit",type=int,default=1000); sub.add_argument("--offset",type=int,default=0)
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream,"reconfigure"): stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    store = None
    try:
        config = Config.load(args.root,args.data,args.config)
        mutation = args.command in {"index","update","remove","restore"}
        store = Store(config.data/"index.sqlite3",readonly=not mutation)
        if args.command in {"index","update"}:
            provider = None if args.lexical_only else FastEmbedProvider(config)
            result = ingest(config,store,provider,args.full)
        elif args.command=="inventory": result = store.inventory()
        elif args.command=="integrity":
            result = store.integrity()
            if args.sources:
                stale = []
                for doc in store.inventory():
                    try: current = file_hash(config.source(doc["source_path"]))==doc["content_hash"]
                    except (OSError,ValueError): current = False
                    if not current: stale.append(doc["source_path"])
                result["stale_sources"] = stale; result["ok"] &= not stale
        elif args.command in {"remove","restore"}:
            relative = config.source(args.source_path).relative_to(config.root).as_posix()
            store.remove(relative,args.command=="restore")
            result = {"source_path":relative,"action":args.command,"note":"Sources are unchanged; restore requires update to ingest again."}
        elif args.command=="experiments":
            if not 1<=args.limit<=10000 or args.offset<0: raise ValueError("Invalid pagination")
            result = store.observations(args.experiment,args.metric,args.limit,args.offset)
        else:
            provider = FastEmbedProvider(config) if args.mode!="lexical" else None
            retriever = Retriever(config,store,provider)
            generator = None
            if getattr(args,"generator",None)=="ollama":
                if not args.llm_model: raise ValueError("--llm-model is required for Ollama")
                generator = OllamaGenerator(args.llm_model,args.ollama_url)
            if args.command=="evaluate": result = evaluate(retriever,args.dataset,args.output,args.k,args.mode)
            elif args.command=="serve":
                server = make_server(retriever,port=args.port,generator=generator,default_mode=args.mode,default_k=args.k)
                print(f"Read-only API: http://127.0.0.1:{args.port}",file=sys.stderr,flush=True)
                try: server.serve_forever()
                finally: server.server_close()
                return 0
            else:
                filters = {key:getattr(args,key) for key in ["module","source_type","experiment","after","before"] if getattr(args,key) is not None}
                result = retriever.search(args.question,args.mode,args.k,filters) if args.command=="search" else ask(retriever,args.question,args.mode,args.k,filters,args.context_chars,generator)
        print(render_answer(result) if args.command=="ask" and args.format=="text" else json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
        return 1 if args.command=="integrity" and not result["ok"] else 0
    except (OSError,ValueError,RuntimeError,sqlite3.Error) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False),file=sys.stderr)
        return 2
    finally:
        if store: store.close()


if __name__=="__main__": raise SystemExit(main())
