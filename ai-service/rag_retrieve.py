from sentence_transformers import SentenceTransformer
import numpy as np, json
class Retriever:
    def __init__(self, idx='kb_index.npz', meta='kb_docs.json'):
        self.docs = json.load(open(meta, encoding='utf-8'))
        self.embs = np.load(idx)['embs']
        self.enc = SentenceTransformer('all-MiniLM-L6-v2')
    def topk(self, query:str, k=6):
        qv = self.enc.encode([query], normalize_embeddings=True)[0]
        sims = self.embs @ qv
        return [self.docs[i] for i in sims.argsort()[::-1][:k]]
