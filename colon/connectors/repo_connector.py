import os
import logging
import subprocess
from typing import Any, Callable, Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RepoConnector:
    """
    Clones a git repository, indexes its files, and provides search/read tools.

    This lets agents explore and understand a codebase.
    """

    def __init__(self, repo_url: str, data_dir: str, branch: str = "main",
                 access_token: str = None,
                 include_patterns: List[str] = None,
                 exclude_patterns: List[str] = None):
        self.repo_url = repo_url
        self.data_dir = data_dir
        self.branch = branch
        self.access_token = access_token
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.next', '.cache', '*.pyc', '*.pyo',
            '*.so', '*.dylib', '*.dll', '*.exe', '*.bin',
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico', '*.svg',
            '*.mp3', '*.mp4', '*.avi', '*.mov',
            '*.zip', '*.tar', '*.gz', '*.rar',
            '*.woff', '*.woff2', '*.ttf', '*.eot',
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        ]
        self.repo_dir = os.path.join(data_dir, 'repo')
        self._file_index: List[Dict[str, Any]] = []

    def clone_or_pull(self) -> Dict[str, Any]:
        """Clone the repo (or pull if already cloned). Returns sync stats."""
        auth_url = self._build_auth_url()

        if os.path.exists(os.path.join(self.repo_dir, '.git')):
            # Pull
            try:
                result = subprocess.run(
                    ['git', '-C', self.repo_dir, 'pull', 'origin', self.branch],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    logger.warning(f"Git pull failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"Git pull error: {e}")
        else:
            # Clone
            os.makedirs(self.repo_dir, exist_ok=True)
            try:
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', '--branch', self.branch,
                     auth_url, self.repo_dir],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                raise RuntimeError("Git clone timed out (300s limit)")

        # Index files
        self._index_files()

        # Get last commit
        last_commit = ""
        try:
            r = subprocess.run(
                ['git', '-C', self.repo_dir, 'log', '-1', '--format=%H %s'],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                last_commit = r.stdout.strip()
        except Exception:
            pass

        return {
            'files_indexed': len(self._file_index),
            'total_size_bytes': sum(f['size'] for f in self._file_index),
            'last_commit': last_commit,
            'synced_at': datetime.now(timezone.utc).isoformat(),
        }

    def _build_auth_url(self) -> str:
        if not self.access_token:
            return self.repo_url
        # Handle HTTPS URLs with token
        if self.repo_url.startswith('https://'):
            # https://github.com/user/repo -> https://token@github.com/user/repo
            return self.repo_url.replace('https://', f'https://{self.access_token}@')
        return self.repo_url

    def _should_include(self, rel_path: str) -> bool:
        """Check if file should be included in index."""
        import fnmatch
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return False
            # Check if any path component matches
            parts = rel_path.split(os.sep)
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return False
        if self.include_patterns:
            return any(fnmatch.fnmatch(rel_path, p) for p in self.include_patterns)
        return True

    def _index_files(self):
        """Walk the repo and index text files."""
        self._file_index = []
        if not os.path.exists(self.repo_dir):
            return

        for root, dirs, files in os.walk(self.repo_dir):
            # Skip excluded directories in-place
            dirs[:] = [d for d in dirs if self._should_include(d)]

            for fname in files:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.repo_dir)
                if not self._should_include(rel_path):
                    continue
                try:
                    size = os.path.getsize(full_path)
                    if size > 500_000:  # Skip files > 500KB
                        continue
                    self._file_index.append({
                        'path': rel_path,
                        'full_path': full_path,
                        'size': size,
                    })
                except OSError:
                    continue

    def search_code(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search indexed files for query terms. Returns matching chunks."""
        query_terms = set(query.lower().split())
        if not query_terms:
            return []

        results = []
        for finfo in self._file_index:
            try:
                with open(finfo['full_path'], 'r', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            content_lower = content.lower()
            # Check if any query terms appear
            matches = sum(1 for t in query_terms if t in content_lower)
            if matches == 0:
                continue

            score = matches / len(query_terms)

            # Extract relevant lines (lines containing query terms)
            lines = content.split('\n')
            relevant_lines = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(t in line_lower for t in query_terms):
                    # Include surrounding context (2 lines before/after)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    chunk = '\n'.join(f"L{start+j+1}: {lines[start+j]}" for j in range(end - start))
                    relevant_lines.append(chunk)
                    if len(relevant_lines) >= 3:  # Max 3 chunks per file
                        break

            if relevant_lines:
                results.append({
                    'file': finfo['path'],
                    'content': '\n---\n'.join(relevant_lines),
                    'score': score,
                    'size': finfo['size'],
                })

        results.sort(key=lambda r: r['score'], reverse=True)
        return results[:top_k]

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a specific file from the repo."""
        full_path = os.path.join(self.repo_dir, file_path)
        # Prevent path traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(self.repo_dir)):
            return {"error": "Invalid file path"}
        if not os.path.exists(full_path):
            return {"error": f"File not found: {file_path}"}
        try:
            with open(full_path, 'r', errors='ignore') as f:
                content = f.read()
            return {"file": file_path, "content": content, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}

    def list_files(self, directory: str = "", pattern: str = None) -> List[Dict[str, str]]:
        """List files in the repo, optionally filtered by directory and pattern."""
        import fnmatch
        results = []
        for finfo in self._file_index:
            if directory and not finfo['path'].startswith(directory):
                continue
            if pattern and not fnmatch.fnmatch(finfo['path'], pattern):
                continue
            results.append({'path': finfo['path'], 'size': finfo['size']})
        return results

    def get_structure(self, max_depth: int = 3) -> str:
        """Get a tree-like structure of the repo."""
        tree = {}
        for finfo in self._file_index:
            parts = finfo['path'].split(os.sep)
            if len(parts) > max_depth:
                parts = parts[:max_depth] + ['...']
            current = tree
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = None

        def render(node, prefix=""):
            lines = []
            items = sorted(node.items(), key=lambda x: (x[1] is not None, x[0]))
            for i, (name, subtree) in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if subtree is not None:
                    extension = "    " if is_last else "│   "
                    lines.extend(render(subtree, prefix + extension))
            return lines

        return '\n'.join(render(tree))

    def generate_tools(self) -> List[Callable]:
        """Generate @tool functions for interacting with the repo."""
        from strands import tool

        connector = self

        @tool(name="search_codebase",
              description="Search the connected codebase for code, functions, classes, or patterns. Returns matching file chunks with line numbers.")
        def search_codebase(tool_input: dict, **kwargs) -> dict:
            query = tool_input.get('query', '')
            top_k = tool_input.get('top_k', 10)
            results = connector.search_code(query, top_k)
            return {"results": results, "total_found": len(results)}

        @tool(name="read_repo_file",
              description="Read the full contents of a specific file from the connected repository.")
        def read_repo_file(tool_input: dict, **kwargs) -> dict:
            file_path = tool_input.get('file_path', '')
            return connector.read_file(file_path)

        @tool(name="list_repo_files",
              description="List files in the connected repository. Optionally filter by directory path or glob pattern.")
        def list_repo_files(tool_input: dict, **kwargs) -> dict:
            directory = tool_input.get('directory', '')
            pattern = tool_input.get('pattern', None)
            files = connector.list_files(directory, pattern)
            return {"files": files, "count": len(files)}

        @tool(name="get_repo_structure",
              description="Get a tree-like directory structure of the connected repository. Useful for understanding project layout.")
        def get_repo_structure(tool_input: dict, **kwargs) -> dict:
            max_depth = tool_input.get('max_depth', 3)
            structure = connector.get_structure(max_depth)
            return {"structure": structure}

        return [search_codebase, read_repo_file, list_repo_files, get_repo_structure]
