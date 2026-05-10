#!/usr/bin/env python3
"""
Production MCP Server for Colonees — Web Fetch, Time, and Utilities.

Registered as a stdio MCP server in Colonees. Provides real tools that
agents can use at runtime — no API keys required for basic operations.
"""
import json
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Colonees Tools")


@mcp.tool()
def get_current_utc_time() -> str:
    """Return the current UTC date and time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def fetch_web_page(url: str) -> str:
    """
    Fetch a web page and return its text content.
    Use this to read documentation, articles, or any public web content.
    Returns the first 8000 characters of the page text.
    """
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Colonees/1.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "text/html" in content_type:
                text = resp.text
                try:
                    from html.parser import HTMLParser
                    class TextExtractor(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.text = []
                            self.skip = False
                        def handle_starttag(self, tag, attrs):
                            if tag in ('script', 'style', 'noscript'):
                                self.skip = True
                        def handle_endtag(self, tag):
                            if tag in ('script', 'style', 'noscript'):
                                self.skip = False
                        def handle_data(self, data):
                            if not self.skip:
                                self.text.append(data)
                    extractor = TextExtractor()
                    extractor.feed(text)
                    text = ' '.join(extractor.text)
                except Exception:
                    pass
                text = ' '.join(text.split())[:8000]
                return text if text.strip() else "(empty page)"
            elif "application/json" in content_type:
                data = resp.json()
                return json.dumps(data, indent=2)[:8000]
            else:
                return resp.text[:8000]
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@mcp.tool()
def http_get_json(url: str) -> str:
    """
    Make an HTTP GET request and return the JSON response.
    Useful for querying public APIs.
    """
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers={"User-Agent": "Colonees/1.0"})
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, indent=2)[:8000]
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
