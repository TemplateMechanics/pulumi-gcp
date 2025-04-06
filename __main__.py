import yaml
import pulumi
from gcpclassic import GCPResourceBuilder
from typing import Dict, Any

def load_config(file_path: str) -> Dict[str, Any]:
    """Load and validate YAML configuration from the given file path."""
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)
    
    # For GCP, ensure required keys exist: team, service, environment, and region.
    required_keys = ["team", "service", "environment", "region"]
    for key in required_keys:
        if key not in config_data:
            raise ValueError(f"Missing required configuration key: {key}")
    
    return config_data

def main():
    # Load YAML configuration.
    config_data = load_config("config.yaml")

    try:
        builder = GCPResourceBuilder(config_data)
    except Exception as e:
        pulumi.log.error(f"Failed to initialize GCPResourceBuilder: {e}")
        raise

    try:
        builder.build()
    except Exception as e:
        pulumi.log.error(f"Failed during resource build: {e}")
        raise

    # Export resource IDs if available.
    for name, resource in builder.resources.items():
        try:
            pulumi.export(name, resource.id)
        except Exception as e:
            pulumi.log.warn(f"Failed to export resource '{name}': {e}")

if __name__ == "__main__":
    main()
