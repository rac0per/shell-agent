import hashlib
import importlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


class VectorRetriever:
    """Simple Chroma-based retriever for local RAG knowledge base."""

    def __init__(
        self,
        persist_dir: str = "data/chroma_db",
        collection_name: str = "shell_kb",
        embedding_model: str = "BAAI/bge-small-zh-v1.5",
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        distance_threshold: float = 1.2,
        max_chunks_per_source: int = 2,
    ):
        try:
            chromadb = importlib.import_module("chromadb")
            sentence_transformers = importlib.import_module("sentence_transformers")
            sentence_transformer_cls = sentence_transformers.SentenceTransformer
        except Exception as exc:
            raise RuntimeError(
                "RAG dependencies missing. Install: chromadb sentence-transformers"
            ) from exc

        self._chromadb = chromadb
        self._embed_model = sentence_transformer_cls(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.distance_threshold = distance_threshold
        self.max_chunks_per_source = max_chunks_per_source

        self.client = self._chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def _embed(self, texts: Sequence[str]) -> List[List[float]]:
        vectors = self._embed_model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def _chunk_text(self, text: str) -> List[str]:
        """Markdown-aware chunking: split on headings/paragraphs first, then by size."""
        clean_text = text.strip()
        if not clean_text:
            return []

        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        # Split on Markdown headings (## / ###) or double newlines (paragraphs)
        import re
        raw_sections = re.split(r'(?=\n#{1,3} )|\n{2,}', clean_text)
        sections = [s.strip() for s in raw_sections if s.strip()]

        chunks: List[str] = []
        buffer = ""
        for section in sections:
            candidate = f"{buffer}\n\n{section}".strip() if buffer else section
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                # Section itself is too large — fall back to character splitting
                if len(section) > self.chunk_size:
                    step = max(1, self.chunk_size - self.chunk_overlap)
                    for start in range(0, len(section), step):
                        part = section[start : start + self.chunk_size].strip()
                        if part:
                            chunks.append(part)
                        if start + self.chunk_size >= len(section):
                            break
                    buffer = ""
                else:
                    buffer = section
        if buffer:
            chunks.append(buffer)
        return chunks

    def _expand_sources(self, paths: Iterable[str]) -> List[Path]:
        files: List[Path] = []
        for item in paths:
            p = Path(item)
            if not p.exists():
                continue
            if p.is_file():
                files.append(p)
                continue
            for ext in ("*.md", "*.txt", "*.py", "*.json", "*.yaml", "*.yml"):
                files.extend(p.rglob(ext))
        # Deduplicate while preserving order
        seen = set()
        unique_files: List[Path] = []
        for fp in files:
            key = str(fp.resolve())
            if key not in seen:
                seen.add(key)
                unique_files.append(fp)
        return unique_files

    def build_or_update_index_from_paths(self, paths: Iterable[str]) -> int:
        docs: List[str] = []
        ids: List[str] = []
        metadatas: List[dict] = []

        for fp in self._expand_sources(paths):
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            chunks = self._chunk_text(text)
            for i, chunk in enumerate(chunks):
                source = str(fp)
                digest = hashlib.md5(f"{source}:{i}:{chunk}".encode("utf-8")).hexdigest()
                ids.append(digest)
                docs.append(chunk)
                metadatas.append({"source": source, "chunk_index": i})

        if not docs:
            return 0

        embeddings = self._embed(docs)
        self.collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)
        return len(docs)

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        query_vec = self._embed([query])[0]
        # Fetch extra candidates to allow for filtering and deduplication
        fetch_k = max(top_k * 3, top_k + 8)
        result = self.collection.query(
            query_embeddings=[query_vec],
            n_results=fetch_k,
            include=["documents", "metadatas", "distances"],
        )

        docs_batch = result.get("documents", [[]])
        metas_batch = result.get("metadatas", [[]])
        dists_batch = result.get("distances", [[]])

        docs = docs_batch[0] if docs_batch else []
        metadatas = metas_batch[0] if metas_batch else []
        distances = dists_batch[0] if dists_batch else []

        rows: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}

        for i, content in enumerate(docs):
            metadata = metadatas[i] if i < len(metadatas) and isinstance(metadatas[i], dict) else {}
            distance = distances[i] if i < len(distances) else None

            # Quality filter: skip chunks that are too far from the query
            if isinstance(distance, (int, float)) and float(distance) > self.distance_threshold:
                continue

            source = str(metadata.get("source", ""))

            # Per-source deduplication: keep only the best N chunks per document
            count = source_counts.get(source, 0)
            if count >= self.max_chunks_per_source:
                continue
            source_counts[source] = count + 1

            score = None
            if isinstance(distance, (int, float)):
                score = 1.0 / (1.0 + float(distance))

            rows.append(
                {
                    "content": content,
                    "source": source,
                    "chunk_index": metadata.get("chunk_index"),
                    "distance": distance,
                    "score": score,
                }
            )

            if len(rows) >= top_k:
                break

        return rows
