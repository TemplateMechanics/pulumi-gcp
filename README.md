# Pulumi YAML-Based Infrastructure Builder for GCP

This project provides a dynamic and extensible Pulumi-based infrastructure-as-code solution for Google Cloud Platform (GCP), fully configured using a YAML file. It automatically manages resource naming (with custom name overrides), supports referencing existing resources, allows dynamic linking between resources, and integrates secret resolution via Pulumi configuration to meet resource-specific naming requirements.

## 📂 Project Structure

```
.
├── __main__.py         # Entry point: parses YAML and builds GCP resources
├── gcpclassic.py       # GCP-specific logic, naming conventions, and secret resolution
├── config.py           # Dataclasses and dynamic Pulumi resource mapping
├── config.yaml         # User-defined infrastructure configuration
└── README.md           # Documentation (this file)
```

---

## 🚀 Features

- **YAML-defined infrastructure**: Define all infrastructure clearly in YAML.
- **Dynamic Pulumi resource mapping**: Automatically maps YAML definitions to Pulumi resource classes.
- **Intelligent resource naming**: Automatically incorporates team, service, environment, and region abbreviations.
- **GCP region abbreviation**: Converts full GCP region names (e.g., `us-central1`) into standardized abbreviations (e.g., `usc1`).
- **Resource referencing**: Use `ref:<resource-name>.<attribute>` syntax to dynamically link resources.
- **New and existing resources**: Seamlessly create new resources or fetch existing ones.
- **Custom name overrides**: Override generated names with a `custom_name` field for resources with strict naming rules.
- **Secret resolution**: Use `secret:<key>` in your YAML to securely reference sensitive data from Pulumi configuration.

---

## 📄 Example `config.yaml`

```yaml
team: "DevOps"
service: "test-svc"
environment: "dev"
region: "us-central1"
labels:
  owner: "test-user"
  project: "PulumiGCPDemo"

gcp_resources:
  - name: "network-01"
    type: "compute.Network"
    args:
      auto_create_subnetworks: false

  - name: "subnetwork-01"
    type: "compute.Subnetwork"
    args:
      network: "ref:network-01.self_link"
      ip_cidr_range: "10.0.0.0/16"
      region: "us-central1"
      private_ip_google_access: true

  - name: "sql-instance"
    type: "sql.DatabaseInstance"
    custom_name: "mycustomsqlinstance"  # Custom override for resources with naming restrictions.
    args:
      region: "us-central1"
      database_version: "MYSQL_5_7"
      settings:
        tier: "db-f1-micro"
      root_password: "secret:sqlInstancePassword"
```

---

## 🛠 Getting Started

```bash
pulumi login
pulumi stack init dev
pulumi config set gcp:region us-central1
pulumi config set sqlInstancePassword YOUR_SECRET_VALUE --secret
pulumi up
```

---

## 🔗 Referencing Resources

Use the syntax `ref:<resource-name>.<attribute>` to dynamically reference outputs from previously defined resources.

Example:

```yaml
network: "ref:network-01.self_link"
```

---

## 🏷 Resource Naming Convention

Resource names follow the pattern:

```
<team>-<service>-<environment>-<region-abbr>-<resource-name>
```

**Example:**

```
devops-test-svc-dev-usc1-network-01
```

GCP region abbreviations are automatically handled internally (e.g., `us-central1` → `usc1`).

---

## ⚙️ Dynamic Resource Resolution

The system automatically introspects Pulumi GCP packages (`pulumi_gcp`) to dynamically map resources without explicit resource class definitions, simplifying management and ensuring new resources are available as Pulumi updates.

---

## ✨ Potential Enhancements

- **Reusable YAML templates** for common resource patterns.
- **Multi-region and multi-environment support**.
- **Enhanced dependency visualization**.
- **Pre-execution YAML validation** to prevent configuration errors.

---

## 👥 Authors & Contributors

Developed using the **Benitez-Johnson Method** by:
- **Dave Johnson**
- **Christian Benitez**

Special thanks to **Brandon Rutledge** for architecture and implementation contributions.
