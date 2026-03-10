import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.vector_retriever import VectorRetriever


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/update local RAG vector index")
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Source file/folder path. Repeat --source for multiple paths.",
    )
    parser.add_argument("--db", default="data/chroma_db", help="Vector DB directory")
    parser.add_argument("--collection", default="shell_kb", help="Collection name")
    parser.add_argument(
        "--model",
        default="BAAI/bge-small-zh-v1.5",
        help="SentenceTransformer model name",
    )

    args = parser.parse_args()

    retriever = VectorRetriever(
        persist_dir=args.db,
        collection_name=args.collection,
        embedding_model=args.model,
    )

    count = retriever.build_or_update_index_from_paths(args.source)
    print(f"Indexed chunks: {count}")

    # Help user set runtime env vars for CLI usage.
    root = Path(__file__).resolve().parent.parent
    abs_sources = [str((root / s).resolve()) if not Path(s).is_absolute() else s for s in args.source]
    joined = ";".join(abs_sources)
    print("Set env vars before running CLI:")
    print("  $env:SHELL_AGENT_ENABLE_RAG='true'")
    print(f"  $env:SHELL_AGENT_RAG_DOCS='{joined}'")
    print(f"  $env:SHELL_AGENT_RAG_DB='{Path(args.db).resolve()}'")
    print(f"  $env:SHELL_AGENT_RAG_COLLECTION='{args.collection}'")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
