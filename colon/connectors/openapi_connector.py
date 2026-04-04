import json
import logging
import re
import httpx
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class OpenAPIConnector:
    """
    Parses an OpenAPI/Swagger spec and generates callable tool functions.

    Given a Swagger URL or dict, this connector:
    1. Fetches and parses the spec
    2. Extracts all endpoints with their parameters, request bodies, and descriptions
    3. Generates a @tool-decorated function for each endpoint
    4. Each tool function makes the actual HTTP call with proper auth
    """

    def __init__(self, spec_url_or_dict: str | Dict, base_url: str = None,
                 auth_type: str = None, auth_value: str = None,
                 auth_header_name: str = "Authorization"):
        """
        Args:
            spec_url_or_dict: URL to fetch OpenAPI spec from, or the spec dict directly
            base_url: Override base URL for API calls (uses spec's servers[0] if not provided)
            auth_type: "bearer", "api_key", "basic", or None
            auth_value: The token/key value
            auth_header_name: Header name for API key auth (default: "Authorization")
        """
        self.spec = self._load_spec(spec_url_or_dict)
        self.base_url = base_url or self._extract_base_url()
        self.auth_headers = self._build_auth_headers(auth_type, auth_value, auth_header_name)

    def _load_spec(self, spec_url_or_dict) -> Dict:
        if isinstance(spec_url_or_dict, dict):
            return spec_url_or_dict
        # Fetch from URL
        try:
            resp = httpx.get(spec_url_or_dict, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            if spec_url_or_dict.endswith(('.yaml', '.yml')):
                import yaml
                return yaml.safe_load(resp.text)
            return resp.json()
        except Exception as e:
            raise ValueError(f"Failed to load OpenAPI spec from {spec_url_or_dict}: {e}")

    def _extract_base_url(self) -> str:
        # OpenAPI 3.x
        servers = self.spec.get('servers', [])
        if servers:
            return servers[0].get('url', '').rstrip('/')
        # Swagger 2.x
        host = self.spec.get('host', 'localhost')
        base_path = self.spec.get('basePath', '')
        schemes = self.spec.get('schemes', ['https'])
        return f"{schemes[0]}://{host}{base_path}".rstrip('/')

    def _build_auth_headers(self, auth_type: str, auth_value: str, header_name: str) -> Dict[str, str]:
        if not auth_type or not auth_value:
            return {}
        if auth_type == "bearer":
            return {"Authorization": f"Bearer {auth_value}"}
        elif auth_type == "api_key":
            return {header_name: auth_value}
        elif auth_type == "basic":
            import base64
            encoded = base64.b64encode(auth_value.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        return {}

    def generate_tools(self) -> List[Callable]:
        """Generate @tool functions for each endpoint in the spec."""
        from strands import tool

        tools = []
        paths = self.spec.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ('get', 'post', 'put', 'delete', 'patch'):
                    tool_fn = self._create_endpoint_tool(path, method, details)
                    if tool_fn:
                        tools.append(tool_fn)

        logger.info(f"Generated {len(tools)} tools from OpenAPI spec")
        return tools

    def get_tool_names(self) -> List[str]:
        """Get the names of tools that would be generated."""
        names = []
        paths = self.spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ('get', 'post', 'put', 'delete', 'patch'):
                    name = self._make_tool_name(path, method, details)
                    names.append(name)
        return names

    def _make_tool_name(self, path: str, method: str, details: Dict) -> str:
        """Create a clean tool name from path + method."""
        # Use operationId if available
        op_id = details.get('operationId')
        if op_id:
            # Clean: camelCase -> snake_case, remove non-alphanumeric
            name = re.sub(r'([A-Z])', r'_\1', op_id).lower().strip('_')
            name = re.sub(r'[^a-z0-9_]', '_', name)
            name = re.sub(r'_+', '_', name)
            return name[:60]
        # Build from path + method
        clean_path = path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
        clean_path = re.sub(r'[^a-z0-9_]', '_', clean_path.lower())
        clean_path = re.sub(r'_+', '_', clean_path)
        return f"{method}_{clean_path}"[:60]

    def _extract_parameters(self, details: Dict) -> Dict[str, Dict]:
        """Extract parameters from endpoint definition."""
        params = {}
        for param in details.get('parameters', []):
            name = param.get('name', '')
            schema = param.get('schema', {})
            params[name] = {
                'type': schema.get('type', 'string'),
                'description': param.get('description', ''),
                'required': param.get('required', False),
                'in': param.get('in', 'query'),  # query, path, header
            }
        # Extract request body (OpenAPI 3.x)
        request_body = details.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            # If it's an object with properties, add each as a body param
            if schema.get('type') == 'object' and 'properties' in schema:
                required_fields = schema.get('required', [])
                for prop_name, prop_schema in schema['properties'].items():
                    params[prop_name] = {
                        'type': prop_schema.get('type', 'string'),
                        'description': prop_schema.get('description', ''),
                        'required': prop_name in required_fields,
                        'in': 'body',
                    }
            else:
                # Treat entire body as a single JSON param
                params['request_body'] = {
                    'type': 'string',
                    'description': 'JSON request body',
                    'required': request_body.get('required', False),
                    'in': 'body',
                }
        return params

    def _create_endpoint_tool(self, path: str, method: str, details: Dict) -> Optional[Callable]:
        """Create a @tool function for a single endpoint."""
        from strands import tool

        tool_name = self._make_tool_name(path, method, details)
        summary = details.get('summary', details.get('description', f'{method.upper()} {path}'))
        params = self._extract_parameters(details)
        base_url = self.base_url
        auth_headers = self.auth_headers

        # Build the docstring with parameter info
        param_docs = []
        for pname, pinfo in params.items():
            req = " (required)" if pinfo['required'] else " (optional)"
            param_docs.append(f"  {pname}: {pinfo['type']}{req} - {pinfo['description']}")
        docstring = f"{summary}\n\nParameters:\n" + "\n".join(param_docs) if param_docs else summary

        # Capture all params in closure
        endpoint_path = path
        endpoint_method = method
        endpoint_params = params

        def make_tool(t_name, t_doc, e_path, e_method, e_params, b_url, a_headers):
            @tool(name=t_name, description=t_doc)
            def api_call(tool_input: dict, **kwargs) -> dict:
                """Call the API endpoint with the given parameters."""
                import httpx as _httpx

                url = b_url + e_path
                query_params = {}
                headers = {**a_headers, 'Content-Type': 'application/json'}
                body = {}

                # Route input parameters to the right places
                input_data = tool_input if isinstance(tool_input, dict) else {}
                for pname, pinfo in e_params.items():
                    val = input_data.get(pname)
                    if val is None:
                        continue
                    if pinfo['in'] == 'path':
                        url = url.replace('{' + pname + '}', str(val))
                    elif pinfo['in'] == 'query':
                        query_params[pname] = val
                    elif pinfo['in'] == 'header':
                        headers[pname] = str(val)
                    elif pinfo['in'] == 'body':
                        if pname == 'request_body':
                            try:
                                body = json.loads(val) if isinstance(val, str) else val
                            except (json.JSONDecodeError, TypeError):
                                body = val
                        else:
                            body[pname] = val

                try:
                    with _httpx.Client(timeout=30) as client:
                        if e_method == 'get':
                            resp = client.get(url, params=query_params, headers=headers)
                        elif e_method == 'post':
                            resp = client.post(url, params=query_params, headers=headers, json=body or None)
                        elif e_method == 'put':
                            resp = client.put(url, params=query_params, headers=headers, json=body or None)
                        elif e_method == 'delete':
                            resp = client.delete(url, params=query_params, headers=headers)
                        elif e_method == 'patch':
                            resp = client.patch(url, params=query_params, headers=headers, json=body or None)
                        else:
                            return {"error": f"Unsupported method: {e_method}"}

                    # Parse response
                    try:
                        response_data = resp.json()
                    except Exception:
                        response_data = resp.text

                    return {
                        "status_code": resp.status_code,
                        "data": response_data,
                    }
                except Exception as e:
                    return {"error": str(e)}

            return api_call

        try:
            return make_tool(tool_name, docstring, endpoint_path, endpoint_method,
                           endpoint_params, base_url, auth_headers)
        except Exception as e:
            logger.warning(f"Failed to create tool for {method.upper()} {path}: {e}")
            return None

    def get_spec_info(self) -> Dict[str, Any]:
        """Get summary info about the loaded spec."""
        info = self.spec.get('info', {})
        paths = self.spec.get('paths', {})
        endpoint_count = sum(
            1 for methods in paths.values()
            for m in methods
            if m in ('get', 'post', 'put', 'delete', 'patch')
        )
        return {
            'title': info.get('title', 'Unknown API'),
            'version': info.get('version', ''),
            'description': info.get('description', ''),
            'base_url': self.base_url,
            'endpoints': endpoint_count,
            'paths': list(paths.keys()),
        }
