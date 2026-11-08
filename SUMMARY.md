# AsyncEval - Resultados

Data: 2026-11-08 | trials por teste: 3 | temperatura: 0.7

| Modelo | Trials corrigidos | Taxa de acerto | pass@k | pass^k | Latencia media | Tokens | Custo ($) |
|---|---|---|---|---|---|---|---|
| GPT-4o-mini (baseline) | 24 (+0 erros) | 0.167 | 2/8 | 1/8 | 8.73s | 20722 | 0.0092 |
| DeepSeek chat | 24 (+0 erros) | 0.167 | 2/8 | 1/8 | 21.0s | 16813 | 0.0106 |
| Gemini 3.8 Flash (free tier) | 10 (+14 erros) | 0.9 | 4/8 | 2/8 | 194.27s | 50010 | 0 |
| Gemini 3.5 Flash-Lite (free tier) | 24 (+0 erros) | 0.292 | 3/8 | 2/8 | 3.04s | 27817 | 0 |
| Gemma 4 31B (open, free tier) | 24 (+0 erros) | 0.458 | 5/8 | 3/8 | 164.76s | 130630 | 0 |

## Acertos por teste (acertos/trials)

| Teste | GPT-4o-mini (baseline) | DeepSeek chat | Gemini 3.8 Flash (free tier) | Gemini 3.5 Flash-Lite (free tier) | Gemma 4 31B (open, free tier) |
|---|---|---|---|---|---|
| hard01_wait_for_swallowed_cancel | 0/3 | 0/3 | 1/2 | 0/3 | 0/3 |
| hard02_taskgroup_cleanup_order | 0/3 | 0/3 | 3/3 | 0/3 | 1/3 |
| hard03_lock_no_barging | 0/3 | 0/3 | 3/3 | 1/3 | 1/3 |
| hard04_contextvar_propagation | 0/3 | 0/3 | - | 0/3 | 0/3 |
| hard05_eager_task_factory | 1/3 | 3/3 | 2/2 | 3/3 | 3/3 |
| hard06_threadlocal_pool_reuse | 3/3 | 1/3 | - | 3/3 | 3/3 |
| hard07_async_gen_finalization | 0/3 | 0/3 | - | 0/3 | 0/3 |
| hard08_shield_and_cancel | 0/3 | 0/3 | - | 0/3 | 3/3 |
