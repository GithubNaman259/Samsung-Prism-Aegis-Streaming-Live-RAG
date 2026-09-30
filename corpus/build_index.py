"""One-shot indexer: corpus/docs/*.md -> corpus/index.json (chunks + embeddings).

Run from the repo root:  python -m corpus.build_index
Idempotent — safe to re-run after editing the corpus.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config  # noqa: E402
from backend.embeddings import embed, get_encoder  # noqa: E402
from backend.retrieval.corpus import build_chunks  # noqa: E402


def main() -> int:
    if not config.CORPUS_DIR.exists() or not any(config.CORPUS_DIR.glob("*.md")):
        from corpus.make_corpus import write_corpus  # noqa: PLC0415

        written = write_corpus(config.CORPUS_DIR)
        print(f"Corpus was empty — generated {len(written)} demo documents.")

    chunks = build_chunks(config.CORPUS_DIR)
    encoder = get_encoder()
    texts = [f"{c.section}. {c.text}" for c in chunks]
    matrix = embed(texts)

    payload = {
        "encoder": getattr(encoder, "name", "unknown"),
        "dim": int(matrix.shape[1]) if matrix.size else 0,
        "chunks": [c.model_dump() for c in chunks],
        "embeddings": [[round(float(x), 6) for x in row] for row in matrix],
    }
    config.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.INDEX_PATH.write_text(json.dumps(payload), encoding="utf-8")

    docs = len({c.doc_id for c in chunks})
    print(
        f"Indexed {len(chunks)} chunks from {docs} documents "
        f"using encoder '{payload['encoder']}' (dim={payload['dim']}).\n"
        f"Wrote {config.INDEX_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
