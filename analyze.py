"""Resume as falhas por tarefa: quais saidas erradas os modelos mais previram (sem API)."""
import glob, json, collections
import runner

tests = {}
for f in sorted(glob.glob("tests/hard*.json")):
    tests[f.replace("\\", "/").split("/")[-1][:-5]] = json.load(open(f, encoding="utf-8"))
recs = collections.defaultdict(list)
for f in glob.glob("transcripts/*/hard*_trial*.json"):
    d = json.load(open(f, encoding="utf-8"))
    if d.get("status") == "ok" and d.get("graded"):
        recs[d["test"]].append(d)

out = ["# Resumo das falhas (gerado por analyze.py)", ""]
for tid, t in tests.items():
    exp, rs = t["expected_stdout"], recs.get(tid, [])
    fails = [r for r in rs if not r["passed"]]
    out += [f"## {tid}", "", f"Acertos: {len(rs) - len(fails)}/{len(rs)}", f"Esperado: {exp}", ""]
    c, who = collections.Counter(), collections.defaultdict(set)
    for r in fails:
        key = json.dumps(runner.extract_stdout(r["reply"]), ensure_ascii=False)
        c[key] += 1
        who[key].add(r["model"])
    for key, n in c.most_common(3):
        got = json.loads(key)
        if got is None:
            diff = "sem JSON valido"
        else:
            d = next(((i, a, b) for i, (a, b) in enumerate(zip(got, exp)) if a != b), None)
            diff = (f"1a linha diferente (#{d[0] + 1}): previu {d[1]!r}, esperado {d[2]!r}" if d
                    else f"tamanho diferente: previu {len(got)} linhas, esperado {len(exp)}")
        out += [f"- {n} falha(s) previram {got}", f"  modelos: {', '.join(sorted(who[key]))}", f"  {diff}"]
    out.append("")
open("FAILURES.md", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
print("Salvo em FAILURES.md")