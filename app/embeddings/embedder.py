try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

import numpy as np


class BGEEmbedder:
    """
    BGE-M3 embedding wrapper for LegalMind.

    Converts contract chunks into dense 1024-dimensional
    vector representations for semantic retrieval.
    """

    def __init__(
        self,
        model_name="BAAI/bge-m3"
    ):
        self.model_name = model_name

        if SentenceTransformer is None:
            self.model = None
        else:
            self.model = SentenceTransformer(
                model_name
            )

    def embed_texts(
        self,
        texts,
        batch_size=8
    ):
        if not texts or self.model is None:
            return np.empty(
                (0, 1024),
                dtype=np.float32
            )

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings.astype(
            np.float32
        )

    def embed_chunks(
        self,
        chunks,
        batch_size=8
    ):
        texts = [
            chunk.get("text", "")
            for chunk in chunks
        ]

        return self.embed_texts(
            texts,
            batch_size=batch_size
        )


def embed_texts(
    texts,
    model_name="BAAI/bge-m3",
    batch_size=8
):
    embedder = BGEEmbedder(
        model_name=model_name
    )

    return embedder.embed_texts(
        texts,
        batch_size=batch_size
    )


def embed_chunks(
    chunks,
    model_name="BAAI/bge-m3",
    batch_size=8
):
    embedder = BGEEmbedder(
        model_name=model_name
    )

    return embedder.embed_chunks(
        chunks,
        batch_size=batch_size
    )
