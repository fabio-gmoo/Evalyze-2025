import json
def validate_exam(json_text: str):
    try:
        data = json.loads(json_text)
    except Exception as e:
        return {'ok': False, 'error': f'JSON inválido: {e}'}
    qs = data.get('questions')
    if not isinstance(qs, list) or not qs:
        return {'ok': False, 'error': 'Debe tener questions como lista no vacía.'}
    for i, q in enumerate(qs, 1):
        if not q.get('q'): return {'ok': False, 'error': f\"'q' vacío en item {i}\"}
        opts = q.get('options', [])
        if not (isinstance(opts, list) and len(opts) >= 4):
            return {'ok': False, 'error': f\"'options' >= 4 en item {i}\"}
        ans = q.get('answer')
        if ans not in opts:
            return {'ok': False, 'error': f\"'answer' no está en 'options' en item {i}\"}
        if len(set(opts)) != len(opts):
            return {'ok': False, 'error': f\"'options' contiene duplicados en item {i}\"}
    return {'ok': True, 'count': len(qs)}
