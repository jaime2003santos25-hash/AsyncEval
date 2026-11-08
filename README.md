# AsyncEval — Can LLMs predict what asyncio actually does?

**What it tests.** Whether an LLM can predict the *exact* stdout of small, deterministic Python 3.12 concurrency programs (asyncio, threads, contextvars). Each task hinges on one real scheduling, cancellation or context rule that is easy to get wrong by intuition. The correct answer is obtained by actually running the program, so every task has exactly one verifiable answer.

**Who relies on this, and what a failure costs.** Backend and infrastructure engineers increasingly use LLMs to review and debug async code: timeout and cancellation handling, lock fairness, request-scoped context, resource cleanup on shutdown. A model that mis-predicts these behaviours will approve code that ignores timeouts, leaks data between requests, or hangs or loses cleanup at shutdown. These bugs are hard to reproduce in production, which is why a wrong "this looks fine" from an assistant is costly.

## Tasks (8, CPython 3.12.3)

| Task | Rule being tested |
|---|---|
| `hard01_wait_for_swallowed_cancel` | In 3.12, `wait_for` returns the value (no `TimeoutError`) if the coroutine swallows the cancellation |
| `hard02_taskgroup_cleanup_order` | Interleaving of sibling cancellation and `finally`+`await` inside a `TaskGroup` |
| `hard03_lock_no_barging` | `asyncio.Lock` FIFO handoff: the releasing task cannot re-acquire ahead of waiters |
| `hard04_contextvar_propagation` | `create_task` copies context; inline await shares it; `call_soon` captures it; `to_thread` copies it; `run_in_executor` does not |
| `hard05_eager_task_factory` | 3.12 eager tasks run synchronously until their first suspension |
| `hard06_threadlocal_pool_reuse` | `threading.local` leaks across tasks on a reused pool thread |
| `hard07_async_gen_finalization` | Abandoned async generator cleanup is scheduled late and cancelled mid-`finally` by `asyncio.run` |
| `hard08_shield_and_cancel` | Cancelling the awaiter of `asyncio.shield` does not cancel the inner task |

Each task is one JSON file in `tests/` containing the prompt (the program is embedded in it), `expected_stdout` (the reference solution), `why_hard`, and a few deliberately wrong answers used to test the grader. The expected output is **never shown to the model**.

## Grading

Code-based, outcome-only, no LLM judge. The model must end its reply with `{"stdout": [...]}`. A trial passes only if the list equals the reference lines exactly (trailing whitespace ignored). A `partial` score (fraction of matching line positions) is stored for analysis but is not what is reported.

**How tasks and grader were validated (no API calls):**
- `python verify_references.py` re-runs every program 5 times and checks the output is identical each time and equals `expected_stdout`.
- `python runner.py --selftest` checks that the grader accepts the reference answer and rejects wrong ones (reversed, truncated, empty).
- Reference outputs come from real execution, not from a model. They were produced on CPython 3.12.3 and re-verified on CPython 3.12.14 (Alpine Linux, where the runs were executed): all eight programs gave identical output on 5 runs each and matched the references.

## How to run

```bash
python --version                 # tasks target 3.12.x
pip install -r requirements.txt
python verify_references.py      # re-executes the programs (free, offline)
python runner.py --selftest      # validates the grader (free, offline)

export OPENROUTER_API_KEY=...    # only for the OpenRouter models
export GEMINI_API_KEY=...        # Google AI Studio free-tier key, no billing needed
python -u runner.py --trials 3 --max-tokens 8000 --workers 3 \
  --only hard01_wait_for_swallowed_cancel hard02_taskgroup_cleanup_order \
  hard03_lock_no_barging hard04_contextvar_propagation hard05_eager_task_factory \
  hard06_threadlocal_pool_reuse hard07_async_gen_finalization hard08_shield_and_cancel

python analyze.py                # writes FAILURES.md: most common wrong predictions per task
```

Finished trials are saved in `transcripts/` and skipped on re-runs, so an interrupted run resumes and only retries trials that failed for infrastructure reasons (network, quota, truncation). `--skip <model-id>` avoids calling a model whose quota is exhausted. Output: `SUMMARY.md`, `evaluation_report.json`, one transcript per trial. Models are listed in the `MODELS` block at the top of `runner.py`. No API keys are stored in the repository.

## Results

Runs: 2026-11-07 to 2026-11-08 · temperature 0.7 · max_tokens 8000 (the six Gemma trials that were truncated at 8000 tokens were re-run with 16000) · 3 trials per task · same tasks, prompt and grader for every model.

Trials that failed for infrastructure reasons (network errors, free-tier quota, truncated output) are excluded from the pass rates; they are never counted as model failures.

| Model | Valid trials | Pass rate | Tasks solved in 3/3 trials | Tasks solved in ≥1 trial | Total tokens | Cost |
|---|---|---|---|---|---|---|
| GPT-4o-mini | 24/24 | 16.7% | 1/8 | 2/8 | 20,722 | $0.0092 |
| DeepSeek chat | 24/24 | 16.7% | 1/8 | 2/8 | 16,813 | $0.0106 |
| Gemini 3.5 Flash-Lite (free tier) | 24/24 | 29.2% | 2/8 | 3/8 | 27,817 | $0 |
| Gemma 4 31B (free tier) | 24/24 | 45.8% | 3/8 | 5/8 | 130,630 | $0 |
| Gemini 3.8 Flash (free tier), **partial** | 10/24 | 90% (9/10) | n/a | n/a | 50,010 | $0 |

**Gemini 3.8 Flash is partial.** Its free tier allows 20 requests per day, so only 10 of 24 trials completed (hard01 ×2, hard02 ×3, hard03 ×3, hard05 ×2). Its pass rate covers those tasks only and is not comparable to the other rows. Because of budget limits, no larger paid frontier model was tested, so this eval makes no claim about the strongest models available.

Passed trials per task (passed/valid):

| Task | GPT-4o-mini | DeepSeek | Gemini 3.8 Flash (partial) | Gemini 3.5 Flash-Lite | Gemma 4 31B |
|---|---|---|---|---|---|
| hard01_wait_for_swallowed_cancel | 0/3 | 0/3 | 1/2 | 0/3 | 0/3 |
| hard02_taskgroup_cleanup_order | 0/3 | 0/3 | 3/3 | 0/3 | 1/3 |
| hard03_lock_no_barging | 0/3 | 0/3 | 3/3 | 1/3 | 1/3 |
| hard04_contextvar_propagation | 0/3 | 0/3 | no data | 0/3 | 0/3 |
| hard05_eager_task_factory | 1/3 | 3/3 | 2/2 | 3/3 | 3/3 |
| hard06_threadlocal_pool_reuse | 3/3 | 1/3 | no data | 3/3 | 3/3 |
| hard07_async_gen_finalization | 0/3 | 0/3 | no data | 0/3 | 0/3 |
| hard08_shield_and_cancel | 0/3 | 0/3 | no data | 0/3 | 3/3 |

## Failure analysis

`FAILURES.md` (generated by `analyze.py`) lists, for every task, the most common wrong predictions and the first line where they diverge from the reference. Summary:

- **hard01 (wait_for):** 1 of 14 valid trials passed. In 12 of the 13 failures the model predicted that `main` prints `main: timeout`. All five models produced this answer, including Gemini 3.8 Flash. They assume a timeout always raises `TimeoutError`, but in 3.12 `wait_for` returns the value when the coroutine swallows the cancellation. This behaviour is documented: the docstring of `asyncio.wait_for` in CPython 3.12 states that a value returned after the task suppresses the cancellation is returned to the caller.
- **hard02 (TaskGroup), the "came close" task:** 4 of 15 passed (Gemini 3.8 Flash 3, Gemma 1). Flash-Lite and Gemma correctly predicted that the siblings are cancelled, but misordered one step: they placed `A: finally start` before `B: finally end`. DeepSeek and GPT-4o-mini predicted `A: finished`, i.e. they missed that `A` is cancelled and never finishes.
- **hard03 (Lock fairness):** 5 of 15 passed. 9 of the 10 failures gave the same wrong answer: `greedy` takes the lock three times before `p1` and `p2` get it. This mistake appeared in four different models. `asyncio.Lock` hands the lock to waiting tasks first.
- **hard04 (contextvars):** 0 of 12 passed. The most frequent wrong answers (5 of the 12 failed trials) all predicted `executor: sees main-3`; the correct value is `root`, because `run_in_executor` does not copy the context. They also let `t1` run to completion before `t2` prints, and GPT-4o-mini predicted that a task sees a value set after `create_task`.
- **hard05 (eager tasks) and hard06 (thread-local):** mostly solved (12/14 and 10/12). They show the grader accepts correct answers and that models are not failing everything. The failures on hard05 came from GPT-4o-mini and on hard06 from DeepSeek. These two tasks do not expose a strong limitation.
- **hard07 (async generator finalization):** 0 of 12 passed. In all 11 failures shown in `FAILURES.md` the model predicted that `agen: finally end` is printed. It never is: the cleanup task is cancelled by `asyncio.run` in the middle of `finally`. The models disagree on where the cleanup runs, but all assumed it completes.
- **hard08 (shield):** 3 of 12 passed (only Gemma, 3/3). In all 6 failures shown the model predicted `main: inner done = True`; the correct value is `False`, because the shielded task has not finished yet when `main` prints it.

Example failing transcripts (each is a trial from a model that passed 0 of 3 on that task):
- hard01: `transcripts/gemma-4-31b-it/hard01_wait_for_swallowed_cancel_trial1.json`
- hard02: `transcripts/gemini-3.5-flash-lite/hard02_taskgroup_cleanup_order_trial1.json`
- hard03: `transcripts/deepseek_deepseek-chat/hard03_lock_no_barging_trial1.json`
- hard04: `transcripts/gemini-3.5-flash-lite/hard04_contextvar_propagation_trial1.json`
- hard07: `transcripts/gemma-4-31b-it/hard07_async_gen_finalization_trial1.json`
- hard08: `transcripts/openai_gpt-4o-mini/hard08_shield_and_cancel_trial1.json`

## Main failure mode / hot take

The models reason about what async code is *meant* to do, not about the exact event-loop schedule. Failures are not random noise: the same wrong answer repeats across different models (9 of 10 failures on hard03; 7 identical wrong answers on hard01, produced by all five models), which points to shared misconceptions rather than sampling variance. The typical errors treat asynchronous steps as immediate (cleanup, cancellation and finalization "just happen") and miss how many event-loop turns each step takes.

The two models that spent the most tokens per trial (Gemma 4 and Gemini 3.8 Flash, about 5k total tokens per trial including the prompt, vs about 0.7–1.2k for the others) scored highest. This is a correlation on a small sample, not a proven cause. A model with code execution would solve all eight tasks by running them, so the gap measured here is mental simulation of the scheduler, which matters whenever code is reviewed without being run.

## Limitations (stated honestly)

- Tasks target CPython 3.12.3. Some behaviours (`hard01`, `hard05`) depend on the version, and `hard07` depends on CPython's garbage-collection and asyncgen-finalization behaviour. Other versions may print different output.
- Single-turn, exact-match grading is all-or-nothing, so a single wrong line fails a trial.
- Only 3 trials per task at temperature 0.7. Model outputs are stochastic, so a re-run may differ slightly; the transcript of every reported trial is included.
- Free-tier Gemini/Gemma models were used because of budget limits, and they are not the strongest models available. Gemini 3.8 Flash is partial (10 of 24 trials) because of the free-tier daily limit. Results describe only the models listed above.
- The ten earlier prompts (`tests/test1…test10`) are kept for transparency but are **not** part of the reported results. They are open-ended explanation prompts graded by keyword regexes, which is a weaker grader than exact match.

## Cost and runtime

OpenRouter models (GPT-4o-mini and DeepSeek) cost about $0.02 in total; Gemini and Gemma ran on Google's free tier ($0). Average latency per call: 3–21 s for the fast models, about 165 s (Gemma 4) and 195 s (Gemini 3.8 Flash) for the models that reason at length. A full 3-trial run of the 8 tasks over 5 models is 120 calls.

## Provenance and AI use

- **Before the hackathon work in this repo:** nothing reused except generic tools (Python, `requests`).
- **First version:** ten explanation prompts and a runner that counted a trial as "success" if the API answered. It had no reference answers and no grader. It was drafted with Google Gemini and then replaced by the current design.
- **Redesign:** the runner with automated grading, the eight `hard` tasks, the verification and analysis scripts (`upgrade_tests.py` created the hard tests and added graders to the older prompts) and the first draft of this README were developed with Claude (Anthropic) in a chat session. Everything was run from a phone (Acode + Alpine Linux).
- **Author review:** I re-ran `verify_references.py` on my own phone (CPython 3.12.14): all eight programs gave identical output over 5 runs and matched the references. For `hard01` and `hard03` I checked the expected behaviour against the standard-library source on that interpreter: the `wait_for` docstring states that a value returned after the task suppresses the cancellation is returned, and `Lock.acquire` only takes the lock immediately when no waiter is queued. The other reference outputs come from real execution, and I did not derive them independently by hand. The task ideas were drafted with AI assistance (see above), and I kept only tasks whose output I could reproduce by running the code.
- No external benchmark was copied. All data is synthetic (the programs themselves). No confidential data. No API keys in the repository.

## Repository layout

```
tests/                   one JSON per task (prompt, expected_stdout, why_hard); hard01-08 are the reported tasks
runner.py                harness: runs N trials per model, grades by code, writes reports
verify_references.py     re-executes the programs and checks them against the references
analyze.py               summarizes the most common wrong predictions per task (writes FAILURES.md)
upgrade_tests.py         one-off script that created the hard tests and added graders to the older prompts
transcripts/<model>/     one JSON per trial (prompt, full reply, grade)
SUMMARY.md               results table
FAILURES.md              failure summary per task
evaluation_report.json   results in machine-readable form
requirements.txt
```