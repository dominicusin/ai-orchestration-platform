import os
import requests
import time

# [Предположение] Промпт может потребовать адаптации под специфику конкретной модели
PROMPT = "Convert this C++ code to idiomatic Haskell. Output ONLY valid Haskell code without markdown wrappers.\n\nCode:\n{code}"

def ask_groq(cpp_code, api_key, model="llama3-8b-8192"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(code=cpp_code)}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        return f"-- Ошибка Groq: {resp.status_code} {resp.text}"
    except Exception as e:
        return f"-- Ошибка соединения: {e}"

def ask_gemini(cpp_code, api_key, model="gemini-1.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT.format(code=cpp_code)}]}]
    }
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        return f"-- Ошибка Gemini: {resp.status_code} {resp.text}"
    except Exception as e:
        return f"-- Ошибка соединения: {e}"

def process_with_api(src_dir, dest_dir, provider="groq", api_key=""):
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".cpp", ".h", ".hpp")):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    cpp_code = f.read()
                
                print(f"Обработка {file_path} через {provider}...")
                
                if provider == "groq":
                    haskell_code = ask_groq(cpp_code, api_key)
                elif provider == "gemini":
                    haskell_code = ask_gemini(cpp_code, api_key)
                else:
                    print("Неизвестный провайдер")
                    return
                
                # [Предположение] Пауза для обхода блокировок по rate limit бесплатных тарифов
                time.sleep(5) 
                
                rel_path = os.path.relpath(root, src_dir)
                target_dir = os.path.join(dest_dir, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                target_file = os.path.join(target_dir, file.split('.')[0] + ".hs")
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(haskell_code)

if __name__ == "__main__":
    # Пример вызова. Вставьте реальные пути и ключ.
    process_with_api("./OpenPapyrus", "./Surypus2", provider="gemini", api_key="REDACTED_GOOGLE_API_KEY")
    pass