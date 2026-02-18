"""Agent module for MLflow demo.

This module contains the DC Assistant agent for NFL defensive coordinator analysis.
"""

from mlflow_demo.agent.agent import AGENT, ToolCallingAgent, get_agent

__all__ = ['AGENT', 'ToolCallingAgent', 'get_agent']
