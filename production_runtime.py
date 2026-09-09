from functools import lru_cache
from pathlib import Path

from qdrant_client import QdrantClient

from app.agents.critic_agent import CriticAgent
from app.agents.reasoning.legal_reasoning_agent import LegalReasoningAgent
from app.embeddings.embedder import BGEEmbedder
from app.retrieval.hybrid_retriever import HybridRetriever
from app.workflow.reasoning_critic_loop import ReasoningCriticLoop
from app.workflow.phase3_workflow import Phase3Workflow
from app.workflow.phase4_pakistan_runtime import PakistanPhase4Runtime


ROOT = Path("/content/drive/MyDrive/legalmind")
PROCESSED = ROOT / "data/phase4_pakistan/processed"
QDRANT_PATH = ROOT / "data/qdrant_storage"

CORPUS = {
    "name": "contract_act_1872",
    "title": "Contract Act, 1872",
    "chunks": PROCESSED / "chunks/contract_act_1872_chunks.json",
    "embeddings": PROCESSED / "embeddings/contract_act_1872_embeddings.npy",
    "collection": "legalmind_pakistan_contract_act_1872",
}


class QueryEmbedder:
    def __init__(self):
        self.base = BGEEmbedder()

    def encode(self, texts, normalize_embeddings=True, **kwargs):
        import numpy as np

        single = isinstance(texts, str)

        if single:
            texts = [texts]

        embeddings = self.base.embed_texts(texts)

        if normalize_embeddings:
            norms = np.linalg.norm(
                embeddings,
                axis=1,
                keepdims=True,
            )
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms

        return embeddings[0] if single else embeddings


@lru_cache(maxsize=1)
def build_production_runtime():
    qdrant = QdrantClient(path=str(QDRANT_PATH))
    embedder = QueryEmbedder()

    retriever = HybridRetriever(
        chunks_path=CORPUS["chunks"],
        embeddings_path=CORPUS["embeddings"],
        qdrant_client=qdrant,
        collection_name=CORPUS["collection"],
        embedding_model=embedder,
    )

    reasoning_agent = LegalReasoningAgent()
    critic_agent = CriticAgent()

    reasoning_critic = ReasoningCriticLoop(
        reasoning_agent=reasoning_agent,
        critic_agent=critic_agent,
        max_cycles=3,
    )

    workflow = Phase3Workflow(
        reasoning_critic_loop=reasoning_critic,
    )

    phase4 = PakistanPhase4Runtime(
        hybrid_retriever=retriever,
        corpus_name=CORPUS["name"],
        title=CORPUS["title"],
        workflow=workflow,
    )

    return phase4, workflow
