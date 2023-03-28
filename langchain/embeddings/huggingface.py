"""Wrapper around HuggingFace embedding models."""
from typing import Any, List

from pydantic import BaseModel, Extra

from langchain.embeddings.base import Embeddings

DEFAULT_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
DEFAULT_INSTRUCT_MODEL = "hkunlp/instructor-large"
DEFAULT_EMBED_INSTRUCTION = "Represent the document for retrieval: "
DEFAULT_QUERY_INSTRUCTION = (
    "Represent the question for retrieving supporting documents: "
)


class HuggingFaceEmbeddings(BaseModel, Embeddings):
    """Wrapper around sentence_transformers embedding models.

    To use, you should have the ``sentence_transformers`` python package installed.

    Example:
        .. code-block:: python

            from langchain.embeddings import HuggingFaceEmbeddings
            model_name = "sentence-transformers/all-mpnet-base-v2"
            hf = HuggingFaceEmbeddings(model_name=model_name)
    """

    client: Any  #: :meta private:
    model_name: str = DEFAULT_MODEL_NAME
    """Model name to use."""

    def __init__(self, **kwargs: Any):
        """Initialize the sentence_transformer."""
        super().__init__(**kwargs)
        try:
            import sentence_transformers
            try:
                self.client = sentence_transformers.SentenceTransformer(self.model_name)
            except:
                try:
                    # [Hugging Face Models can be converted into sentence_transformer models by adding a pooling layer](https://www.sbert.net/docs/training/overview.html#creating-networks-from-scratch)
                    word_embedding_model = sentence_transformers.models.Transformer(self.model_name)
                    pooling_model = sentence_transformers.models.Pooling(word_embedding_model.get_word_embedding_dimension())
                    self.client = sentence_transformers.SentenceTransformer(modules=[word_embedding_model, pooling_model])
                except ImportError:
                    raise ValueError(
                        "Model is not compatible sentence_transformers architecture. "
                        "Please use a sentence_transformers model."
                    )
        except ImportError:
            raise ValueError(
                "Could not import sentence_transformers python package. "
                "Please install it with `pip install sentence_transformers`."
            )

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        embeddings = self.client.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        text = text.replace("\n", " ")
        embedding = self.client.encode(text)
        return embedding.tolist()


class HuggingFaceInstructEmbeddings(BaseModel, Embeddings):
    """Wrapper around sentence_transformers embedding models.

    To use, you should have the ``sentence_transformers``
    and ``InstructorEmbedding`` python package installed.

    Example:
        .. code-block:: python

            from langchain.embeddings import HuggingFaceInstructEmbeddings
            model_name = "hkunlp/instructor-large"
            hf = HuggingFaceInstructEmbeddings(model_name=model_name)
    """

    client: Any  #: :meta private:
    model_name: str = DEFAULT_INSTRUCT_MODEL
    """Model name to use."""
    embed_instruction: str = DEFAULT_EMBED_INSTRUCTION
    """Instruction to use for embedding documents."""
    query_instruction: str = DEFAULT_QUERY_INSTRUCTION
    """Instruction to use for embedding query."""

    def __init__(self, **kwargs: Any):
        """Initialize the sentence_transformer."""
        super().__init__(**kwargs)
        try:
            from InstructorEmbedding import INSTRUCTOR

            self.client = INSTRUCTOR(self.model_name)
        except ImportError as e:
            raise ValueError("Dependencies for InstructorEmbedding not found.") from e

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace instruct model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        instruction_pairs = [[self.embed_instruction, text] for text in texts]
        embeddings = self.client.encode(instruction_pairs)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace instruct model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        instruction_pair = [self.query_instruction, text]
        embedding = self.client.encode([instruction_pair])[0]
        return embedding.tolist()
