#!/usr/bin/env python3
"""AsyncEval runner (drop-in): usa a pasta tests/ existente, agora COM correção automática.

Cada tests/*.json mantém "id", "title", "prompt" e pode ganhar um destes campos de correção:
  "expected_stdout": ["linha1", "linha2"]    -> acerto exato (o modelo responde {"stdout": [...]})
  "grader": {"all_of": ["regex",...], "any_of": ["regex",...], "none_of": ["regex",...]}
Opcional p/ validar o corretor:  "reference_answer": "texto certo",  "wrong_answers": ["errado1",...]
Teste sem campo de correção aparece como UNGRADED e fica FORA da taxa de acerto.

Uso:
  python runner.py --selftest            # valida corretores (sem API)
  export OPENROUTER_API_KEY=...          # nunca commitar
  python runner.py --trials 3            # roda tudo (retoma se cair)
"""
import argparse, json, os, pathlib, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
ROOT = pathlib.Path(__file__).parent
SYSTEM = "You are an expert senior software engineer specialized in asynchronous systems and concurrency."

# Edite esta lista. CONFIRA os slugs em openrouter.ai/models (os de ponta podem ter mudado).
G = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MODELS = [
    {"id": "openai/gpt-4o-mini", "name": "GPT-4o-mini (baseline)"},
    {"id": "deepseek/deepseek-chat", "name": "DeepSeek chat"},
    {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (free tier)", "url": G, "key_env": "GEMINI_API_KEY"},
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite (free tier)", "url": G, "key_env": "GEMINI_API_KEY"},
    {"id": "gemma-4-31b-it", "name": "Gemma 4 31B (open, free tier)", "url": G, "key_env": "GEMINI_API_KEY"},
]

JSON_SUFFIX = ('\n\nFinish your reply with ONE JSON object on its own line, exactly: '
               '{"stdout": ["line 1", "line 2"]} (one item per output line, no trailing newline).')


def slug(s): return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def load_tests(tests_dir, only=None):
    tests = []
    for f in sorted(os.listdir(tests_dir)):
        if f.endswith(".json") and (not only or f[:-5] in only):
            t = json.load(open(os.path.join(tests_dir, f), encoding="utf-8"))
            t["_file"] = f[:-5]
            tests.append(t)
    return tests


def build_prompt(t):
    p = t.get("prompt", "")
    if "expected_stdout" in t and '"stdout"' not in p:
        p += JSON_SUFFIX
    return p


def extract_stdout(reply):
    dec, found, i = json.JSONDecoder(), None, (reply or "").find("{")
    while i != -1:
        try:
            obj, end = dec.raw_decode(reply[i:])
            if isinstance(obj, dict) and "stdout" in obj:
                found = obj["stdout"]
            i = reply.find("{", i + max(end, 1))
        except ValueError:
            i = reply.find("{", i + 1)
    return found if isinstance(found, list) and all(isinstance(x, str) for x in found) else None


def grade(t, reply):
    """Retorna dict(passed, partial, reason) ou None se o teste não tem corretor."""
    if "expected_stdout" in t:
        got = extract_stdout(reply)
        if got is None:
            return {"passed": False, "partial": 0.0, "reason": "sem JSON valido"}
        got, exp = [x.rstrip() for x in got], [x.rstrip() for x in t["expected_stdout"]]
        if got == exp:
            return {"passed": True, "partial": 1.0, "reason": "acerto exato"}
        n = max(len(got), len(exp)) or 1
        return {"passed": False, "partial": round(sum(a == b for a, b in zip(got, exp)) / n, 3), "reason": "diferente"}
    g = t.get("grader")
    if g:
        fl = re.I | re.S
        all_of, any_of, none_of = g.get("all_of", []), g.get("any_of", []), g.get("none_of", [])
        ok_all = [bool(re.search(p, reply or "", fl)) for p in all_of]
        ok_any = (not any_of) or any(re.search(p, reply or "", fl) for p in any_of)
        ok_none = not any(re.search(p, reply or "", fl) for p in none_of)
        passed = all(ok_all) and ok_any and ok_none
        partial = (sum(ok_all) / len(ok_all)) if ok_all else (1.0 if passed else 0.0)
        return {"passed": passed, "partial": round(partial, 3), "reason": "regex"}
    return None


def selftest(tests):
    bad = 0
    for t in tests:
        name, has_ref = t["_file"], "reference_answer" in t
        if grade(t, "") is None:
            print(f"UNGRADED       {name}: sem corretor (nao entra no placar)"); continue
        if not has_ref:
            print(f"NAO VALIDADO   {name}: falta 'reference_answer' para testar o corretor"); continue
        ref_reply = t["reference_answer"] if isinstance(t["reference_answer"], str) else json.dumps({"stdout": t["reference_answer"]})
        if not grade(t, ref_reply)["passed"]:
            print(f"FALHOU         {name}: corretor REJEITA a resposta certa"); bad += 1; continue
        leaks = [w for w in t.get("wrong_answers", []) if grade(t, w)["passed"]]
        if grade(t, "")["passed"] or leaks:
            print(f"FALHOU         {name}: corretor ACEITA resposta errada/vazia"); bad += 1; continue
        print(f"OK             {name}: aceita a certa e rejeita {len(t.get('wrong_answers', [])) + 1} erradas")
    print("\nSELFTEST " + ("COM PROBLEMAS" if bad else "OK"))
    return bad == 0


def call_model(key, model, prompt, temperature, max_tokens, retries=5, url=API_URL):
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "usage": {"include": True},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    if url != API_URL:
        body.pop("usage", None)   # campo so do OpenRouter
    last = None
    for a in range(retries):
        try:
            t0 = time.time()
            r = requests.post(url, headers=h, json=body, timeout=300)
            if r.status_code == 200 and "choices" in r.json():
                j, u = r.json(), r.json().get("usage", {})
                return {"reply": j["choices"][0]["message"].get("content") or "", "latency": round(time.time() - t0, 2),
                        "tokens": u.get("total_tokens", 0), "cost": u.get("cost", 0) or 0, "served_by": j.get("model", model), "finish": j["choices"][0].get("finish_reason")}
            last = f"HTTP {r.status_code}: {r.text.strip()[:300]}"
        except Exception as e:
            last = repr(e)
        time.sleep(30 if "429" in str(last) else 2 ** a * 2)
    return {"error": last}   # sem fallback para outro modelo: isso falsearia o resultado


def one_trial(key, m, t, k, args):
    path = ROOT / "transcripts" / slug(m["id"]) / f"{t['_file']}_trial{k}.json"
    if path.exists():
        return json.loads(path.read_text())
    if m["id"] in (args.skip or []):
        return {"model": m["id"], "name": m["name"], "test": t["_file"], "title": t.get("title", t["_file"]), "trial": k, "status": "error", "error": "pulado (--skip)"}
    prompt = build_prompt(t)
    res = call_model(os.getenv(m.get("key_env", "OPENROUTER_API_KEY")) or key, m["id"], prompt, args.temperature, args.max_tokens, url=m.get("url", API_URL))
    rec = {"model": m["id"], "name": m["name"], "test": t["_file"], "title": t.get("title", t["_file"]), "trial": k,
           "temperature": args.temperature, "date": time.strftime("%Y-%m-%d"), "prompt": prompt}
    if "error" in res:
        return {**rec, "status": "error", "error": res["error"]}   # nao salva: tenta de novo na proxima execucao
    if res.get("finish") == "length":
        return {**rec, "status": "error", "error": "resposta cortada (finish_reason=length): use --max-tokens maior"}
    g = grade(t, res["reply"])
    rec.update({"status": "ok", **res, "graded": g is not None, **(g or {"passed": None, "partial": None, "reason": "ungraded"})})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    return rec


def report(recs, tests, args, elapsed):
    graded_ids = [t["_file"] for t in tests if grade(t, "") is not None]
    rows, per_model = [], []
    for m in MODELS:
        ok = [r for r in recs if r["model"] == m["id"] and r["status"] == "ok"]
        err = sum(1 for r in recs if r["model"] == m["id"] and r["status"] == "error")
        gr = [r for r in ok if r["graded"]]
        by = {}
        for r in gr: by.setdefault(r["test"], []).append(r)
        passed = sum(r["passed"] for r in gr)
        at_k = sum(any(x["passed"] for x in v) for v in by.values())
        pow_k = sum(len(v) == args.trials and all(x["passed"] for x in v) for v in by.values())
        e = {"model": m["id"], "name": m["name"], "graded_trials": len(gr), "errors": err,
             "pass_rate": round(passed / len(gr), 3) if gr else None,
             "pass_at_k": f"{at_k}/{len(graded_ids)}", "pass_pow_k": f"{pow_k}/{len(graded_ids)}",
             "avg_latency_s": round(sum(r["latency"] for r in ok) / len(ok), 2) if ok else None,
             "tokens": sum(r["tokens"] for r in ok), "cost_usd": round(sum(r["cost"] for r in ok), 4),
             "per_test": {tid: f"{sum(x['passed'] for x in v)}/{len(v)}" for tid, v in by.items()}}
        per_model.append(e)
        rows.append(f"| {m['name']} | {len(gr)} (+{err} erros) | {e['pass_rate']} | {e['pass_at_k']} | {e['pass_pow_k']} | "
                    f"{e['avg_latency_s']}s | {e['tokens']} | {e['cost_usd']} |")
    ungraded = [t["_file"] for t in tests if t["_file"] not in graded_ids]
    json.dump({"date": time.strftime("%Y-%m-%d"), "trials_per_test": args.trials, "temperature": args.temperature,
               "total_seconds": round(elapsed, 1), "ungraded_tests": ungraded, "models": per_model},
              open(ROOT / "evaluation_report.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    md = ["# AsyncEval - Resultados", "", f"Data: {time.strftime('%Y-%m-%d')} | trials por teste: {args.trials} | temperatura: {args.temperature}", "",
          "| Modelo | Trials corrigidos | Taxa de acerto | pass@k | pass^k | Latencia media | Tokens | Custo ($) |", "|---|---|---|---|---|---|---|---|"] + rows
    md += ["", "## Acertos por teste (acertos/trials)", "", "| Teste | " + " | ".join(m["name"] for m in MODELS) + " |", "|---|" + "---|" * len(MODELS)]
    for tid in graded_ids:
        md.append(f"| {tid} | " + " | ".join(next(p for p in per_model if p["model"] == m["id"])["per_test"].get(tid, "-") for m in MODELS) + " |")
    if ungraded:
        md += ["", "Testes SEM corretor (fora do placar): " + ", ".join(ungraded)]
    (ROOT / "SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(md) + "\n\nSalvo: SUMMARY.md, evaluation_report.json, transcripts/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests-dir", default="tests")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", nargs="*", help="nomes de teste, ex: test3_event_loop_order")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--skip", nargs="*", default=[], help="ids de modelos a NAO chamar (usa so o que ja esta salvo)")
    args = ap.parse_args()
    if not os.path.isdir(args.tests_dir):
        sys.exit("Pasta 'tests/' nao encontrada.")
    tests = load_tests(args.tests_dir, args.only)
    if args.selftest:
        sys.exit(0 if selftest(tests) else 1)
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        sys.exit("Defina OPENROUTER_API_KEY (export OPENROUTER_API_KEY=...)")
    jobs = [(m, t, k) for m in MODELS for t in tests for k in range(1, args.trials + 1)]
    print(f"{len(tests)} testes x {len(MODELS)} modelos x {args.trials} trials = {len(jobs)} chamadas")
    t0, recs = time.time(), []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one_trial, key, m, t, k, args) for m, t, k in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result(); recs.append(r)
            tag = "ERRO " if r["status"] == "error" else ("S/COR " if not r["graded"] else ("PASS " if r["passed"] else "FAIL "))
            print(f"[{i}/{len(jobs)}] {tag}{r['model']} {r['test']} t{r['trial']}" + (" -> " + r["error"][:300] if r["status"] == "error" else ""))
    report(recs, tests, args, time.time() - t0)


if __name__ == "__main__":
    main()