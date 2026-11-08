#!/usr/bin/env python3
"""upgrade_tests.py - rode UMA vez na pasta do projeto (onde esta tests/).
 1) Acrescenta correcao automatica aos seus test1..test10 (mantem id/title/prompt;
    so remove o caractere chines perdido no prompt do test6).
 2) Cria 8 testes dificeis hard01..hard08 (prever stdout de programas Python 3.12 asyncio),
    com gabarito obtido por EXECUCAO REAL no CPython 3.12.3.
Depois rode:  python runner.py --selftest
"""
import glob, json, os, sys

TEMPLATE = """You are given a Python 3.12 program (CPython 3.12, default asyncio event loop, run as `python program.py`).
Predict EXACTLY what it writes to stdout, line by line, in order. Ignore stderr.
Think as carefully as you need. Then finish your reply with ONE JSON object on its own, in this exact shape:
{"stdout": ["first line", "second line"]}
Each list item is one line of stdout without the trailing newline. If nothing is printed, use {"stdout": []}.

```python
%s
```"""

UPDATES = {'test1': {'prompt_replace': [],
           'grader': {'all_of': ['race|condi[çc][ãa]o de corrida|concorr[êe]ncia|lost '
                                 'update|ambas|both|simult[âa]ne|ao mesmo tempo|intercal|interleav',
                                 '\\b20\\b',
                                 'mutex|lock|sem[áa]foro|semaphore|at[óo]mic|fila|queue|serializ|reler|re-?read|verifica.{0,20}ap[óo]s']},
           'reference_answer': 'Não. Há uma race condition: as duas chamadas leem current = 100 antes do '
                               'delay, ambas passam no if e ambas retornam Success; o saldo final fica 20 (e '
                               'não -60). Corrige com um mutex/lock que serializa as chamadas, ou relendo o '
                               'saldo depois do await.',
           'wrong_answers': ['Sim, o saldo final fica correto: uma retorna Success e a outra Denied, saldo '
                             '20.',
                             'Não é seguro porque o JavaScript é lento.']},
 'test2': {'grader': {'all_of': ['deadlock|impasse|bloqueio m[úu]tuo',
                                 'ordem|order|timeout|try[_ ]?lock|[úu]nico lock|single lock']},
           'reference_answer': 'Pode ocorrer deadlock: task1 segura lock_a e espera lock_b enquanto task2 '
                               'segura lock_b e espera lock_a. Resolve-se adquirindo os locks sempre na '
                               'mesma ordem, ou usando timeout no acquire.',
           'wrong_answers': ['Nada de especial acontece, as duas terminam sempre.',
                             'Fica mais lento mas funciona.']},
 'test3': {'expected_stdout': ['1', '5', '4', '3', '2'],
           'reference_answer': ['1', '5', '4', '3', '2'],
           'wrong_answers': ['{"stdout": ["1","5","3","4","2"]}', '{"stdout": ["1","2","3","4","5"]}']},
 'test4': {'grader': {'all_of': ['Index:\\s*5|(cinco|five|5)\\s*(vezes|times)|imprim\\w*.{0,40}\\b5\\b|prints?.{0,40}\\b5\\b',
                                 '\\blet\\b',
                                 'escopo|scope|closure']},
           'reference_answer': 'Com var, i tem escopo de função e é partilhado pela closure; quando os '
                               "timeouts disparam o loop já terminou e i vale 5, por isso imprime 'Index: 5' "
                               'cinco vezes. Corrige-se com let (escopo de bloco).',
           'wrong_answers': ['Imprime Index: 0, 1, 2, 3, 4 normalmente.',
                             'O problema é só a função ser async.']},
 'test5': {'grader': {'all_of': ['allSettled',
                                 'status',
                                 'rejeit|reject|falh|fail',
                                 'fail[- ]?fast|curto|short[- ]?circuit|imediat|assim que|as soon '
                                 'as|primeira? rejei',
                                 'n[ãa]o cancel|not cancel|continu\\w+ (a )?(execut|run)|still run|n[ãa]o '
                                 '(aborta|interrompe)|keep(s)? running']},
           'reference_answer': 'Promise.all rejeita imediatamente (fail-fast) com o motivo da primeira '
                               'promessa que falha, mas as outras continuam a executar, não são canceladas. '
                               'Promise.allSettled espera todas e devolve um array de objetos com status '
                               "'fulfilled' ou 'rejected', nunca rejeita.",
           'wrong_answers': ['Promise.all cancela as outras promessas quando uma falha.',
                             'São equivalentes.']},
 'test6': {'prompt_replace': [['单 thread', 'thread única']],
           'expected_stdout': ['1'],
           'reference_answer': ['1'],
           'wrong_answers': ['{"stdout": ["100"]}', '{"stdout": ["0"]}']},
 'test7': {'grader': {'all_of': ['event loop',
                                 'main thread|thread principal',
                                 'n[ãa]o (usa|utiliza|passa|vai|corre|executa)\\w*.{0,60}(thread ?pool|pool '
                                 "de threads|libuv)|(does not|doesn't|not) (use|go through|run "
                                 'on).{0,60}(thread ?pool|libuv)|(runs?|executa\\w*|corre\\w*).{0,40}(main '
                                 'thread|thread principal)',
                                 'UV_THREADPOOL_SIZE|worker[_ ]threads|ass[ií]ncron|async|cluster']},
           'reference_answer': 'pbkdf2Sync não usa o thread pool do libuv: corre na thread principal e '
                               'bloqueia o event loop, logo nenhum outro callback de I/O é atendido. A '
                               'versão assíncrona pbkdf2 usa o thread pool (tamanho 4 por defeito, '
                               'UV_THREADPOOL_SIZE). Resolve-se usando a versão assíncrona ou '
                               'worker_threads.',
           'wrong_answers': ['O pbkdf2Sync ocupa as 4 threads do thread pool do libuv e por isso o I/O fica '
                             'em fila.',
                             'Não tem impacto.']},
 'test8': {'grader': {'all_of': ['race|condi[çc][ãa]o de corrida|lost update|inconsist|last[- '
                                 ']write|[úu]ltima escrita|sobrescrev|overwrit',
                                 'serial|fila|queue|mutex|lock|synchroniz|sincroniz|at[óo]mic|single[- '
                                 ']thread|thread [úu]nica']},
           'reference_answer': 'A ponte serializa as mensagens, mas não torna atómica a sequência '
                               'ler-modificar-escrever: pode haver race condition com lost update (a última '
                               'escrita sobrescreve a outra). Resolve-se serializando as operações numa fila '
                               'no lado nativo ou usando operações atómicas.',
           'wrong_answers': ['Como a ponte é serializada nunca há problema nenhum.',
                             'O app simplesmente fecha sempre.']},
 'test9': {'grader': {'all_of': ['n[ãa]o (melhora|ajuda|traz|acelera|h[áa] ganho)|no (real '
                                 ')?(speedup|benefit|improvement|performance gain)|not '
                                 '(improve|help|faster|speed)|pior|slower|overhead',
                                 'multiprocessing|processos|processes',
                                 'I/O|E/S|entrada e sa[ií]da']},
           'reference_answer': 'Para tarefas pesadas de CPU o threading não melhora a performance, pode até '
                               'piorar por overhead, porque o GIL permite uma thread de cada vez. Para '
                               'I/O-bound ajuda. A alternativa é multiprocessing (processos separados) ou '
                               'extensões nativas.',
           'wrong_answers': ['O threading acelera tarefas de CPU em máquinas multi-core.',
                             'O GIL só existe em Windows.']},
 'test10': {'grader': {'all_of': ['bloque|block',
                                  'deadlock',
                                  'buffer|select|default|timeout|goroutine|context']},
            'reference_answer': 'Um envio num canal sem buffer bloqueia até existir um receptor; sem ninguém '
                                'a escutar a goroutine fica bloqueada para sempre e, se todas bloquearem, o '
                                'runtime reporta deadlock. Mitiga-se com um receptor numa goroutine, canal '
                                'com buffer, ou select com default/timeout.',
            'wrong_answers': ['O envio é assíncrono e nunca bloqueia.',
                              'Os dados perdem-se mas não há problema.']}}

HARD = [
  dict(file='hard01_wait_for_swallowed_cancel', title='wait_for when the coroutine swallows cancellation',
    why_hard="In Python 3.12 asyncio.wait_for runs the awaitable inside the caller's task under asyncio.timeout(). If the coroutine catches CancelledError and returns normally, no TimeoutError is raised and wait_for returns the value. Models assume a timeout always yields TimeoutError.",
    expected=['stubborn: cancelled, cleaning up', 'stubborn: cleanup done', 'result: recovered', 'main: done'],
    program=r'''
import asyncio

async def stubborn():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("stubborn: cancelled, cleaning up")
        await asyncio.sleep(0)
        print("stubborn: cleanup done")
        return "recovered"
    return "finished"

async def main():
    try:
        result = await asyncio.wait_for(stubborn(), timeout=0.05)
        print("result:", result)
    except asyncio.TimeoutError:
        print("main: timeout")
    except asyncio.CancelledError:
        print("main: cancelled")
    print("main: done")

asyncio.run(main())
'''),
  dict(file='hard02_taskgroup_cleanup_order', title='TaskGroup failure: order of sibling cleanup',
    why_hard='Requires simulating the event loop step by step: which child finishes first, when the failing child raises, when siblings get cancelled, and how awaits inside finally blocks interleave. The order is a pure consequence of FIFO scheduling, not guessable.',
    expected=['C: finished', 'C: finally start', 'B: finally start', 'C: finally end', 'B: finally end', 'A: finally start', 'A: finally end', "caught: ['B']", 'main: done'],
    program=r'''
import asyncio

async def worker(name, delay_steps, fail=False):
    try:
        for i in range(delay_steps):
            await asyncio.sleep(0)
        if fail:
            raise ValueError(name)
        print(f"{name}: finished")
    finally:
        print(f"{name}: finally start")
        await asyncio.sleep(0)
        print(f"{name}: finally end")

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker("A", 5))
            tg.create_task(worker("B", 2, fail=True))
            tg.create_task(worker("C", 1))
        print("group: clean exit")
    except* ValueError as eg:
        print("caught:", [str(e) for e in eg.exceptions])
    print("main: done")

asyncio.run(main())
'''),
  dict(file='hard03_lock_no_barging', title='asyncio.Lock fairness (no barging)',
    why_hard='A task that releases a Lock and immediately re-acquires it does NOT jump ahead of tasks already waiting (FIFO handoff). Models often assume the releasing task wins or that order is arbitrary.',
    expected=['greedy: got lock 0', 'p1: got lock', 'p2: got lock', 'greedy: got lock 1', 'greedy: got lock 2', 'done'],
    program=r'''
import asyncio

lock = asyncio.Lock()

async def greedy():
    for i in range(3):
        async with lock:
            print(f"greedy: got lock {i}")
            await asyncio.sleep(0)
            await asyncio.sleep(0)
        # releases, then immediately tries to take the lock again

async def polite(name):
    async with lock:
        print(f"{name}: got lock")

async def main():
    g = asyncio.create_task(greedy())
    await asyncio.sleep(0)          # let greedy take the lock first
    p1 = asyncio.create_task(polite("p1"))
    p2 = asyncio.create_task(polite("p2"))
    await asyncio.gather(g, p1, p2)
    print("done")

asyncio.run(main())
'''),
  dict(file='hard04_contextvar_propagation', title='contextvars across tasks, callbacks, threads and executors',
    why_hard='create_task copies the context at creation time; awaiting a coroutine inline shares the context; call_soon captures the current context; asyncio.to_thread copies the context but loop.run_in_executor does not. Five different rules in one program.',
    expected=['t1: sees main-1', 't2: sees main-2', 't1: after sleep sees set-by-t1', 't2: after sleep sees set-by-t2', 'main: after t1 sees main-2', 'inline: sees main-2', 'inline: after sleep sees set-by-inline', 'main: after inline sees set-by-inline', 'cb: sees set-by-inline', 'thread: sees main-3', 'executor: sees root'],
    program=r'''
import asyncio
import contextvars

var = contextvars.ContextVar("var", default="root")

async def child(tag):
    print(f"{tag}: sees {var.get()}")
    var.set(f"set-by-{tag}")
    await asyncio.sleep(0)
    print(f"{tag}: after sleep sees {var.get()}")

async def main():
    var.set("main-1")
    t1 = asyncio.create_task(child("t1"))
    var.set("main-2")
    t2 = asyncio.create_task(child("t2"))
    await t1
    print("main: after t1 sees", var.get())
    await child("inline")
    print("main: after inline sees", var.get())
    await t2
    loop = asyncio.get_running_loop()
    loop.call_soon(lambda: print("cb: sees", var.get()))
    var.set("main-3")
    await asyncio.sleep(0)
    await asyncio.to_thread(lambda: print("thread: sees", var.get()))
    await loop.run_in_executor(None, lambda: print("executor: sees", var.get()))

asyncio.run(main())
'''),
  dict(file='hard05_eager_task_factory', title='Python 3.12 eager task factory',
    why_hard="With eager_task_factory (new in 3.12) a task runs synchronously until its first real suspension inside create_task(). This inverts the classic 'create_task never runs until you await' mental model that most training data teaches.",
    expected=['one: start', 'main: after create one', 'two: start', 'main: after create two', 'one: end', 'two: end', 'main: done'],
    program=r'''
import asyncio

async def job(name):
    print(f"{name}: start")
    await asyncio.sleep(0)
    print(f"{name}: end")

async def main():
    loop = asyncio.get_running_loop()
    loop.set_task_factory(asyncio.eager_task_factory)
    t1 = asyncio.create_task(job("one"))
    print("main: after create one")
    t2 = asyncio.create_task(job("two"))
    print("main: after create two")
    await asyncio.gather(t1, t2)
    print("main: done")

asyncio.run(main())
'''),
  dict(file='hard06_threadlocal_pool_reuse', title='threading.local with reused pool threads',
    why_hard='ThreadPoolExecutor(max_workers=1) reuses the same worker thread, so thread-local state leaks between tasks; a new pool gets a fresh thread; the main thread never sees it. A realistic source of cross-request data leaks.',
    expected=['task0: saw None', 'task1: saw 0', 'task2: saw 1', 'task9: saw None', 'main thread value: unset'],
    program=r'''
import threading
from concurrent.futures import ThreadPoolExecutor

local = threading.local()

def task(n):
    seen = getattr(local, "value", None)
    local.value = n
    return f"task{n}: saw {seen}"

with ThreadPoolExecutor(max_workers=1) as pool:
    for n in range(3):
        print(pool.submit(task, n).result())

with ThreadPoolExecutor(max_workers=1) as pool:
    print(pool.submit(task, 9).result())

print("main thread value:", getattr(local, "value", "unset"))
'''),
  dict(file='hard07_async_gen_finalization', title='Abandoned async generator finalization',
    why_hard="Breaking out of async-for does not run the generator's finally block synchronously. The loop's asyncgen hook schedules aclose() as a separate task, which here is started late and then cancelled by asyncio.run() mid-cleanup, so 'finally end' is never printed.",
    expected=['got 0', 'got 1', 'consume: after loop', 'main: after consume', 'main: end', 'agen: finally start'],
    program=r'''
import asyncio

async def agen():
    try:
        for i in range(5):
            yield i
            await asyncio.sleep(0)
    finally:
        print("agen: finally start")
        await asyncio.sleep(0)
        print("agen: finally end")

async def consume():
    async for x in agen():
        print("got", x)
        if x == 1:
            break
    print("consume: after loop")

async def main():
    await consume()
    print("main: after consume")
    await asyncio.sleep(0)
    print("main: end")

asyncio.run(main())
'''),
  dict(file='hard08_shield_and_cancel', title='asyncio.shield: cancelling the outer does not cancel the inner',
    why_hard='Cancelling the awaiting task leaves the shielded inner task running to completion. Requires tracking exactly when each cancellation and completion becomes visible across event-loop steps.',
    expected=['inner: start', 'outer: cancelled', 'main: o cancelled = True', 'main: inner done = False', 'inner: done', 'main: inner result = 42', 'main: end'],
    program=r'''
import asyncio

async def inner():
    try:
        print("inner: start")
        for _ in range(4):
            await asyncio.sleep(0)
        print("inner: done")
        return 42
    except asyncio.CancelledError:
        print("inner: cancelled")
        raise

async def outer(task):
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        print("outer: cancelled")
        raise

async def main():
    task = asyncio.create_task(inner())
    o = asyncio.create_task(outer(task))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    o.cancel()
    try:
        await o
    except asyncio.CancelledError:
        print("main: o cancelled =", o.cancelled())
    print("main: inner done =", task.done())
    print("main: inner result =", await task)
    print("main: end")

asyncio.run(main())
'''),
]

os.makedirs("tests", exist_ok=True)
for key, fields in UPDATES.items():
    found = glob.glob(os.path.join("tests", key + "_*.json"))
    if not found:
        print("AVISO: nao achei tests/%s_*.json, pulei" % key); continue
    path = found[0]
    data = json.load(open(path, encoding="utf-8"))
    fields = dict(fields)
    for old, new in fields.pop("prompt_replace", []):
        data["prompt"] = data["prompt"].replace(old, new)
    data.update(fields)
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("atualizado", path)
for n, h in enumerate(HARD, 1):
    data = {"id": "hard_%02d" % n, "title": h["title"], "why_hard": h["why_hard"],
            "prompt": TEMPLATE % h["program"].strip("\n"),
            "expected_stdout": h["expected"], "reference_answer": h["expected"],
            "wrong_answers": [json.dumps({"stdout": h["expected"][::-1]}), json.dumps({"stdout": h["expected"][:-1]})]}
    path = os.path.join("tests", h["file"] + ".json")
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("criado    ", path)
print("\nPronto. Agora: python runner.py --selftest")
if sys.version_info[:2] != (3, 12):
    print("Nota: o gabarito dos hard foi gerado no Python 3.12; seu Python e", sys.version.split()[0])