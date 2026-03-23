"""
File Tool Provider

Handles file operations using the local filesystem.
"""

import logging
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from strands import tool

from colon.agents.tool_providers import ToolProvider

logger = logging.getLogger(__name__)


class FileToolProvider(ToolProvider):
    """
    Tool provider for local filesystem operations.

    Exposes @tool-decorated methods that specialists pass directly into
    Agent(tools=[...]). Holds shared state: base_dir.
    """

    def __init__(
        self,
        *args,
        base_dir: Optional[str] = None,
        **kwargs,
    ):
        self.base_dir = Path(base_dir or os.getenv("COLONEES_FILES_DIR", "colonees_files")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(*args, **kwargs)
        logger.info("FileToolProvider ready — base_dir: %s", self.base_dir)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: str) -> Path:
        """Resolve a logical path to an absolute path under base_dir."""
        resolved = (self.base_dir / path.lstrip("/")).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal attempt blocked: {path}")
        return resolved

    def _logical(self, abs_path: Path) -> str:
        return str(abs_path.relative_to(self.base_dir))

    def _public_url(self, path: str) -> str:
        return self._resolve(path).as_uri()

    def get_capabilities(self) -> List[str]:
        return [
            "file_read", "file_write", "file_append", "file_delete",
            "file_copy", "file_move", "file_list", "file_exists",
            "file_metadata", "full_text_search", "find_and_replace",
            "line_range_read", "folder_create", "folder_delete", "public_url",
        ]

    # ------------------------------------------------------------------
    # Read / Write
    # ------------------------------------------------------------------

    @tool
    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read the full content of a file.

        Args:
            path:     Logical file path e.g. 'scripts/draft.txt'.
            encoding: Text encoding (default utf-8). Use 'bytes' to get raw base64.
        """
        try:
            abs_path = self._resolve(path)
            if not abs_path.exists():
                return {"status": "failed", "error": f"File not found: {path}", "path": path}
            raw = abs_path.read_bytes()
            content = (
                raw.decode(encoding)
                if encoding != "bytes"
                else __import__("base64").b64encode(raw).decode()
            )
            stat = abs_path.stat()
            return {
                "status": "success",
                "path": path,
                "content": content,
                "size_bytes": stat.st_size,
                "content_type": mimetypes.guess_type(path)[0] or "text/plain",
            }
        except Exception as e:
            logger.error("read_file failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    @tool
    def write_file(
        self,
        path: str,
        content: str,
        content_type: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        Create or overwrite a file.

        Args:
            path:         Logical file path.
            content:      Text content to write.
            content_type: MIME type (informational only; auto-detected if omitted).
            encoding:     Text encoding to use when writing.
        """
        try:
            abs_path = self._resolve(path)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            body = content.encode(encoding)
            abs_path.write_bytes(body)
            detected_type = content_type or mimetypes.guess_type(path)[0] or "text/plain"
            return {
                "status": "success",
                "path": path,
                "public_url": abs_path.as_uri(),
                "size_bytes": len(body),
                "content_type": detected_type,
            }
        except Exception as e:
            logger.error("write_file failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    @tool
    def append_to_file(self, path: str, content: str, separator: str = "\n") -> Dict[str, Any]:
        """
        Append text to an existing file. Creates the file if it does not exist.

        Args:
            path:      Logical file path.
            content:   Text to append.
            separator: String inserted between existing content and new content.
        """
        try:
            abs_path = self._resolve(path)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            existing = abs_path.read_text(encoding="utf-8") if abs_path.exists() else ""
            combined = (existing + separator + content) if existing else content
            abs_path.write_text(combined, encoding="utf-8")
            return {"status": "success", "path": path, "total_size_bytes": len(combined.encode())}
        except Exception as e:
            logger.error("append_to_file failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    # ------------------------------------------------------------------
    # Delete / Copy / Move
    # ------------------------------------------------------------------

    @tool
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Permanently delete a file.

        Args:
            path: Logical file path to delete.
        """
        try:
            abs_path = self._resolve(path)
            if abs_path.exists():
                abs_path.unlink()
            return {"status": "success", "path": path, "deleted": True}
        except Exception as e:
            logger.error("delete_file failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    @tool
    def copy_file(self, source_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Copy a file to a new path.

        Args:
            source_path:      Logical path of the file to copy.
            destination_path: Logical path for the copy.
        """
        try:
            src = self._resolve(source_path)
            dst = self._resolve(destination_path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return {
                "status": "success",
                "source_path": source_path,
                "destination_path": destination_path,
                "public_url": dst.as_uri(),
            }
        except Exception as e:
            logger.error("copy_file failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def move_file(self, source_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Move (rename) a file.

        Args:
            source_path:      Current logical path.
            destination_path: New logical path.
        """
        try:
            src = self._resolve(source_path)
            dst = self._resolve(destination_path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return {
                "status": "success",
                "source_path": source_path,
                "destination_path": destination_path,
                "public_url": dst.as_uri(),
            }
        except Exception as e:
            logger.error("move_file failed: %s", e)
            return {"status": "failed", "error": str(e)}

    # ------------------------------------------------------------------
    # Listing / Existence / Metadata
    # ------------------------------------------------------------------

    @tool
    def list_files(
        self,
        prefix: str = "",
        extension_filter: Optional[str] = None,
        max_results: int = 200,
    ) -> Dict[str, Any]:
        """
        List files, optionally filtered by path prefix or extension.

        Args:
            prefix:           Logical path prefix to search under.
            extension_filter: Only return files with this extension e.g. '.txt', '.mp4'.
            max_results:      Maximum number of results to return.
        """
        try:
            search_root = self._resolve(prefix) if prefix else self.base_dir
            files = []
            for abs_path in sorted(search_root.rglob("*")):
                if not abs_path.is_file():
                    continue
                logical = self._logical(abs_path)
                if extension_filter and not logical.endswith(extension_filter):
                    continue
                stat = abs_path.stat()
                files.append({
                    "path": logical,
                    "public_url": abs_path.as_uri(),
                    "size_bytes": stat.st_size,
                })
                if len(files) >= max_results:
                    break
            return {"status": "success", "files": files, "count": len(files)}
        except Exception as e:
            logger.error("list_files failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def file_exists(self, path: str) -> Dict[str, Any]:
        """
        Check whether a file exists.

        Args:
            path: Logical file path to check.
        """
        try:
            exists = self._resolve(path).exists()
            return {"status": "success", "path": path, "exists": exists}
        except Exception as e:
            return {"status": "failed", "error": str(e), "path": path}

    @tool
    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """
        Retrieve metadata for a file: size, content-type, last-modified.

        Args:
            path: Logical file path.
        """
        try:
            abs_path = self._resolve(path)
            if not abs_path.exists():
                return {"status": "failed", "error": f"File not found: {path}", "path": path}
            stat = abs_path.stat()
            import datetime
            return {
                "status": "success",
                "path": path,
                "public_url": abs_path.as_uri(),
                "size_bytes": stat.st_size,
                "content_type": mimetypes.guess_type(path)[0] or "application/octet-stream",
                "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception as e:
            logger.error("get_file_metadata failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    # ------------------------------------------------------------------
    # Search / Edit
    # ------------------------------------------------------------------

    @tool
    def search_in_files(
        self,
        query: str,
        prefix: str = "",
        extension_filter: Optional[str] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for a text string across all files under a given prefix.

        Args:
            query:            Text to search for (case-insensitive).
            prefix:           Logical path prefix to limit the search scope.
            extension_filter: Only search files with this extension.
            max_results:      Maximum number of matching files to return.
        """
        try:
            listing = self.list_files(prefix=prefix, extension_filter=extension_filter, max_results=500)
            if listing["status"] != "success":
                return listing

            matches = []
            for file_info in listing["files"]:
                result = self.read_file(file_info["path"])
                if result["status"] != "success":
                    continue
                content = result["content"]
                if query.lower() in content.lower():
                    hit_lines = [
                        {"line_number": i + 1, "line": line.strip()}
                        for i, line in enumerate(content.splitlines())
                        if query.lower() in line.lower()
                    ]
                    matches.append({
                        "path": file_info["path"],
                        "hit_count": len(hit_lines),
                        "hits": hit_lines,
                    })
                if len(matches) >= max_results:
                    break

            return {"status": "success", "query": query, "matches": matches, "match_count": len(matches)}
        except Exception as e:
            logger.error("search_in_files failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def replace_in_file(
        self,
        path: str,
        find: str,
        replace: str,
        replace_all: bool = True,
    ) -> Dict[str, Any]:
        """
        Find-and-replace text within a file.

        Args:
            path:        Logical file path.
            find:        Text to find.
            replace:     Replacement text.
            replace_all: Replace all occurrences (default True); False replaces only the first.
        """
        try:
            read_result = self.read_file(path)
            if read_result["status"] != "success":
                return read_result
            original = read_result["content"]
            updated = original.replace(find, replace) if replace_all else original.replace(find, replace, 1)
            occurrences = original.count(find)
            write_result = self.write_file(path, updated)
            if write_result["status"] != "success":
                return write_result
            return {
                "status": "success",
                "path": path,
                "occurrences_replaced": occurrences if replace_all else min(occurrences, 1),
            }
        except Exception as e:
            logger.error("replace_in_file failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    @tool
    def read_lines(
        self,
        path: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Read a specific range of lines from a text file.

        Args:
            path:       Logical file path.
            start_line: First line to return (1-indexed).
            end_line:   Last line to return (inclusive). Omit to read to end of file.
        """
        try:
            read_result = self.read_file(path)
            if read_result["status"] != "success":
                return read_result
            lines = read_result["content"].splitlines()
            total = len(lines)
            sliced = lines[start_line - 1: end_line]
            return {
                "status": "success",
                "path": path,
                "start_line": start_line,
                "end_line": end_line or total,
                "total_lines": total,
                "content": "\n".join(sliced),
            }
        except Exception as e:
            logger.error("read_lines failed: %s", e)
            return {"status": "failed", "error": str(e), "path": path}

    # ------------------------------------------------------------------
    # Folder operations
    # ------------------------------------------------------------------

    @tool
    def create_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Create a folder (and any missing parent directories).

        Args:
            folder_path: Logical folder path e.g. 'scripts/drafts'.
        """
        try:
            abs_path = self._resolve(folder_path)
            abs_path.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "folder_path": folder_path, "public_url": abs_path.as_uri()}
        except Exception as e:
            logger.error("create_folder failed: %s", e)
            return {"status": "failed", "error": str(e), "folder_path": folder_path}

    @tool
    def delete_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Delete an entire folder and all its contents.

        Args:
            folder_path: Logical folder path to delete recursively.
        """
        try:
            abs_path = self._resolve(folder_path)
            if abs_path.exists():
                deleted_count = sum(1 for _ in abs_path.rglob("*") if _.is_file())
                shutil.rmtree(abs_path)
            else:
                deleted_count = 0
            return {"status": "success", "folder_path": folder_path, "deleted_files": deleted_count}
        except Exception as e:
            logger.error("delete_folder failed: %s", e)
            return {"status": "failed", "error": str(e), "folder_path": folder_path}

    # ------------------------------------------------------------------
    # URL
    # ------------------------------------------------------------------

    @tool
    def get_public_url(self, path: str) -> Dict[str, Any]:
        """
        Get the local file:// URL for a file.

        Args:
            path: Logical file path.
        """
        try:
            abs_path = self._resolve(path)
            return {
                "status": "success",
                "path": path,
                "url": abs_path.as_uri(),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e), "path": path}
