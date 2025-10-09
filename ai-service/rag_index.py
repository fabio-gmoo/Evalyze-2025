from sentence_transformers import SentenceTransformer
from pathlib import Path
import numpy as np, json

def chunks(t, n=800): return [t[i:i+n] for i in range(0, len(t), n)]
def iter_docs(root='kb'):
    for p in Path(root).rglob('*.md'):
        txt = p.read_text(encoding='utf-8', errors='ignore')
        for i, c in enumerate(chunks(txt)):
            yield {'text': c, 'source': str(p), 'i': i}

print('Indexando KB...')
enc = SentenceTransformer('all-MiniLM-L6-v2')
docs = list(iter_docs('kb'))
embs = enc.encode([d['text'] for d in docs], normalize_embeddings=True)
np.savez('kb_index.npz', embs=embs)
json.dump(docs, open('kb_docs.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'Listo. Chunks: {len(docs)}')
