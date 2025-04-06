"""
This module defines the data structures for our GCP YAML-Based Infrastructure Builder.
These dataclasses provide a schema for configuration and can be extended for validation or IDE support.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class GCPResource:
    name: str
    type: str
    args: Dict[str, Any]

@dataclass
class Config:
    team: str
    service: str
    environment: str
    region: str
    labels: Optional[Dict[str, str]] = None
    gcp_resources: Optional[List[GCPResource]] = None
