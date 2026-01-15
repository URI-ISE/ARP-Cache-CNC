"""
ARP-Cache-CNC Attack Scenarios and Research Framework

Comprehensive attack simulation, research scenarios, and defense mechanisms
for CNC machine security research.
"""

from .research_scenarios import ResearchScenarioManager, StatisticalDataLogger
from .prevention_modules import DefenseSystem
from .research_framework import ResearchExperimentFramework
from .attack_simulator import GCodeAttackSimulator

__version__ = "1.0.0"
__all__ = [
    "ResearchScenarioManager",
    "StatisticalDataLogger",
    "DefenseSystem",
    "ResearchExperimentFramework",
    "GCodeAttackSimulator",
]
