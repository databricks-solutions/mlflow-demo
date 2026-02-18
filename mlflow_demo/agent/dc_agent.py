"""DC Assistant Agent - Tool-calling agent for NFL defensive coordinator analysis.

This module re-exports the agent from agent.py for backwards compatibility.
All agent/LLM calls should use the centralized AGENT from mlflow_demo.agent.agent.
"""

from mlflow_demo.agent.agent import AGENT, ToolCallingAgent, get_agent

# Re-export for backwards compatibility
DcAssistantAgent = ToolCallingAgent

__all__ = ['AGENT', 'DcAssistantAgent', 'ToolCallingAgent', 'get_agent']
