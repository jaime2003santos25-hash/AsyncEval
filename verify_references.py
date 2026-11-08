"""Re-executa o programa de cada teste hard* e confere se bate com expected_stdout (sem API)."""
import glob, json, re, subprocess, sys

ok = True
for path in sorted(glob.glob("tests/hard*.json")):
    t = json.load(open(path, encoding="utf-8"))
    m = re.search(r"```python\n(.*?)\n```", t["prompt"], re.S)
    outs = set()
    for _ in range(5):
        r = subprocess.run([sys.executable, "-c", m.group(1)], capture_output=True, text=True, timeout=60)
        outs.add(r.stdout)
    same = len(outs) == 1 and list(outs)[0].splitlines() == t["expected_stdout"]
    print(("OK    " if same else "FALHOU"), t["id"], "(5 execucoes identicas e iguais ao gabarito)" if same else "")
    ok = ok and same
print("\nVERIFICACAO", "OK" if ok else "COM PROBLEMAS", "- Python", sys.version.split()[0])
sys.exit(0 if ok else 1)
