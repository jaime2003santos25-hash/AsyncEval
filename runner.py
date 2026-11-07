import os
import json
import time
import sys
import threading
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Dicionário otimizado com as 5 IAs de topo para o AsyncEval
MODELS_CONFIG = {
    "meta-llama/llama-3.1-70b-instruct": {
        "name": "Meta Llama 3.1 70B",
        "fallbacks": ["meta-llama/llama-3.3-70b-instruct"],
        "logo": r"""
    __          __                  ___ ____ 
   / /   層 __ _/ /_____ _          |__ <  _/ 
  / /   / / _  / __/ __ `/           /_/<: ہوئے۔ 
 / /___/ / (_/ / /_/ /_/ /          ___/ / /  
/_____/_/\__,_/\__/\__,_/          /____/__/  
        """
    },
    "nvidia/llama-3.1-nemotron-70b-instruct": {
        "name": "NVIDIA Nemotron 70B",
        "fallbacks": ["meta-llama/llama-3.1-70b-instruct"],
        "logo": r"""
   _   ___   _____ ____  ____  ___   
  / | / / | / /  _/ __ \/  _/ /   |  
 /  |/ /| |/ // // / / // // /| |  
/ /|  / |  // // /_/ // // ___ |  
/_/ |_/  |_/___/____/___/_/  |_|  
        """
    },
    "google/gemma-2-27b-it": {
        "name": "Google Gemma 2 27B",
        "fallbacks": ["google/gemma-2-9b-it:free"],
        "logo": r"""
   ______                             __ 
  / ____/___  ____ ___  ____ ___     / / 
 / / __/ __ \/ __ `__ \/ __ `__ \   / /  
/ /_/ / /_/ / / / / / / / / / / /  /_/   
\____/\____/_/ /_/ /_/_/ /_/ /_/  (_)    
        """
    },
    "openai/gpt-4o-mini": {
        "name": "OpenAI GPT-4o-mini",
        "fallbacks": ["openai/gpt-4o"],
        "logo": r"""
   ____  ____  ______   __               _
  / __ \/ __ \/_  __/  / /   g p t - 4 o  
 / / / / /_/ / / /    / /___ min i     
/___/ .___/ /_/    /_____/          
        """
    },
    "deepseek/deepseek-chat": {
        "name": "DeepSeek V3",
        "fallbacks": ["deepseek/deepseek-chat:free"],
        "logo": r"""
   ____  __________________ _____ ______ __ __
  / __ \/ ____/ ____/ ___// ___// ____// //_/
 / / / / __/ / __/  \__ \ \__ \/ __/  / ,<   
/ /_/ / /___/ /___ ___/ /___/ / /___ / /| |  
\____/_____/_____//____//____/_/_____//_/ |_|  
        """
    }
}

def spin(message, stop_event):
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r    {spinner[i]} {message}...")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(spinner)
    sys.stdout.write("\r\033[K")

def execute_request_with_fallback(primary_model, fallbacks, headers, payload):
    models_to_try = [primary_model] + fallbacks
    for model in models_to_try:
        payload["model"] = model
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response, model
        except Exception:
            continue
    return None, primary_model

def run_evaluation():
    if not OPENROUTER_API_KEY:
        print("\n❌ Erro: A variável de ambiente OPENROUTER_API_KEY não está configurada.\n")
        return

    tests_dir = "./tests"
    if not os.path.exists(tests_dir):
        print("\n❌ Erro: A pasta 'tests/' não foi encontrada.\n")
        return

    test_files = sorted([f for f in os.listdir(tests_dir) if f.endswith(".json")])
    print("\n" + "="*65)
    print(f"🚀 [ASYNC-EVAL BENCHMARK] A iniciar {len(test_files)} testes em {len(MODELS_CONFIG)} IAs selecionadas...")
    print("="*65 + "\n")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    all_models_results = []
    grand_total_tokens = 0
    start_global_time = time.time()

    for primary_model, config in MODELS_CONFIG.items():
        print(config["logo"])
        print(f"🤖 A avaliar modelo: {config['name']} ({primary_model})")
        print("-" * 65 + "\n")
        
        model_results = []
        model_tokens = 0
        success_count = 0
        start_model_time = time.time()

        for idx, file_name in enumerate(test_files, 1):
            file_path = os.path.join(tests_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                test_data = json.load(f)

            test_title = test_data.get('title', file_name)
            print(f"  [Teste {idx}/{len(test_files)}] {test_title}")
            
            payload = {
                "messages": [
                    {"role": "system", "content": "You are an expert senior software engineer specialized in asynchronous systems and concurrency."},
                    {"role": "user", "content": test_data.get("prompt")}
                ]
            }

            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spin, args=("A processar análise de código", stop_event))
            
            start_test_time = time.time()
            spinner_thread.start()
            
            response, used_model = execute_request_with_fallback(primary_model, config["fallbacks"], headers, payload)
            
            stop_event.set()
            spinner_thread.join()
            duration = time.time() - start_test_time

            if response and response.status_code == 200:
                res_json = response.json()
                answer = res_json["choices"][0]["message"]["content"]
                
                usage = res_json.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                model_tokens += tokens
                success_count += 1
                
                fallback_info = f" (via {used_model})" if used_model != primary_model else ""
                print(f"    ✅ Sucesso! (⏱️ {duration:.2f}s | 📊 Tokens: {tokens}){fallback_info}\n")
                
                model_results.append({
                    "id": test_data.get("id"),
                    "title": test_title,
                    "status": "success",
                    "model_used": used_model,
                    "duration_seconds": round(duration, 2),
                    "tokens_used": tokens,
                    "response": answer
                })
            else:
                print(f"    ⚠️ Erro: Nenhum modelo/fallback respondeu no momento.\n")
                model_results.append({
                    "id": test_data.get("id"),
                    "title": test_title,
                    "status": "model_unavailable",
                    "error": "Todos os provedores do modelo falharam."
                })

        model_duration = time.time() - start_model_time
        grand_total_tokens += model_tokens
        
        all_models_results.append({
            "model_name": config["name"],
            "model_key": primary_model,
            "execution_time_seconds": round(model_duration, 2),
            "tokens_consumed": model_tokens,
            "success_rate": f"{success_count}/{len(test_files)}",
            "avg_latency": round(model_duration / len(test_files), 2) if test_files else 0,
            "results": model_results
        })
        print("\n" + "="*65 + "\n")

    total_global_duration = time.time() - start_global_time

    # Exportar JSON
    report = {
        "total_execution_time_seconds": round(total_global_duration, 2),
        "total_tokens_consumed": grand_total_tokens,
        "models_tested_count": len(MODELS_CONFIG),
        "models_evaluation": all_models_results
    }
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    # Exportar Markdown
    with open("SUMMARY.md", "w", encoding="utf-8") as f:
        f.write("# 📊 AsyncEval Benchmark Summary (Top 5 Models)\n\n")
        f.write(f"- **Tempo Total:** {round(total_global_duration, 2)}s\n")
        f.write(f"- **Total de Tokens:** {grand_total_tokens}\n\n")
        f.write("| Modelo | Sucesso | Tempo Total | Latência Média | Tokens |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for m in all_models_results:
            f.write(f"| {m['model_name']} | {m['success_rate']} | {m['execution_time_seconds']}s | {m['avg_latency']}s | {m['tokens_consumed']} |\n")

    print("🏆 SUMMARY SCORECARD")
    print("="*65)
    for m in all_models_results:
        print(f"🔹 {m['model_name']}: {m['success_rate']} Testes OK | Média: {m['avg_latency']}s/teste | Tokens: {m['tokens_consumed']}")
    print("-" * 65)
    print(f"\n🏁 Benchmark concluído em {total_global_duration:.2f}s!")
    print("📄 Relatórios guardados em: evaluation_report.json e SUMMARY.md\n")

if __name__ == "__main__":
    run_evaluation()
