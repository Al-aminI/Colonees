"""
Knowledge Base Manager

Stores and manages Knowledge Base definitions and their associated files.
Provides simple text-based search across uploaded documents (PDFs, CSVs,
text files, markdown) without external embedding dependencies.

Knowledge bases can be scoped to specific specialist types and workspaces,
allowing fine-grained control over which agents access which data.
"""

import json
import logging
import os
import re
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeBaseDefinition:
    """Blueprint for a knowledge base — metadata, file list, and access rules."""

    name: str                                      # unique slug
    display_name: str
    description: str
    type: str                                      # "files", "database", "api"
    file_paths: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    specialist_types: List[str] = field(default_factory=list)   # empty = all
    workspaces: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    stats: Dict[str, Any] = field(default_factory=lambda: {
        "total_files": 0,
        "total_chunks": 0,
        "total_size_bytes": 0,
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KnowledgeBaseDefinition":
        d = deepcopy(d)
        return cls(**d)


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> List[str]:
    """Split *text* into overlapping chunks of approximately *chunk_size* characters."""
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _read_file_text(file_path: str) -> Optional[str]:
    """
    Best-effort plain-text read of a file.

    Handles .txt, .md, .csv, .json as UTF-8 text.
    Attempts to read .pdf as text; silently returns None on failure.
    """
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in (".txt", ".md", ".csv", ".json", ".log", ".yaml", ".yml", ".xml", ".html"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        elif ext == ".pdf":
            # Best-effort: read raw bytes and attempt decode.
            # A proper PDF parser can be added later.
            try:
                with open(file_path, "rb") as fh:
                    raw = fh.read()
                return raw.decode("utf-8", errors="ignore")
            except Exception:
                logger.debug("Could not read PDF as text: %s", file_path)
                return None
        else:
            # Fallback: try reading as text
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
    except Exception as exc:
        logger.warning("Failed to read file %s: %s", file_path, exc)
        return None


def _score_chunk(chunk: str, terms: List[str]) -> float:
    """
    Score a chunk by term frequency.

    Returns the fraction of unique query terms found in the chunk
    (case-insensitive).
    """
    if not terms:
        return 0.0
    chunk_lower = chunk.lower()
    hits = sum(1 for t in terms if t in chunk_lower)
    return hits / len(terms)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class KnowledgeBaseManager:
    """
    In-memory registry of Knowledge Base definitions with JSON persistence
    and simple text-based search.

    Storage layout::

        <storage_dir>/
            knowledge_bases.json      # persisted KB definitions
            kb_files/
                <kb_name>/
                    file1.txt
                    file2.csv
    """

    def __init__(self, storage_dir: str):
        self._knowledge_bases: Dict[str, KnowledgeBaseDefinition] = {}
        self._storage_dir = storage_dir
        self._storage_path = os.path.join(storage_dir, "knowledge_bases.json")
        self._files_dir = os.path.join(storage_dir, "kb_files")
        os.makedirs(self._files_dir, exist_ok=True)
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for raw in data:
                defn = KnowledgeBaseDefinition.from_dict(raw)
                self._knowledge_bases[defn.name] = defn
            logger.info("Loaded %d knowledge bases from %s", len(self._knowledge_bases), self._storage_path)
        except Exception as exc:
            logger.warning("Failed to load knowledge bases: %s", exc)

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = [kb.to_dict() for kb in self._knowledge_bases.values()]
            with open(self._storage_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:
            logger.warning("Failed to save knowledge bases: %s", exc)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, defn: KnowledgeBaseDefinition) -> KnowledgeBaseDefinition:
        if defn.name in self._knowledge_bases:
            raise ValueError(f"Knowledge base '{defn.name}' already exists.")
        defn.created_at = datetime.utcnow().isoformat()
        defn.updated_at = defn.created_at
        self._knowledge_bases[defn.name] = defn
        # Ensure file directory exists
        os.makedirs(os.path.join(self._files_dir, defn.name), exist_ok=True)
        self._save()
        logger.info("Knowledge base created: '%s'", defn.name)
        return defn

    def get(self, name: str) -> Optional[KnowledgeBaseDefinition]:
        return self._knowledge_bases.get(name)

    def list(self, enabled_only: bool = False) -> List[KnowledgeBaseDefinition]:
        result = list(self._knowledge_bases.values())
        if enabled_only:
            result = [kb for kb in result if kb.enabled]
        return result

    def update(self, name: str, updates: Dict[str, Any]) -> KnowledgeBaseDefinition:
        defn = self._knowledge_bases.get(name)
        if not defn:
            raise KeyError(f"Knowledge base '{name}' not found.")
        # Protect immutable fields
        for protected in ("name", "created_at"):
            updates.pop(protected, None)
        updates["updated_at"] = datetime.utcnow().isoformat()
        for k, v in updates.items():
            if hasattr(defn, k):
                setattr(defn, k, v)
        self._save()
        logger.info("Knowledge base updated: '%s'", name)
        return defn

    def delete(self, name: str) -> bool:
        defn = self._knowledge_bases.get(name)
        if not defn:
            raise KeyError(f"Knowledge base '{name}' not found.")
        del self._knowledge_bases[name]
        # Remove files on disk
        kb_dir = os.path.join(self._files_dir, name)
        if os.path.isdir(kb_dir):
            import shutil
            shutil.rmtree(kb_dir, ignore_errors=True)
        self._save()
        logger.info("Knowledge base deleted: '%s'", name)
        return True

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def upload_file(self, kb_name: str, filename: str, content_bytes: bytes) -> str:
        """
        Save an uploaded file into the KB's directory.

        Returns the absolute file path of the saved file.
        Updates ``file_paths`` and ``stats`` on the KB definition.
        """
        defn = self._knowledge_bases.get(kb_name)
        if not defn:
            raise KeyError(f"Knowledge base '{kb_name}' not found.")

        kb_dir = os.path.join(self._files_dir, kb_name)
        os.makedirs(kb_dir, exist_ok=True)

        file_path = os.path.join(kb_dir, filename)
        with open(file_path, "wb") as fh:
            fh.write(content_bytes)

        # Update definition
        if file_path not in defn.file_paths:
            defn.file_paths.append(file_path)
        self._refresh_stats(defn)
        defn.updated_at = datetime.utcnow().isoformat()
        self._save()

        logger.info("File uploaded to KB '%s': %s (%d bytes)", kb_name, filename, len(content_bytes))
        return file_path

    def delete_file(self, kb_name: str, filename: str) -> bool:
        """Remove a single file from a KB."""
        defn = self._knowledge_bases.get(kb_name)
        if not defn:
            raise KeyError(f"Knowledge base '{kb_name}' not found.")

        file_path = os.path.join(self._files_dir, kb_name, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{filename}' not found in knowledge base '{kb_name}'.")

        os.remove(file_path)
        defn.file_paths = [p for p in defn.file_paths if p != file_path]
        self._refresh_stats(defn)
        defn.updated_at = datetime.utcnow().isoformat()
        self._save()

        logger.info("File deleted from KB '%s': %s", kb_name, filename)
        return True

    def list_files(self, kb_name: str) -> List[Dict[str, Any]]:
        """List all files in a knowledge base with metadata."""
        defn = self._knowledge_bases.get(kb_name)
        if not defn:
            raise KeyError(f"Knowledge base '{kb_name}' not found.")

        kb_dir = os.path.join(self._files_dir, kb_name)
        if not os.path.isdir(kb_dir):
            return []

        files = []
        for fname in sorted(os.listdir(kb_dir)):
            fpath = os.path.join(kb_dir, fname)
            if not os.path.isfile(fpath):
                continue
            stat = os.stat(fpath)
            files.append({
                "filename": fname,
                "path": fpath,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return files

    def _refresh_stats(self, defn: KnowledgeBaseDefinition) -> None:
        """Recompute stats for a KB by scanning its file directory."""
        kb_dir = os.path.join(self._files_dir, defn.name)
        total_files = 0
        total_size = 0
        total_chunks = 0

        if os.path.isdir(kb_dir):
            for fname in os.listdir(kb_dir):
                fpath = os.path.join(kb_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                total_files += 1
                total_size += os.path.getsize(fpath)
                # Estimate chunks
                text = _read_file_text(fpath)
                if text:
                    total_chunks += len(_chunk_text(text))

        defn.stats = {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, kb_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Simple text search across all files in a knowledge base.

        Splits each file into ~500-char chunks with 50-char overlap.
        Scores by fraction of query terms found in each chunk.
        Returns the top-k results sorted by score descending.
        """
        defn = self._knowledge_bases.get(kb_name)
        if not defn:
            raise KeyError(f"Knowledge base '{kb_name}' not found.")

        terms = [t.lower() for t in re.split(r"\s+", query.strip()) if t]
        if not terms:
            return []

        results: List[Dict[str, Any]] = []
        kb_dir = os.path.join(self._files_dir, kb_name)

        if not os.path.isdir(kb_dir):
            return []

        for fname in os.listdir(kb_dir):
            fpath = os.path.join(kb_dir, fname)
            if not os.path.isfile(fpath):
                continue
            text = _read_file_text(fpath)
            if not text:
                continue
            chunks = _chunk_text(text)
            for chunk in chunks:
                score = _score_chunk(chunk, terms)
                if score > 0:
                    results.append({
                        "content": chunk,
                        "source": fname,
                        "score": round(score, 4),
                    })

        # Sort by score descending, then truncate
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def search_all(
        self,
        query: str,
        kb_names: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search across multiple knowledge bases.

        If *kb_names* is None or empty, searches all enabled KBs.
        """
        if not kb_names:
            kb_names = [kb.name for kb in self._knowledge_bases.values() if kb.enabled]

        all_results: List[Dict[str, Any]] = []
        for name in kb_names:
            if name not in self._knowledge_bases:
                continue
            hits = self.search(name, query, top_k=top_k)
            for hit in hits:
                hit["knowledge_base"] = name
            all_results.extend(hits)

        all_results.sort(key=lambda r: r["score"], reverse=True)
        return all_results[:top_k]

    def get_stats(self, kb_name: str) -> Dict[str, Any]:
        """Return stats dict for a knowledge base."""
        defn = self._knowledge_bases.get(kb_name)
        if not defn:
            raise KeyError(f"Knowledge base '{kb_name}' not found.")
        self._refresh_stats(defn)
        self._save()
        return defn.stats
