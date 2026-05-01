import hashlib
import importlib
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


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
        hybrid_enabled: bool = True,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.2,
        keyword_scan_limit: int = 2000,
        keyword_min_token_length: int = 2,
        keyword_only_threshold: float = 0.5,
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
        self.hybrid_enabled = hybrid_enabled
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.keyword_scan_limit = keyword_scan_limit
        self.keyword_min_token_length = keyword_min_token_length
        self.keyword_only_threshold = keyword_only_threshold

        self.client = self._chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    # ------------------------------------------------------------------
    # Category detection
    # ------------------------------------------------------------------
    _CATEGORY_MAP: Dict[str, str] = {
        "commands": "commands",
        "safety": "safety",
        "tasks": "tasks",
        "patterns": "patterns",
        "examples": "examples",
    }

    @classmethod
    def _detect_category(cls, fp: Path) -> str:
        """Return a category string based on the file's parent directory name."""
        for part in fp.parts:
            cat = cls._CATEGORY_MAP.get(part.lower())
            if cat:
                return cat
        return "general"

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

    @staticmethod
    def _source_variants(source_path: str) -> List[str]:
        """Return canonical path variants to clean up mixed separator history."""
        norm = source_path.strip()
        if not norm:
            return []
        variants = {norm, norm.replace("\\", "/"), norm.replace("/", "\\")}
        return [v for v in variants if v]

    def _tokenize_query(self, query: str) -> List[str]:
        text = query.strip().lower()
        if not text:
            return []

        raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_./:-]+", text)
        tokens: List[str] = []
        seen = set()

        for tok in raw_tokens:
            if re.search(r"[\u4e00-\u9fff]", tok):
                # Use the full Chinese phrase as-is.  Generating bigrams from long
                # phrases creates common structural tokens (文档/标准/操作/步骤) that
                # match template headings in every enriched doc, polluting keyword scores.
                candidates = [tok]
                # Only split very short (2-3 char) Chinese tokens into characters when
                # the token itself is already 2 chars (e.g. "权限" → keep as-is, fine).
            else:
                if len(tok) < self.keyword_min_token_length:
                    continue
                candidates = [tok]

            for candidate in candidates:
                if candidate and candidate not in seen:
                    seen.add(candidate)
                    tokens.append(candidate)

        return tokens

    def _build_vector_candidates(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        query_vec = self._embed([query])[0]
        fetch_k = max(top_k * 3, top_k + 8)
        query_kwargs: Dict[str, Any] = dict(
            query_embeddings=[query_vec],
            n_results=fetch_k,
            include=["documents", "metadatas", "distances"],
        )
        if category_filter:
            query_kwargs["where"] = {"category": category_filter}

        result = self.collection.query(**query_kwargs)

        docs_batch = result.get("documents", [[]])
        metas_batch = result.get("metadatas", [[]])
        dists_batch = result.get("distances", [[]])
        ids_batch = result.get("ids", [[]])

        docs = docs_batch[0] if docs_batch else []
        metadatas = metas_batch[0] if metas_batch else []
        distances = dists_batch[0] if dists_batch else []
        ids = ids_batch[0] if ids_batch else []

        rows: List[Dict[str, Any]] = []
        for i, content in enumerate(docs):
            metadata = metadatas[i] if i < len(metadatas) and isinstance(metadatas[i], dict) else {}
            distance = distances[i] if i < len(distances) else None
            vec_score = 0.0
            if isinstance(distance, (int, float)):
                vec_score = 1.0 / (1.0 + float(distance))

            row_id = ids[i] if i < len(ids) else f"vec::{i}::{metadata.get('source', '')}::{metadata.get('chunk_index')}"
            rows.append(
                {
                    "id": str(row_id),
                    "content": str(content),
                    "source": str(metadata.get("source", "")),
                    "category": metadata.get("category", "general"),
                    "chunk_index": metadata.get("chunk_index"),
                    "distance": distance,
                    "vector_score": vec_score,
                    "keyword_score": 0.0,
                }
            )

        return rows

    def _keyword_match_score(self, query: str, tokens: List[str], source: str, content: str) -> float:
        if not tokens:
            return 0.0

        full_text = f"{source.lower()}\n{content.lower()}"
        hit_count = sum(1 for token in tokens if token in full_text)
        overlap = hit_count / len(tokens)
        phrase_bonus = 0.25 if query.lower() in full_text else 0.0
        return min(1.0, overlap + phrase_bonus)

    def _build_keyword_candidates(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.hybrid_enabled:
            return []

        tokens = self._tokenize_query(query)
        if not tokens:
            return []

        total = self.collection.count()
        if not isinstance(total, int) or total <= 0:
            return []

        get_kwargs: Dict[str, Any] = {
            "include": ["documents", "metadatas"],
            "limit": min(total, self.keyword_scan_limit),
        }
        if category_filter:
            get_kwargs["where"] = {"category": category_filter}

        result = self.collection.get(**get_kwargs)
        if not isinstance(result, dict):
            return []

        docs = result.get("documents")
        metadatas = result.get("metadatas")
        ids = result.get("ids")
        if not isinstance(docs, list) or not isinstance(metadatas, list):
            return []

        rows: List[Dict[str, Any]] = []
        for i, content in enumerate(docs):
            metadata = metadatas[i] if i < len(metadatas) and isinstance(metadatas[i], dict) else {}
            source = str(metadata.get("source", ""))
            content_text = str(content)
            kw_score = self._keyword_match_score(query, tokens, source, content_text)
            if kw_score <= 0.0:
                continue

            row_id = ids[i] if isinstance(ids, list) and i < len(ids) else f"kw::{i}::{source}::{metadata.get('chunk_index')}"
            rows.append(
                {
                    "id": str(row_id),
                    "content": content_text,
                    "source": source,
                    "category": metadata.get("category", "general"),
                    "chunk_index": metadata.get("chunk_index"),
                    "distance": None,
                    "vector_score": 0.0,
                    "keyword_score": kw_score,
                }
            )

        rows.sort(key=lambda row: row.get("keyword_score", 0.0), reverse=True)
        return rows[: max(top_k * 3, top_k + 8)]

    def _merge_and_rerank(
        self,
        vector_rows: List[Dict[str, Any]],
        keyword_rows: List[Dict[str, Any]],
        query: str,
        category_filter: Optional[str],
    ) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}

        for row in vector_rows:
            merged[row["id"]] = dict(row)

        for row in keyword_rows:
            existing = merged.get(row["id"])
            if existing is None:
                # Only admit keyword-only candidates that pass the confidence threshold.
                # This prevents enriched-doc noise from displacing good vector matches.
                if float(row.get("keyword_score", 0.0)) >= self.keyword_only_threshold:
                    merged[row["id"]] = dict(row)
                continue

            existing["keyword_score"] = max(
                float(existing.get("keyword_score", 0.0)),
                float(row.get("keyword_score", 0.0)),
            )

        rows = list(merged.values())
        query_tokens = self._tokenize_query(query)

        for row in rows:
            vector_score = float(row.get("vector_score", 0.0))
            keyword_score = float(row.get("keyword_score", 0.0))

            if vector_score > 0.0:
                # Keyword acts as a multiplicative boost so it can never drag a
                # well-ranked vector result below a keyword-only candidate.
                score = vector_score * (1.0 + self.keyword_weight * keyword_score)
            else:
                # Keyword-only candidates: heavily discounted so they only rescue
                # queries that had zero usable vector matches.
                score = self.keyword_weight * keyword_score * 0.4

            if category_filter and str(row.get("category", "")) == category_filter:
                score += 0.05

            source = str(row.get("source", "")).lower()
            if source:
                base = Path(source).name.lower()
                if base and any(tok and tok in base for tok in query_tokens):
                    score += 0.03

            if row.get("chunk_index") == 0:
                score += 0.01

            row["score"] = score

        rows.sort(
            key=lambda row: (
                float(row.get("score", 0.0)),
                -float(row.get("distance")) if isinstance(row.get("distance"), (int, float)) else 0.0,
            ),
            reverse=True,
        )
        return rows

    def build_or_update_index_from_paths(self, paths: Iterable[str]) -> int:
        files = self._expand_sources(paths)

        # Clean existing chunks for each source first to avoid stale/duplicate records
        # when chunking strategy changes or historical metadata is incomplete.
        for fp in files:
            source = str(fp)
            for variant in self._source_variants(source):
                self.delete_by_source(variant)

        docs: List[str] = []
        ids: List[str] = []
        metadatas: List[dict] = []

        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            chunks = self._chunk_text(text)
            category = self._detect_category(fp)
            for i, chunk in enumerate(chunks):
                source = str(fp)
                digest = hashlib.md5(f"{source}:{i}:{chunk}".encode("utf-8")).hexdigest()
                ids.append(digest)
                docs.append(chunk)
                metadatas.append({"source": source, "chunk_index": i, "category": category})

        if not docs:
            return 0

        embeddings = self._embed(docs)
        self.collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)
        return len(docs)

    def clear_collection(self) -> int:
        """Delete all chunks from the collection and return removed count."""
        total = self.collection.count()
        if not isinstance(total, int) or total <= 0:
            return 0

        deleted = 0
        offset = 0
        batch = 1000
        while offset < total:
            result = self.collection.get(limit=batch, offset=offset, include=[])
            ids = result.get("ids") or []
            if not ids:
                break
            self.collection.delete(ids=ids)
            deleted += len(ids)
            offset += batch

        return deleted

    def list_sources(self) -> Dict[str, int]:
        """Return {source_path: chunk_count} for every indexed document."""
        total = self.collection.count()
        if total == 0:
            return {}
        result = self.collection.get(include=["metadatas"], limit=total)
        counts: Dict[str, int] = {}
        for meta in (result.get("metadatas") or []):
            if isinstance(meta, dict):
                src = str(meta.get("source", "unknown"))
                counts[src] = counts.get(src, 0) + 1
        return counts

    def list_categories(self) -> Dict[str, int]:
        """Return {category: chunk_count} across the collection."""
        total = self.collection.count()
        if total == 0:
            return {}
        result = self.collection.get(include=["metadatas"], limit=total)
        counts: Dict[str, int] = {}
        for meta in (result.get("metadatas") or []):
            if isinstance(meta, dict):
                cat = str(meta.get("category", "general"))
                counts[cat] = counts.get(cat, 0) + 1
        return counts

    def delete_by_source(self, source_path: str) -> int:
        """Delete all chunks whose source matches source_path. Returns deleted count."""
        result = self.collection.get(
            where={"source": source_path},
            include=["metadatas"],
        )
        ids_to_delete = result.get("ids") or []
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    def retrieve(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        vector_rows = self._build_vector_candidates(query, top_k=top_k, category_filter=category_filter)
        keyword_rows = self._build_keyword_candidates(query, top_k=top_k, category_filter=category_filter)
        ranked_rows = self._merge_and_rerank(
            vector_rows,
            keyword_rows,
            query=query,
            category_filter=category_filter,
        )

        rows: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}

        for row in ranked_rows:
            distance = row.get("distance")
            keyword_score = float(row.get("keyword_score", 0.0))

            # Quality filter: skip chunks that are too far from the query
            if (
                isinstance(distance, (int, float))
                and float(distance) > self.distance_threshold
                and keyword_score <= 0.0
            ):
                continue

            source = str(row.get("source", ""))

            # Per-source deduplication: keep only the best N chunks per document
            count = source_counts.get(source, 0)
            if count >= self.max_chunks_per_source:
                continue
            source_counts[source] = count + 1

            rows.append(
                {
                    "content": row.get("content", ""),
                    "source": source,
                    "category": row.get("category", "general"),
                    "chunk_index": row.get("chunk_index"),
                    "distance": distance,
                    "score": row.get("score"),
                }
            )

            if len(rows) >= top_k:
                break

        return rows
