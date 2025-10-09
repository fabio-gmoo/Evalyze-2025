import os, requests
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434/api/generate')
def chat_once(prompt: str, model: str = 'examiner') -> str:
    payload = {'model': model, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.2}}
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    if 'response' not in data:
        raise RuntimeError(f'Respuesta inesperada de Ollama: {data}')
    return data['response']
