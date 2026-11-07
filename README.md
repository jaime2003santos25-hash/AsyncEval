# ⚡ AsyncEval — LLM Concurrency & Asynchronous Logic Benchmark

**AsyncEval** é um framework de benchmark automatizado desenhado para avaliar a precisão, eficiência e raciocínio técnico de Large Language Models (LLMs) diante de vulnerabilidades críticas de concorrência, *race conditions*, *deadlocks* e gestão assíncrona de memória.

Desenvolvido inteiramente num ambiente móvel de engenharia (Acode + Terminal Alpine Linux) para a avaliação de modelos no hackathon micro1.

---

## 📌 Por que este Benchmark é Relevante?

A maioria dos benchmarks tradicionais avalia conhecimento superficial ou sintaxe básica. O **AsyncEval** submete os modelos a falhas silenciosas de sistemas concorrentes reais, tais como:
* Perda de atomicidade em operações I/O assíncronas.
* Inanição de threads no Event Loop (Libuv/Node.js).
* Bloqueios de memória por *closures* e contexto global.
* Concorrência na ponte nativa do React Native e *deadlocks* em canais de Go/Python.

---

## 🛠️ Estrutura do Repositório

```text
eval-concurrency-limits/
├── tests/
│   ├── test1_race_condition.json
│   ├── test2_deadlock_detection.json
│   ├── test3_event_loop_order.json
│   ├── test4_memory_leak_closure.json
│   ├── test5_promise_all_settled_bail.json
│   ├── test6_asyncio_race.json
│   ├── test7_thread_pool_starvation.json
│   ├── test8_react_native_bridge_race.json
│   ├── test9_python_gil_multithreading.json
│   └── test10_goroutine_channel_deadlock.json
├── runner.py
├── requirements.txt
├── SUMMARY.md
└── evaluation_report.json

---

🚦 Como Executar

​1. Dependências
Bash (Terminal) 
pip install -r requirements.txt

2. Definir a Chave da API 
Bash (Terminal) 
export OPENROUTER_API_KEY="sua_chave_aqui"

3. Iniciar a Avaliação Multi-Modelo 

Bash (Terminal) 
python runner.py

---

📊 Relatórios de Saída

Ao finalizar, o benchmark gera:

1) ​evaluation_report.json: Relatório técnico completo contendo métricas e o raciocínio detalhado de cada modelo.

2) ​SUMMARY.md: Tabela comparativa consolidando latência média, taxa de sucesso e contagem de tokens por modelo.