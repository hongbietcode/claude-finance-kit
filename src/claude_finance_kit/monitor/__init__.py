"""Realtime research monitor, paper execution, and notifications."""

from claude_finance_kit.monitor.config import MonitorConfig
from claude_finance_kit.monitor.engine import Monitor
from claude_finance_kit.monitor.flow import UnusualFlowConfig, UnusualFlowDetector
from claude_finance_kit.monitor.paper import PaperBroker
from claude_finance_kit.monitor.telegram import TelegramNotifier

__all__ = [
    "Monitor",
    "MonitorConfig",
    "UnusualFlowConfig",
    "UnusualFlowDetector",
    "PaperBroker",
    "TelegramNotifier",
]
