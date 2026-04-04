"""
Knowledge Base Tool Provider

Gives specialist agents the ability to search knowledge bases at runtime.
Follows the same pattern as other tool providers in colon/agents/tools/:
returns a list of @tool-decorated callables for use in Agent(tools=[...]).
"""

import logging
from typing import Any, Dict, List, Optional

from strands import tool

from colon.core.knowledge_base import KnowledgeBaseManager

logger = logging.getLogger(__name__)


class KnowledgeBaseToolProvider:
    """
    Provides a ``search_knowledge_base`` tool to specialist agents.

    Instantiated with a shared :class:`KnowledgeBaseManager` and an optional
    list of knowledge base names the agent is allowed to query.  If no names
    are specified, the tool searches all enabled knowledge bases.
    """

    def __init__(self, kb_manager: KnowledgeBaseManager, kb_names: Optional[List[str]] = None):
        self.kb_manager = kb_manager
        self.kb_names = kb_names or []

    def get_tools(self) -> List:
        """
        Return Strands-compatible tool callables for searching knowledge bases.

        The returned list can be passed directly into ``Agent(tools=[...])``.
        """
        # Capture references for closure
        manager = self.kb_manager
        allowed_names = self.kb_names

        @tool
        def search_knowledge_base(
            query: str,
            top_k: int = 5,
        ) -> Dict[str, Any]:
            """
            Search the knowledge base for information relevant to the query.

            Use this tool when you need to find information from uploaded
            documents (PDFs, CSVs, text files, markdown) that have been added
            to the platform's knowledge bases.

            Args:
                query:  Natural-language search query describing what you need.
                top_k:  Maximum number of results to return (default 5).

            Returns:
                A dict with status and a list of matching chunks, each
                containing ``content``, ``source``, ``score``, and
                ``knowledge_base`` fields.
            """
            try:
                results = manager.search_all(
                    query=query,
                    kb_names=allowed_names if allowed_names else None,
                    top_k=top_k,
                )
                return {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "result_count": len(results),
                }
            except Exception as exc:
                logger.error("search_knowledge_base failed: %s", exc)
                return {
                    "status": "failed",
                    "error": str(exc),
                    "query": query,
                    "results": [],
                    "result_count": 0,
                }

        return [search_knowledge_base]

    def get_capabilities(self) -> List[str]:
        """Return capability strings this provider covers."""
        return ["knowledge_base_search"]
