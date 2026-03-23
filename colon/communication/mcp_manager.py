"""
Colonees MCP Tool Manager
Tool integration via Model Context Protocol
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from strands import Agent, tool

from ..core.model_config import get_model

logger = logging.getLogger(__name__)


class StrandsMCPToolManager:
    """
    MCP Tool Manager for Colonees with Strands integration

    Provides:
    - Built-in tool integration
    - Custom tool registration and management
    - Tool execution with timeout handling and error recovery
    - Tool invocation logging and monitoring
    """

    def __init__(self, gateway_client=None):
        self.gateway = gateway_client
        
        # Import Strands built-in tools
        try:
            from strands_tools import file_read, file_write
            self.built_in_tools = [file_read, file_write]
        except ImportError:
            logger.warning("Strands tools not available, using empty built-in tools list")
            self.built_in_tools = []
        
        # Tool registry
        self.custom_tools: Dict[str, Any] = {}
        self.tool_stats = {
            'total_tool_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'average_execution_time': 0.0,
            'tools_registered': 0
        }
        
        # Tool execution configuration
        self.execution_config = {
            'default_timeout': 15000,  # 15 seconds in milliseconds
            'max_retries': 2,
            'sandbox_enabled': True,
            'logging_enabled': True
        }
        
        logger.info("Strands MCP Tool Manager initialized")
    
    def create_agent(
        self,
        specialization: str,
        custom_tools: Optional[List] = None
    ) -> Agent:
        """Create Strands agent with tools"""

        tools = self.built_in_tools.copy()
        if custom_tools:
            tools.extend(custom_tools)

        tools.append(self.execute_gateway_tool)

        agent = Agent(
            name=f"{specialization}_agent",
            tools=tools,
            system_prompt=f"You are a {specialization} specialist agent with access to tools and external services.",
            model=get_model()
        )

        logger.info(f"Agent created: {specialization} with {len(tools)} tools")
        return agent
    
    @tool
    async def execute_gateway_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Custom tool that wraps AgentCore Gateway access"""
        
        start_time = datetime.now()
        
        try:
            # Log tool invocation
            if self.execution_config['logging_enabled']:
                logger.info(f"Executing gateway tool: {tool_name} with parameters: {parameters}")
            
            # Execute tool through AgentCore Gateway
            result = await self.gateway.call_tool(
                tool_name=tool_name,
                parameters=parameters,
                timeout=self.execution_config['default_timeout']
            )
            
            # Update success statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_success_stats(execution_time)
            
            logger.debug(f"Gateway tool {tool_name} executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            # Update failure statistics
            self._update_failure_stats()
            
            logger.error(f"Gateway tool {tool_name} execution failed: {e}")
            
            # Attempt retry if configured
            if self.execution_config['max_retries'] > 0:
                return await self._retry_tool_execution(tool_name, parameters, 1)
            else:
                raise
    
    async def _retry_tool_execution(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        attempt: int
    ) -> Dict[str, Any]:
        """Retry tool execution with exponential backoff"""
        
        if attempt > self.execution_config['max_retries']:
            raise Exception(f"Tool {tool_name} failed after {self.execution_config['max_retries']} retries")
        
        # Exponential backoff delay
        delay = min(2 ** (attempt - 1), 10)  # Max 10 seconds
        logger.info(f"Retrying tool {tool_name} in {delay}s (attempt {attempt})")
        await asyncio.sleep(delay)
        
        try:
            result = await self.gateway.call_tool(
                tool_name=tool_name,
                parameters=parameters,
                timeout=self.execution_config['default_timeout']
            )
            
            logger.info(f"Tool {tool_name} succeeded on retry attempt {attempt}")
            return result
            
        except Exception as e:
            logger.warning(f"Tool {tool_name} retry attempt {attempt} failed: {e}")
            return await self._retry_tool_execution(tool_name, parameters, attempt + 1)
    
    async def register_custom_tool(
        self, 
        tool_name: str, 
        tool_function: callable,
        description: str = "",
        parameters_schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a custom tool"""
        
        try:
            tool_info = {
                'name': tool_name,
                'function': tool_function,
                'description': description,
                'parameters_schema': parameters_schema or {},
                'registered_at': datetime.now().isoformat(),
                'call_count': 0,
                'success_count': 0,
                'failure_count': 0
            }
            
            self.custom_tools[tool_name] = tool_info
            self.tool_stats['tools_registered'] += 1
            
            logger.info(f"Custom tool registered: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register custom tool {tool_name}: {e}")
            return False
    
    async def execute_custom_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a custom tool"""
        
        if tool_name not in self.custom_tools:
            raise ValueError(f"Custom tool {tool_name} not found")
        
        tool_info = self.custom_tools[tool_name]
        start_time = datetime.now()
        
        try:
            # Update call count
            tool_info['call_count'] += 1
            
            # Execute tool function
            if asyncio.iscoroutinefunction(tool_info['function']):
                result = await tool_info['function'](**parameters)
            else:
                result = tool_info['function'](**parameters)
            
            # Update success statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            tool_info['success_count'] += 1
            self._update_success_stats(execution_time)
            
            logger.debug(f"Custom tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            # Update failure statistics
            tool_info['failure_count'] += 1
            self._update_failure_stats()
            
            logger.error(f"Custom tool {tool_name} execution failed: {e}")
            raise
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools from Gateway and Strands"""
        
        try:
            # Get tools from AgentCore Gateway
            gateway_tools = await self.gateway.list_tools()
            
            # Get Strands built-in tools
            strands_tools = [tool.__name__ for tool in self.built_in_tools]
            
            # Get custom tools
            custom_tool_names = list(self.custom_tools.keys())
            
            return {
                "gateway_tools": gateway_tools,
                "strands_tools": strands_tools,
                "custom_tools": custom_tool_names,
                "total_tools": len(gateway_tools) + len(strands_tools) + len(custom_tool_names)
            }
            
        except Exception as e:
            logger.error(f"Failed to list available tools: {e}")
            return {
                "gateway_tools": [],
                "strands_tools": [tool.__name__ for tool in self.built_in_tools],
                "custom_tools": list(self.custom_tools.keys()),
                "error": str(e)
            }
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool"""
        
        # Check custom tools first
        if tool_name in self.custom_tools:
            return self.custom_tools[tool_name].copy()
        
        # Check gateway tools
        try:
            gateway_tools = await self.gateway.list_tools()
            for tool in gateway_tools:
                if tool.get('name') == tool_name:
                    return tool
        except Exception as e:
            logger.error(f"Failed to get gateway tool info: {e}")
        
        # Check Strands built-in tools
        for tool in self.built_in_tools:
            if tool.__name__ == tool_name:
                return {
                    'name': tool.__name__,
                    'type': 'strands_builtin',
                    'description': tool.__doc__ or "Strands built-in tool",
                    'module': tool.__module__
                }
        
        return None
    
    def _update_success_stats(self, execution_time: float):
        """Update statistics on successful tool execution"""
        self.tool_stats['total_tool_calls'] += 1
        self.tool_stats['successful_calls'] += 1
        
        # Update average execution time
        total_calls = self.tool_stats['total_tool_calls']
        current_avg = self.tool_stats['average_execution_time']
        self.tool_stats['average_execution_time'] = (
            (current_avg * (total_calls - 1) + execution_time) / total_calls
        )
    
    def _update_failure_stats(self):
        """Update statistics on failed tool execution"""
        self.tool_stats['total_tool_calls'] += 1
        self.tool_stats['failed_calls'] += 1
    
    def configure_execution(self, config: Dict[str, Any]):
        """Configure tool execution parameters"""
        
        valid_keys = ['default_timeout', 'max_retries', 'sandbox_enabled', 'logging_enabled']
        
        for key, value in config.items():
            if key in valid_keys:
                self.execution_config[key] = value
                logger.info(f"Tool execution config updated: {key} = {value}")
            else:
                logger.warning(f"Invalid tool execution config key: {key}")
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool management statistics"""
        
        custom_tool_stats = {}
        for tool_name, tool_info in self.custom_tools.items():
            custom_tool_stats[tool_name] = {
                'call_count': tool_info['call_count'],
                'success_count': tool_info['success_count'],
                'failure_count': tool_info['failure_count'],
                'success_rate': (
                    tool_info['success_count'] / tool_info['call_count'] 
                    if tool_info['call_count'] > 0 else 0
                )
            }
        
        return {
            'overall_stats': self.tool_stats.copy(),
            'custom_tool_stats': custom_tool_stats,
            'execution_config': self.execution_config.copy(),
            'built_in_tools_count': len(self.built_in_tools)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on tool systems"""
        
        health_status = {
            'gateway_connection': False,
            'strands_tools': len(self.built_in_tools) > 0,
            'custom_tools': len(self.custom_tools),
            'overall_health': 'unknown'
        }
        
        # Test gateway connection
        try:
            await self.gateway.list_tools()
            health_status['gateway_connection'] = True
        except Exception as e:
            logger.warning(f"Gateway health check failed: {e}")
        
        # Determine overall health
        if health_status['gateway_connection'] and health_status['strands_tools']:
            health_status['overall_health'] = 'healthy'
        elif health_status['gateway_connection'] or health_status['strands_tools']:
            health_status['overall_health'] = 'degraded'
        else:
            health_status['overall_health'] = 'unhealthy'
        
        return health_status
    
    async def shutdown(self):
        """Shutdown tool manager"""
        
        # Clean up custom tools
        self.custom_tools.clear()
        
        # Close gateway connection if needed
        if hasattr(self.gateway, 'close'):
            try:
                await self.gateway.close()
            except Exception as e:
                logger.error(f"Error closing gateway connection: {e}")
        
        logger.info("Strands MCP Tool Manager shutdown complete")