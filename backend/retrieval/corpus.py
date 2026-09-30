"""Corpus loading + chunking.

Corpus Isolation (PRD §4.3) is enforced structurally: this module is the *only*
source of retrievable text in the system, it reads from the local filesystem,
and it has no network client of any kind. Nothing downstream can cite a chunk
that did not come from here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .. import config
from ..schemas import Chunk

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
MIN_CHUNK_WORDS = 15


@dataclass
class LoadedDoc:
    doc_id: str
    title: str
    path: Path
    raw: str


def load_docs(corpus_dir: Path | None = None) -> list[LoadedDoc]:
    directory = Path(corpus_dir or config.CORPUS_DIR)
    if not directory.exists():
        raise FileNotFoundError(
            f"Corpus directory not found: {directory}. "
            "Run `python -m corpus.build_index` from the repo root."
        )
    docs: list[LoadedDoc] = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        first = raw.strip().splitlines()[0] if raw.strip() else path.stem
        title = _HEADING_RE.sub(r"\2", first).strip() or path.stem
        docs.append(LoadedDoc(doc_id=path.stem, title=title, path=path, raw=raw))
    if not docs:
        raise FileNotFoundError(f"No .md documents found in {directory}")
    return docs


def _split_sections(raw: str) -> Iterator[tuple[str, str]]:
    """Yield (section_label, body) pairs split on markdown headings."""
    current_label = "intro"
    buffer: list[str] = []
    section_no = 0
    for line in raw.splitlines():
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) >= 2:
            if any(s.strip() for s in buffer):
                yield current_label, "\n".join(buffer)
            section_no += 1
            current_label = f"§{section_no} {match.group(2).strip()}"
            buffer = []
        else:
            buffer.append(line)
    if any(s.strip() for s in buffer):
        yield current_label, "\n".join(buffer)


def _pack_paragraphs(body: str, target_words: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    packed: list[str] = []
    current: list[str] = []
    count = 0
    for para in paragraphs:
        words = len(para.split())
        if current and count + words > target_words:
            packed.append("\n\n".join(current))
            current, count = [], 0
        current.append(para)
        count += words
    if current:
        packed.append("\n\n".join(current))
    return packed


def chunk_docs(
    docs: list[LoadedDoc], target_words: int | None = None
) -> list[Chunk]:
    target = target_words or config.CHUNK_TARGET_WORDS
    chunks: list[Chunk] = []
    for doc in docs:
        idx = 0
        for section_label, body in _split_sections(doc.raw):
            for piece in _pack_paragraphs(body, target):
                cleaned = _HEADING_RE.sub(r"\2", piece).strip()
                # A bare title carries no retrievable fact but scores highly on
                # keyword overlap — drop it rather than let it displace evidence.
                if len(cleaned.split()) < MIN_CHUNK_WORDS:
                    continue
                piece = cleaned
                idx += 1
                section_num = section_label.split(" ")[0]
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.doc_id}#c{idx}",
                        doc_id=doc.doc_id,
                        section=section_label,
                        text=re.sub(r"\s+", " ", piece).strip(),
                        citation=f"{doc.doc_id} {section_num}",
                    )
                )
    return chunks


def build_chunks(corpus_dir: Path | None = None) -> list[Chunk]:
    return chunk_docs(load_docs(corpus_dir))
