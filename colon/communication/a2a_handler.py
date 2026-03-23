"""
Colonees A2A Message Handler
Agent-to-Agent communication via Strands A2A Protocol
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

from strands import Agent
from strands.agent.a2a_agent import A2AAgent

from ..core.model_config import get_model

logger = logging.getLogger(__name__)


class StrandsA2AMessageHandler:
    """
    A2A Protocol Message Handler for Colonees

    Provides:
    - Agent-to-agent communication via A2A Protocol
    - Message routing and delivery mechanisms
    - Communication retry and error handling
    - Circuit breakers for communication failures
    """

    def __init__(self, agent_name: str, tools: Optional[List] = None):
        self.agent_name = agent_name
        self.runtime_url = os.environ.get('RUNTIME_URL', 'http://127.0.0.1:9000/')

        self.a2a_agent = A2AAgent(
            name=agent_name,
            tools=tools or [],
            system_prompt=f"You are {agent_name}, a specialist agent capable of collaborating with other agents.",
            model=get_model()
        )
        
        # Message tracking and statistics
        self.message_stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'failed_messages': 0,
            'average_latency': 0.0,
            'circuit_breaker_trips': 0
        }
        
        # Circuit breaker configuration
        self.circuit_breaker = {
            'failure_threshold': 5,
            'recovery_timeout': 60,  # seconds
            'current_failures': 0,
            'state': 'closed',  # closed, open, half_open
            'last_failure_time': None
        }
        
        # Retry configuration
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,  # seconds
            'max_delay': 30.0,  # seconds
            'exponential_base': 2.0
        }
        
        logger.info(f"Strands A2A Message Handler initialized for agent: {agent_name}")
    
    async def send_message(
        self, 
        target_agent: str, 
        message: Dict[str, Any],
        timeout: float = 50.0  # 50ms delivery requirement
    ) -> Dict[str, Any]:
        """Send message to another agent via Strands A2A protocol with retry logic"""
        
        # Check circuit breaker
        if not self._check_circuit_breaker():
            raise Exception(f"Circuit breaker is open for agent communication")
        
        start_time = datetime.now()
        
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                # Use Strands A2A agent to send message
                response = await self.a2a_agent.send_message(
                    target_agent_id=target_agent,
                    message=message,
                    timeout=timeout
                )
                
                # Update statistics on success
                latency = (datetime.now() - start_time).total_seconds() * 1000  # ms
                self._update_success_stats(latency)
                
                logger.debug(f"Message sent successfully to {target_agent} in {latency:.2f}ms")
                return response
                
            except Exception as e:
                logger.warning(f"Message send attempt {attempt + 1} failed to {target_agent}: {e}")
                
                if attempt < self.retry_config['max_retries']:
                    # Calculate exponential backoff delay
                    delay = min(
                        self.retry_config['base_delay'] * (self.retry_config['exponential_base'] ** attempt),
                        self.retry_config['max_delay']
                    )
                    
                    logger.debug(f"Retrying message to {target_agent} in {delay:.2f}s")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    self._update_failure_stats()
                    raise Exception(f"Failed to send message to {target_agent} after {self.retry_config['max_retries']} retries: {e}")
    
    async def handle_incoming_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming A2A messages through Strands framework"""
        try:
            start_time = datetime.now()
            
            # Log incoming message
            logger.debug(f"Received A2A message: {message.get('type', 'unknown')} from {message.get('sender', 'unknown')}")
            
            # Use A2A agent to process message
            response = await self.a2a_agent.process_message(message)
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
            self.message_stats['messages_received'] += 1
            
            logger.debug(f"Message processed in {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Failed to handle incoming message: {e}")
            self.message_stats['failed_messages'] += 1
            raise
    
    async def broadcast_message(
        self, 
        target_agents: List[str], 
        message: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Broadcast message to multiple agents"""
        results = {}
        
        # Send messages concurrently
        tasks = []
        for target_agent in target_agents:
            task = asyncio.create_task(
                self.send_message(target_agent, message),
                name=f"broadcast_to_{target_agent}"
            )
            tasks.append((target_agent, task))
        
        # Wait for all messages to complete
        for target_agent, task in tasks:
            try:
                response = await task
                results[target_agent] = {
                    'status': 'success',
                    'response': response
                }
            except Exception as e:
                results[target_agent] = {
                    'status': 'failed',
                    'error': str(e)
                }
                logger.error(f"Broadcast failed to {target_agent}: {e}")
        
        logger.info(f"Broadcast completed to {len(target_agents)} agents")
        return results
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows communication"""
        current_time = datetime.now()
        
        if self.circuit_breaker['state'] == 'open':
            # Check if recovery timeout has passed
            if (self.circuit_breaker['last_failure_time'] and 
                (current_time - self.circuit_breaker['last_failure_time']).total_seconds() > 
                self.circuit_breaker['recovery_timeout']):
                
                # Move to half-open state
                self.circuit_breaker['state'] = 'half_open'
                logger.info("Circuit breaker moved to half-open state")
                return True
            else:
                return False
        
        return True  # closed or half_open states allow communication
    
    def _update_success_stats(self, latency_ms: float):
        """Update statistics on successful message"""
        self.message_stats['messages_sent'] += 1
        
        # Update average latency
        total_messages = self.message_stats['messages_sent']
        current_avg = self.message_stats['average_latency']
        self.message_stats['average_latency'] = (
            (current_avg * (total_messages - 1) + latency_ms) / total_messages
        )
        
        # Reset circuit breaker on success
        if self.circuit_breaker['state'] == 'half_open':
            self.circuit_breaker['state'] = 'closed'
            self.circuit_breaker['current_failures'] = 0
            logger.info("Circuit breaker reset to closed state")
    
    def _update_failure_stats(self):
        """Update statistics on failed message"""
        self.message_stats['failed_messages'] += 1
        self.circuit_breaker['current_failures'] += 1
        self.circuit_breaker['last_failure_time'] = datetime.now()
        
        # Check if circuit breaker should trip
        if (self.circuit_breaker['current_failures'] >= self.circuit_breaker['failure_threshold'] and
            self.circuit_breaker['state'] == 'closed'):
            
            self.circuit_breaker['state'] = 'open'
            self.message_stats['circuit_breaker_trips'] += 1
            logger.warning(f"Circuit breaker tripped for agent {self.agent_name}")
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """Get agent card information for A2A discovery"""
        return {
            'agent_id': self.agent_name,
            'name': self.agent_name,
            'description': f"Colonees specialist agent {self.agent_name} with A2A communication capabilities",
            'capabilities': [tool.__name__ for tool in self.a2a_agent.tools] if self.a2a_agent.tools else [],
            'endpoints': {
                'a2a': f"{self.runtime_url}/.well-known/agent-card.json"
            },
            'protocols': ['a2a', 'http'],
            'framework': 'strands',
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            'agent_name': self.agent_name,
            'message_stats': self.message_stats.copy(),
            'circuit_breaker': {
                'state': self.circuit_breaker['state'],
                'current_failures': self.circuit_breaker['current_failures'],
                'failure_threshold': self.circuit_breaker['failure_threshold']
            },
            'retry_config': self.retry_config.copy()
        }
    
    async def shutdown(self):
        """Shutdown A2A message handler"""
        logger.info(f"Strands A2A Message Handler shutdown for agent: {self.agent_name}")


class A2AMessageRouter:
    """
    Router for managing multiple A2A message handlers
    """
    
    def __init__(self):
        self.handlers: Dict[str, StrandsA2AMessageHandler] = {}
        self.routing_table: Dict[str, str] = {}  # message_type -> handler_name
        
        logger.info("A2A Message Router initialized")
    
    def register_handler(self, handler: StrandsA2AMessageHandler):
        """Register an A2A message handler"""
        self.handlers[handler.agent_name] = handler
        logger.info(f"A2A handler registered: {handler.agent_name}")
    
    def unregister_handler(self, agent_name: str):
        """Unregister an A2A message handler"""
        if agent_name in self.handlers:
            del self.handlers[agent_name]
            logger.info(f"A2A handler unregistered: {agent_name}")
    
    async def route_message(
        self, 
        message: Dict[str, Any], 
        target_handler: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route message to appropriate handler"""
        
        if target_handler and target_handler in self.handlers:
            handler = self.handlers[target_handler]
        else:
            # Use routing table or default to first available handler
            message_type = message.get('type', 'default')
            handler_name = self.routing_table.get(message_type)
            
            if handler_name and handler_name in self.handlers:
                handler = self.handlers[handler_name]
            elif self.handlers:
                handler = next(iter(self.handlers.values()))
            else:
                raise Exception("No A2A handlers available for message routing")
        
        return await handler.handle_incoming_message(message)
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        handler_stats = {}
        for name, handler in self.handlers.items():
            handler_stats[name] = handler.get_communication_stats()
        
        return {
            'total_handlers': len(self.handlers),
            'routing_table': self.routing_table.copy(),
            'handler_stats': handler_stats
        }
    
    async def shutdown(self):
        """Shutdown all handlers"""
        for handler in self.handlers.values():
            await handler.shutdown()
        
        self.handlers.clear()
        logger.info("A2A Message Router shutdown complete")