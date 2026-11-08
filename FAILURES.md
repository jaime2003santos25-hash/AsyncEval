# Resumo das falhas (gerado por analyze.py)

## hard01_wait_for_swallowed_cancel

Acertos: 1/14
Esperado: ['stubborn: cancelled, cleaning up', 'stubborn: cleanup done', 'result: recovered', 'main: done']

- 7 falha(s) previram ['stubborn: cancelled, cleaning up', 'stubborn: cleanup done', 'main: timeout', 'main: done']
  modelos: deepseek/deepseek-chat, gemini-3.5-flash-lite, gemini-3.8-flash, gemma-4-31b-it, openai/gpt-4o-mini
  1a linha diferente (#3): previu 'main: timeout', esperado 'result: recovered'
- 3 falha(s) previram ['main: timeout', 'main: done', 'stubborn: cancelled, cleaning up', 'stubborn: cleanup done']
  modelos: deepseek/deepseek-chat, gemini-3.5-flash-lite, gemma-4-31b-it
  1a linha diferente (#1): previu 'main: timeout', esperado 'stubborn: cancelled, cleaning up'
- 2 falha(s) previram ['main: timeout', 'main: done']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#1): previu 'main: timeout', esperado 'stubborn: cancelled, cleaning up'

## hard02_taskgroup_cleanup_order

Acertos: 4/15
Esperado: ['C: finished', 'C: finally start', 'B: finally start', 'C: finally end', 'B: finally end', 'A: finally start', 'A: finally end', "caught: ['B']", 'main: done']

- 3 falha(s) previram ['C: finished', 'C: finally start', 'C: finally end', 'B: finally start', 'B: finally end', 'A: finished', 'A: finally start', 'A: finally end', "caught: ['B']", 'main: done']
  modelos: deepseek/deepseek-chat
  1a linha diferente (#3): previu 'C: finally end', esperado 'B: finally start'
- 2 falha(s) previram ['C: finished', 'C: finally start', 'B: finally start', 'C: finally end', 'A: finally start', 'B: finally end', 'A: finally end', "caught: ['B']", 'main: done']
  modelos: gemini-3.5-flash-lite, gemma-4-31b-it
  1a linha diferente (#5): previu 'A: finally start', esperado 'B: finally end'
- 1 falha(s) previram ['A: finished', 'C: finished', 'B: finally start', 'B: finally end', 'A: finally start', 'A: finally end', 'C: finally start', 'C: finally end', "caught: ['B']", 'main: done']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#1): previu 'A: finished', esperado 'C: finished'

## hard03_lock_no_barging

Acertos: 5/15
Esperado: ['greedy: got lock 0', 'p1: got lock', 'p2: got lock', 'greedy: got lock 1', 'greedy: got lock 2', 'done']

- 9 falha(s) previram ['greedy: got lock 0', 'greedy: got lock 1', 'greedy: got lock 2', 'p1: got lock', 'p2: got lock', 'done']
  modelos: deepseek/deepseek-chat, gemini-3.5-flash-lite, gemma-4-31b-it, openai/gpt-4o-mini
  1a linha diferente (#2): previu 'greedy: got lock 1', esperado 'p1: got lock'
- 1 falha(s) previram ['greedy: got lock 0', 'p1: got lock', 'p2: got lock', 'done']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#4): previu 'done', esperado 'greedy: got lock 1'

## hard04_contextvar_propagation

Acertos: 0/12
Esperado: ['t1: sees main-1', 't2: sees main-2', 't1: after sleep sees set-by-t1', 't2: after sleep sees set-by-t2', 'main: after t1 sees main-2', 'inline: sees main-2', 'inline: after sleep sees set-by-inline', 'main: after inline sees set-by-inline', 'cb: sees set-by-inline', 'thread: sees main-3', 'executor: sees root']

- 3 falha(s) previram ['t1: sees main-1', 't1: after sleep sees set-by-t1', 'main: after t1 sees main-2', 'inline: sees main-2', 'inline: after sleep sees set-by-inline', 'main: after inline sees set-by-inline', 't2: sees main-2', 't2: after sleep sees set-by-t2', 'cb: sees set-by-inline', 'thread: sees main-3', 'executor: sees main-3']
  modelos: gemini-3.5-flash-lite
  1a linha diferente (#2): previu 't1: after sleep sees set-by-t1', esperado 't2: sees main-2'
- 1 falha(s) previram ['t1: sees main-1', 't1: after sleep sees set-by-t1', 'main: after t1 sees main-2', 'inline: sees main-2', 'inline: after sleep sees set-by-inline', 'main: after inline sees set-by-inline', 't2: sees set-by-inline', 't2: after sleep sees set-by-t2', 'cb: sees set-by-t2', 'thread: sees main-3', 'executor: sees main-3']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#2): previu 't1: after sleep sees set-by-t1', esperado 't2: sees main-2'
- 1 falha(s) previram ['t1: sees main-2', 't1: after sleep sees set-by-t1', 'main: after t1 sees main-2', 'inline: sees main-2', 'inline: after sleep sees set-by-inline', 'main: after inline sees set-by-inline', 't2: sees set-by-inline', 't2: after sleep sees set-by-t2', 'cb: sees set-by-t2', 'thread: sees main-3', 'executor: sees main-3']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#1): previu 't1: sees main-2', esperado 't1: sees main-1'

## hard05_eager_task_factory

Acertos: 12/14
Esperado: ['one: start', 'main: after create one', 'two: start', 'main: after create two', 'one: end', 'two: end', 'main: done']

- 2 falha(s) previram ['one: start', 'two: start', 'main: after create one', 'main: after create two', 'one: end', 'two: end', 'main: done']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#2): previu 'two: start', esperado 'main: after create one'

## hard06_threadlocal_pool_reuse

Acertos: 10/12
Esperado: ['task0: saw None', 'task1: saw 0', 'task2: saw 1', 'task9: saw None', 'main thread value: unset']

- 1 falha(s) previram ['task0: saw None', 'task1: saw None', 'task2: saw None', 'task9: saw None', 'main thread value: unset']
  modelos: deepseek/deepseek-chat
  1a linha diferente (#2): previu 'task1: saw None', esperado 'task1: saw 0'
- 1 falha(s) previram ['task0: saw None', 'task1: saw 0', 'task2: saw 1', 'task9: saw 2', 'main thread value: unset']
  modelos: deepseek/deepseek-chat
  1a linha diferente (#4): previu 'task9: saw 2', esperado 'task9: saw None'

## hard07_async_gen_finalization

Acertos: 0/12
Esperado: ['got 0', 'got 1', 'consume: after loop', 'main: after consume', 'main: end', 'agen: finally start']

- 5 falha(s) previram ['got 0', 'got 1', 'agen: finally start', 'agen: finally end', 'consume: after loop', 'main: after consume', 'main: end']
  modelos: gemini-3.5-flash-lite, gemma-4-31b-it
  1a linha diferente (#3): previu 'agen: finally start', esperado 'consume: after loop'
- 3 falha(s) previram ['got 0', 'got 1', 'consume: after loop', 'main: after consume', 'main: end', 'agen: finally start', 'agen: finally end']
  modelos: openai/gpt-4o-mini
  tamanho diferente: previu 7 linhas, esperado 6
- 3 falha(s) previram ['got 0', 'got 1', 'consume: after loop', 'agen: finally start', 'agen: finally end', 'main: after consume', 'main: end']
  modelos: deepseek/deepseek-chat
  1a linha diferente (#4): previu 'agen: finally start', esperado 'main: after consume'

## hard08_shield_and_cancel

Acertos: 3/12
Esperado: ['inner: start', 'outer: cancelled', 'main: o cancelled = True', 'main: inner done = False', 'inner: done', 'main: inner result = 42', 'main: end']

- 2 falha(s) previram ['inner: start', 'inner: done', 'main: o cancelled = True', 'main: inner done = True', 'main: inner result = 42', 'main: end']
  modelos: openai/gpt-4o-mini
  1a linha diferente (#2): previu 'inner: done', esperado 'outer: cancelled'
- 2 falha(s) previram ['inner: start', 'inner: done', 'outer: cancelled', 'main: o cancelled = True', 'main: inner done = True', 'main: inner result = 42', 'main: end']
  modelos: deepseek/deepseek-chat
  1a linha diferente (#2): previu 'inner: done', esperado 'outer: cancelled'
- 2 falha(s) previram ['inner: start', 'outer: cancelled', 'main: o cancelled = True', 'inner: done', 'main: inner done = True', 'main: inner result = 42', 'main: end']
  modelos: deepseek/deepseek-chat, gemini-3.5-flash-lite
  1a linha diferente (#4): previu 'inner: done', esperado 'main: inner done = False'
