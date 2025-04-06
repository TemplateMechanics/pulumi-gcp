import pulumi
import inspect
import pulumi_gcp as gcp
import re
from typing import Any, Dict

# Consolidated list of common GCP region abbreviations
GCP_REGION_ABBREVIATIONS = {
    "asia-east1": "ase1",
    "asia-east2": "ase2",
    "asia-northeast1": "an1",
    "asia-northeast2": "an2",
    "asia-northeast3": "an3",
    "asia-south1": "as1",
    "asia-southeast1": "ase1",
    "asia-southeast2": "ase2",
    "australia-southeast1": "aus1",
    "australia-southeast2": "aus2",
    "europe-central2": "ec2",
    "europe-north1": "en1",
    "europe-west1": "ew1",
    "europe-west2": "ew2",
    "europe-west3": "ew3",
    "europe-west4": "ew4",
    "europe-west6": "ew6",
    "northamerica-northeast1": "nn1",
    "southamerica-east1": "se1",
    "us-central1": "usc1",
    "us-east1": "use1",
    "us-east4": "use4",
    "us-west1": "usw1",
    "us-west2": "usw2",
    "us-west3": "usw3",
    "us-west4": "usw4",
}

def to_snake_case(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def resolve_value(value: Any, resources: Dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: resolve_value(v, resources) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_value(item, resources) for item in value]
    elif isinstance(value, str):
        if value.startswith("secret:"):
            # Fetch secret from Pulumi config
            secret_key = value[len("secret:"):]
            config = pulumi.Config()
            return config.require_secret(secret_key)
        elif value.startswith("ref:"):
            ref_text = value[4:]
            if "." in ref_text:
                ref_res, ref_attr = ref_text.split(".", 1)
            else:
                ref_res, ref_attr = ref_text, "id"
            if ref_res not in resources:
                raise ValueError(f"Referenced resource '{ref_res}' not found.")
            resource_obj = resources[ref_res]
            attr_val = getattr(resource_obj, ref_attr, None)
            if attr_val is None:
                raise ValueError(f"Attribute '{ref_attr}' not found on resource '{ref_res}'")
            return attr_val
        else:
            return value
    else:
        return value

def get_lookup_params(required_params: set, resolved_args: dict) -> dict:
    lookup_params = {}
    for param in required_params:
        snake_key = to_snake_case(param)
        if snake_key in resolved_args:
            lookup_params[param] = resolved_args[snake_key]
        elif param in resolved_args:
            lookup_params[param] = resolved_args[param]
    return lookup_params

class GCPResourceBuilder:
    def __init__(self, config_data: dict):
        self.config = config_data
        self.resources: Dict[str, Any] = {}

    def get_abbreviation(self, region: str) -> str:
        return GCP_REGION_ABBREVIATIONS.get(region.lower(), region.split("-")[0].lower())

    def generate_resource_name(self, base_name: str) -> str:
        team = self.config.get("team", "team").strip().lower()
        service = self.config.get("service", "svc").strip().lower()
        env = self.config.get("environment", "dev").strip().lower()
        reg_abbr = self.get_abbreviation(self.config.get("region", "us-central1"))
        return f"{team}-{service}-{env}-{reg_abbr}-{base_name}".lower()

    def resolve_args(self, args: dict) -> dict:
        return {key: resolve_value(value, self.resources) for key, value in args.items()}

    def _apply_common_parameters(self, resolved_args: dict, init_sig: inspect.Signature) -> dict:
        # For GCP, many resources support 'labels' instead of 'tags'
        if "labels" in init_sig.parameters:
            resource_labels = self.config.get("labels")
            if resource_labels:
                resolved_args.setdefault("labels", resource_labels)
        else:
            resolved_args.pop("labels", None)

        # Handle 'region' if the resource expects it.
        if "region" in init_sig.parameters:
            if "region" not in resolved_args:
                resolved_args["region"] = self.config.get("region", "us-central1")
        else:
            resolved_args.pop("region", None)
        return resolved_args

    def build(self):
        gcp_resources = self.config.get("gcp_resources", [])
        for resource_cfg in gcp_resources:
            name = resource_cfg["name"]
            resource_type = resource_cfg["type"]
            args = resource_cfg.get("args", {}).copy()
            custom_name = resource_cfg.get("custom_name", None)
            is_existing = args.pop("existing", False)
            resolved_args = self.resolve_args(args)
            module_name, class_name = resource_type.rsplit(".", 1)
            module = getattr(gcp, module_name, None)
            if not module:
                pulumi.log.warn(f"GCP module '{module_name}' not found. Skipping '{name}'.")
                continue
            try:
                ResourceClass = getattr(module, class_name)
            except AttributeError:
                pulumi.log.warn(f"Resource class '{class_name}' not found in module '{module_name}'. Skipping '{name}'.")
                continue
            init_sig = inspect.signature(ResourceClass.__init__)
            if is_existing:
                get_func_name = f"get_{to_snake_case(class_name)}"
                try:
                    get_func = getattr(module, get_func_name)
                    sig = inspect.signature(get_func)
                    get_required = {k for k, param in sig.parameters.items() if k not in {"opts"} and param.default == param.empty}
                    get_params = get_lookup_params(get_required, resolved_args)
                    missing = get_required - set(get_params.keys())
                    if missing:
                        pulumi.log.warn(f"Missing required params {missing} for existing resource '{name}'. Skipping the lookup attempt.")
                    else:
                        existing_resource = get_func(**get_params)
                        self.resources[name] = existing_resource
                        pulumi.log.info(f"Fetched existing resource '{name}' via '{get_func_name}' with {get_params}")
                        continue
                except AttributeError:
                    pulumi.log.warn(f"Function '{get_func_name}' not found for '{resource_type}'. Proceeding to create new resource '{name}'.")
                except Exception as e:
                    pulumi.log.warn(f"Failed to retrieve existing resource '{name}': {e}. Proceeding with creation.")
                if "region" in init_sig.parameters and "region" not in resolved_args:
                    resolved_args["region"] = self.config.get("region", "us-central1")
                else:
                    resolved_args.pop("region", None)
            resolved_args = self._apply_common_parameters(resolved_args, init_sig)
            pulumi_name = custom_name if custom_name else self.generate_resource_name(name)
            pulumi.log.info(f"DEBUG for '{name}': final resolved_args => {resolved_args}")
            resource_instance = ResourceClass(pulumi_name, **resolved_args)
            self.resources[name] = resource_instance
            pulumi.log.info(f"Created resource: {pulumi_name} ({resource_type})")
