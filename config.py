from dataclass_wizard import YAMLWizard, asdict
from typing import Dict, Any, Sequence ,Optional, List
from dataclasses import dataclass, field
@dataclass
class BucketArgs:
    name: Optional[str] = None
    location: Optional[str] = None
    project: Optional[str] = None
    labels: Optional[dict[str, str]] = None
@dataclass
class Buckets:
    name: str
    id: Optional[str] = None
    args: Optional[BucketArgs] = None
### https://www.pulumi.com/registry/packages/google-native/api-docs/storage/v1/bucket/ ###
@dataclass
class GCPNative:
    buckets: Optional[List[Buckets]] = None
### https://www.pulumi.com/registry/packages/google-native/ ###
@dataclass
class Environment:
    name: str
    labels: Optional[dict[str, str]] = None
    location: Optional[str] = None
    project: Optional[str] = None
    gcp_native: Optional[GCPNative] = None
@dataclass
class Service:
    name: str
    environments: List[Environment]
@dataclass
class Team:
    name: str
    services: List[Service]
@dataclass
class Config(YAMLWizard):
    teams: List[Team]
### Base Config ###