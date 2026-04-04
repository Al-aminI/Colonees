"""
Knowledge Base Tool Provider

Provides search_knowledge_base tool to specialist agents so they can
query uploaded documents at runtime.
"""

from colon.agents.tools.knowledge.knowledge_tools import KnowledgeBaseToolProvider

__all__ = ["KnowledgeBaseToolProvider"]
