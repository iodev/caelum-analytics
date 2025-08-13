"""
Caelum Analytics - Real-time Monitoring Dashboard

A comprehensive Python-based monitoring, analytics, and visualization system 
for the Caelum MCP Server ecosystem.
"""

__version__ = "0.1.0"
__author__ = "Caelum Team"
__email__ = "team@caelum.dev"
__description__ = "Real-time monitoring, analytics, and visualization dashboard for Caelum MCP Server System"

from .config import Settings

__all__ = ["Settings", "__version__"]