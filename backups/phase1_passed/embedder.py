
from sentence_transformers import SentenceTransformer
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

        self.model = SentenceTransformer(
            model_name
        )

    def embed_texts(
        self,
        texts,
        batch_size=8
    ):
        """
        Generate embeddings for a list of texts.

        Returns:
            numpy.ndarray of shape
            (number_of_texts, 1024)
        """

        if not texts:
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
        """
        Generate embeddings for hierarchical chunks.

        Each chunk must contain a 'text' field.

        Returns:
            numpy.ndarray
        """

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
    """
    Convenience function for embedding raw text.
    """

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
    """
    Convenience function for embedding
    hierarchical contract chunks.
    """

    embedder = BGEEmbedder(
        model_name=model_name
    )

    return embedder.embed_chunks(
        chunks,
        batch_size=batch_size
    )
