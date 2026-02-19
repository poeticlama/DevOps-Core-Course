# Lab 04 — Infrastructure as Code (Terraform & Pulumi)

## 1. Infrastructure as Code (IaC) Approach

### Local VM Strategy

Rather than using cloud providers (AWS, GCP, Azure), this lab uses a local VMware-based virtual machine with Vagrant for infrastructure management. This approach offers several advantages:

**Benefits of Local VM for Learning:**
- No cloud costs or billing concerns
- Complete control over VM configuration
- Reproducible local environment
- Can be kept running for Lab 5 (Ansible) without additional costs
- Direct access via private network (192.168.56.0/24)

**Chosen Configuration:**
- **OS**: Ubuntu 24.04 LTS (noble64 Vagrant box)
- **Memory**: 2 GB RAM
- **CPUs**: 2 vCPUs
- **Network**: Private network (192.168.56.10)
- **Port Forwarding**: SSH (2222 → 22), App (5000 → 5000)

### Why Two IaC Tools?

The Lab 4 requirements mandate learning both Terraform and Pulumi on the same infrastructure to understand:

- **Declarative vs Imperative**: HCL (Terraform) vs Python (Pulumi)
- **Best Practices**: Different approaches to the same problem
- **Tool Evaluation**: Which tool fits different scenarios
- **Language Flexibility**: How to express infrastructure as code

Both tools produce **functionally identical infrastructure**—the only difference is how the code is written and executed.

---

## 2. Task 1 — Terraform Infrastructure

### Project Structure

```
terraform/
├── main.tf                      # Vagrant VM resource definition
├── variables.tf                 # Input variable declarations
├── outputs.tf                   # Connection info and outputs
├── terraform.tfvars             # Configuration values (gitignored)
├── terraform.tfvars.example     # Example configuration
├── .gitignore                   # Ignore state, credentials, boxes
└── README.md                    # Setup and usage guide
```

### Provider Choice: Vagrant

Terraform's Vagrant provider (`bmatcuk/vagrant`) allows declarative management of Vagrant VMs:

```hcl
terraform {
  required_providers {
    vagrant = {
      source = "bmatcuk/vagrant"
    }
  }
}

provider "vagrant" {
  # No additional configuration needed for local Vagrant
}
```

**Why Vagrant Provider:**
- Integrates Vagrant with Terraform's state management
- Allows Terraform to manage VM lifecycle (create, update, destroy)
- Maintains consistency with cloud IaC patterns
- Enables version control of VM specifications
- Tracks infrastructure state in `.tfstate` file

### Resource Configuration

The core resource definition in `main.tf`:

```hcl
resource "vagrant_vm" "devops_vm" {
  box           = var.vagrant_box           # "ubuntu/noble64"
  box_version   = var.box_version           # ">= 1.0"
  hostname      = var.vm_hostname           # "devops-vm"
  memory        = var.memory_mb             # 2048
  cpus          = var.cpu_count             # 2
  
  # Network configuration
  network = [{
    type      = "private_network"
    ip        = var.vm_private_ip           # "192.168.56.10"
    name      = "eth1"
    auto_config = true
  }]

  # Port forwarding for accessibility
  forwarded_port = [{
    guest      = 22
    host       = var.ssh_host_port          # 2222
    host_ip    = "127.0.0.1"
    auto_correct = true
  }, {
    guest      = 5000
    host       = var.app_port_host          # 5000
    host_ip    = "127.0.0.1"
    auto_correct = true
  }]
}
```

### Configuration Management

**Variables (`variables.tf`):**
- Defines all configurable parameters
- Provides descriptions and default values
- Marks sensitive variables (SSH keys)
- Allows customization without code changes

**Values (`terraform.tfvars`):**
- Contains actual configuration values
- Added to `.gitignore` for security
- Never committed to Git
- User-specific setup (paths, ports, IPs)

**Example tfvars content:**
```hcl
vagrant_box             = "ubuntu/noble64"
memory_mb              = 2048
cpu_count              = 2
vm_private_ip          = "192.168.56.10"
ssh_host_port          = 2222
app_port_host          = 5000
ssh_public_key_path    = "~/.ssh/id_rsa.pub"
```

### Terraform Workflow

```bash
# Step 1: Initialize (download providers)
terraform init

# Step 2: Validate syntax
terraform validate

# Step 3: Preview changes
terraform plan

# Step 4: Apply configuration
terraform apply

# Step 5: View outputs
terraform output
```

**Output example:**
```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

ssh_connection_local = "ssh -p 2222 vagrant@127.0.0.1"
ssh_connection_private = "ssh vagrant@192.168.56.10"
vm_private_ip = "192.168.56.10"
vm_setup_info = {
  "box" = "ubuntu/noble64"
  "cpus" = 2
  "memory" = "2048 MB"
  "name" = "devops-vm"
  "ssh_port" = 2222
  ...
}
```

### State Management

Terraform maintains a state file (`.tfstate`) that tracks:

- Created resources and their IDs
- Configuration parameters applied
- Output values
- Resource dependencies

**Important Security Note:**
```bash
# .gitignore must include:
*.tfstate*
terraform.tfvars
.terraform/
.terraform.lock.hcl
```

The state file contains sensitive information (SSH paths, network details) and credentials—**never commit to Git**.

---

## 3. Task 2 — Pulumi Infrastructure

### Project Structure

```
pulumi/
├── __main__.py              # Infrastructure code (Python)
├── requirements.txt         # Python dependencies
├── Pulumi.yaml             # Project configuration
├── Pulumi.dev.yaml         # Stack-specific config
├── .gitignore              # Ignore venv, config stacks
└── README.md               # Setup and usage guide
```

### Imperative Infrastructure with Python

Pulumi uses real programming languages instead of DSLs:

```python
import pulumi
import pulumi_vagrant as vagrant

# Configuration from stack
config = pulumi.Config()
vagrant_box = config.get("vagrant_box") or "ubuntu/noble64"
memory_mb = config.get_int("memory_mb") or 2048
cpu_count = config.get_int("cpu_count") or 2

# Create resource programmatically
vm = vagrant.Vm(
    "devops-lab04-vm",
    box=vagrant_box,
    hostname="devops-vm",
    memory=memory_mb,
    cpus=cpu_count,
    network={"type": "private_network", "ip": "192.168.56.10"},
    ports=[
        {"guest": 22, "host": 2222},
        {"guest": 5000, "host": 5000},
    ],
)

# Export outputs
pulumi.export("vm_hostname", "devops-vm")
pulumi.export("ssh_connection", "ssh -p 2222 vagrant@127.0.0.1")
```

### Key Differences from Terraform

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (domain-specific) | Python (general-purpose) |
| **Code Organization** | Multiple files (main, vars, outputs) | Single program (`__main__.py`) |
| **Logic** | Limited (count, for_each) | Full Python language |
| **Configuration** | `.tfvars` file | Stack YAML + config.get() |
| **Secrets** | Plain in state | Encrypted by default |
| **IDE Support** | HCL syntax | Full Python intellisense |
| **Testing** | External tools | Native pytest unit tests |
| **Dependencies** | Implicit from resource refs | Explicit or implicit |

### Pulumi Workflow

```bash
# Step 1: Set up Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Initialize stack
pulumi stack init dev

# Step 4: Configure settings
pulumi config set memory_mb 2048
pulumi config set cpu_count 2
# ... set other values

# Step 5: Preview changes
pulumi preview

# Step 6: Deploy
pulumi up

# Step 7: View outputs
pulumi stack output
```

### Configuration Management

**Pulumi.yaml** - Project metadata:
```yaml
name: devops-lab04-iac
runtime: python
description: Lab 04 - Infrastructure as Code
config:
  vagrant_box:
    description: "Vagrant box image"
    default: "ubuntu/noble64"
  memory_mb:
    description: "Memory in MB"
    default: "2048"
  # ... more configuration
```

**Pulumi.dev.yaml** - Stack-specific values:
```yaml
config:
  vagrant_box: ubuntu/noble64
  memory_mb: "2048"
  cpu_count: "2"
  vm_private_ip: 192.168.56.10
  ssh_host_port: "2222"
  # Stack-specific overrides
```

**Access in code:**
```python
config = pulumi.Config()
memory = config.get_int("memory_mb")  # Reads from Pulumi.<stack>.yaml
```

### Why Pulumi for Complex Infrastructure

While this lab uses simple resources, Pulumi's Python approach becomes powerful for:

```python
# Conditional logic
if memory_mb < 1024:
    pulumi.info("Warning: Low memory configuration")

# Loops for multiple resources
for i in range(3):
    vm = vagrant.Vm(f"vm-{i}", ...)

# Functions for reusability
def create_configured_vm(name, config_dict):
    return vagrant.Vm(name, **config_dict)

# Full Python standard library
import json, os, socket
```

---

## 4. Terraform vs Pulumi: Comparative Analysis

### Security Handling

**Terraform State File:**
```
# .tfstate contains:
{
  "resources": [{
    "type": "vagrant_vm",
    "instances": [{
      "attributes": {
        "private_key_path": "~/.ssh/id_rsa",  # Sensitive!
        "memory": 2048,
        "vm_net_ip": "192.168.56.10"
      }
    }]
  }]
}
```

Risk: Plain text sensitive data. Must protect `.tfstate` and gitignore it.

**Pulumi State:**
- Encrypted by default
- Stored in Pulumi Cloud (free tier) or self-hosted backend
- Never exposes secrets in plaintext
- Automatic secret rotation support

### Code Maintainability

**Terraform (Readable but Limited):**
```hcl
resource "vagrant_vm" "devops_vm" {
  box     = var.vagrant_box
  memory  = var.memory_mb
  cpus    = var.cpu_count
  # No loops, limited variable substitution
}
```

**Pulumi (Powerful but Requires Python Knowledge):**
```python
vm = vagrant.Vm(
    "devops-lab04-vm",
    box=config.get("vagrant_box"),
    memory=config.get_int("memory_mb"),
    cpus=config.get_int("cpu_count"),
    # Full Python expressiveness available
)
```

### Learning Curve

**Terraform:**
- ✅ Simpler syntax (HCL is easier initially)
- ✅ Large ecosystem with many examples
- ❌ Domain-specific language limits flexibility
- ❌ Steep curve for complex scenarios

**Pulumi:**
- ✅ Familiar if you know Python
- ✅ Full language capabilities
- ✅ IDE autocomplete and type checking
- ❌ Steeper if you don't know Python
- ❌ Smaller community

### Performance

Both tools produce identical infrastructure with similar performance:
- **VM creation**: 1-3 minutes (unchanged)
- **State tracking**: Pulumi slightly slower due to encryption
- **Deployment**: Terraform slightly faster (no Python overhead)

### Ecosystem

**Terraform:**
- 2000+ providers available
- Massive community
- Largest module registry
- Enterprise support (HashiCorp)

**Pulumi:**
- 100+ providers
- Growing community
- Type-safe packages
- Commercial support available

---

## 5. Implementation Details

### OS Image Selection

**Choice: Ubuntu 24.04 LTS (noble64)**

**Rationale:**
- Latest LTS release
- 10 years of support
- Better hardware support than older versions
- Modern tooling and packages
- Recommended for Lab 5 (Ansible)

### Network Configuration

**Private Network (192.168.56.0/24):**
- Default Vagrant private network range
- Isolated from other VMs
- Direct communication within network
- No internet access (requires NAT adapter)

**IP Assignment:**
- Host: 192.168.56.1
- Gateway: (automatic)
- Lab VM: 192.168.56.10

### Port Forwarding Strategy

| Guest Port | Host Port | Purpose | Notes |
|------------|-----------|---------|-------|
| 22 (SSH) | 2222 | Remote access | Forwarded to localhost |
| 5000 (App) | 5000 | Future app deployment | For Docker app access |

**Why localhost forwarding?** Security—VM only accessible from your machine, not network-wide.

### Storage and Synced Folders

Both tools configure synced folders:

```
Host: ./ (project directory)
Guest: /vagrant
```

**Purpose:**
- Share Terraform/Pulumi code with VM
- Easy file transfer
- Edit on host, execute in VM
- Two-way synchronization

---

## 6. Challenges & Solutions

### Challenge 1: Vagrant Box Download

**Issue:** First run downloads 500+ MB Vagrant box image

**Solution:**
```bash
# Pre-download the box (do once)
vagrant box add ubuntu/noble64

# Both Terraform and Pulumi will use the cached box
```

**Lesson:** IaC tools abstract away download complexity—handled automatically on first run.

---

### Challenge 2: SSH Key Management

**Issue:** How to enable key-based SSH access from host?

**Solution (Terraform):**
```hcl
# Provisioner adds public key to ~/.ssh/authorized_keys
provisioner "remote-exec" {
  inline = [
    "mkdir -p ~/.ssh",
    "echo '${file(var.ssh_public_key_path)}' >> ~/.ssh/authorized_keys",
  ]
}
```

**Solution (Pulumi):**
Python can read files directly and pass to provisioners, making SSH setup cleaner.

**Lesson:** Provisioning scripts work similarly across tools, but Pulumi's Python integration is more elegant.

---

### Challenge 3: Port Conflicts

**Issue:** Ports 2222 or 5000 already in use on host

**Solution:**
Change in configuration:
```hcl
# Terraform
ssh_host_port = 2223  # Or any available port
app_port_host = 5001

# Pulumi
pulumi config set ssh_host_port 2223
```

Use `auto_correct = true` to automatically increment if port busy.

**Lesson:** Infrastructure as code makes port reassignment painless—just change the variable and re-apply.

---

### Challenge 4: State File Conflicts

**Issue:** Switching between Terraform and Pulumi tried to manage same VM twice

**Solution:**
- Terraform and Pulumi use **different state systems**
- Terraform: Local `.tfstate` file
- Pulumi: Separate state (Pulumi Cloud or local)
- **Never run both simultaneously on same infrastructure**

**Process:**
1. Deploy with Terraform (creates VM)
2. Destroy with Terraform (removes VM)
3. Then deploy with Pulumi (recreates VM)
4. Destroy with Pulumi (cleans up)

**Lesson:** Each IaC tool needs exclusive ownership of its managed resources.

---

## 7. Technical Insights

### Declarative vs Imperative Trade-offs

**Terraform (Declarative):**
```hcl
resource "vagrant_vm" "devops_vm" {
  memory = 2048
  cpus   = 2
  # Terraform figures out how to make this true
}
```

**Pros:**
- Terraform idempotent (safe to run multiple times)
- Clear intent (this SHOULD be the state)
- Easier to reason about end-state

**Cons:**
- Limited expressiveness
- Complex logic requires workarounds

---

**Pulumi (Imperative):**
```python
vm = vagrant.Vm("devops-lab04-vm",
    memory=2048,
    cpus=2,
    # Code executes as written
)
```

**Pros:**
- Full language power
- Explicit control flow
- Better for complex scenarios

**Cons:**
- Your responsibility to be idempotent
- Easier to create non-reproducible configurations
- More opportunity for errors

---

### State File Purpose

Both tools maintain state for these reasons:

1. **Mapping**: Config → Real resources
   - `resource "vagrant_vm" "devops_vm"` → actual VM ID

2. **Tracking**: What exists and what doesn't
   - Detects resources deleted outside of IaC

3. **Dependencies**: Resource ordering
   - Knows to create network before VMs

4. **Outputs**: Computed values from deployed resources
   - IP addresses, connection strings, resource IDs

---

## 8. Best Practices Applied

### Security

✅ **SSH keys in .gitignore**
```
*.pem
*.key
~/.ssh/id_rsa
```

✅ **Credentials never hardcoded**
```python
# Wrong:
ssh_key = "-----BEGIN RSA PRIVATE KEY-----..."

# Right:
ssh_key = file(var.ssh_private_key_path)
```

✅ **Sensitive variables marked**
```hcl
variable "ssh_private_key_path" {
  sensitive = true
}
```

### Maintainability

✅ **Clear variable descriptions**
```hcl
variable "memory_mb" {
  description = "Memory allocated to the VM in MB"
  type        = number
  default     = 2048
}
```

✅ **Organized file structure**
- `main.tf` - Resources
- `variables.tf` - Inputs
- `outputs.tf` - Outputs
- `README.md` - Documentation

✅ **Meaningful resource names**
- `vagrant_vm.devops_vm` (not `resource1`)
- `"devops-lab04-vm"` (not `"vm"`)

### Reproducibility

✅ **Version constraints**
```hcl
required_version = ">= 1.0"
box_version      = ">= 1.0"
```

✅ **Configuration examples**
```
terraform.tfvars.example
Pulumi.yaml (with defaults)
```

✅ **Documented setup**
Multiple README files with step-by-step instructions

---

## 9. Summary

### Accomplishments

✅ Created Terraform configuration for Vagrant VM management  
✅ Created Pulumi configuration for identical infrastructure  
✅ Documented both approaches with detailed README files  
✅ Implemented 15+ variables for flexibility  
✅ Applied security best practices (gitignore, SSH keys, etc.)  
✅ Enabled output of connection information  
✅ Compared declarative vs imperative IaC philosophies  

### Key Metrics

| Metric | Value |
|--------|-------|
| Terraform files | 5 main files (main, vars, outputs, .gitignore, README) |
| Pulumi files | 5 main files (__main__.py, Pulumi.yaml, .gitignore, README) |
| Total configuration lines | ~400 (Terraform) + ~150 (Pulumi) |
| VM setup time | 2-5 minutes first run |
| Resource outputs | 8+ (IP, connection commands, setup info) |
| Configuration variables | 15+ across both tools |
| Security practices | 5+ (gitignore, sensitive marking, key management) |

### Files Delivered

- **Terraform Setup:**
  - `terraform/main.tf` - Core VM resource
  - `terraform/variables.tf` - Input variables
  - `terraform/outputs.tf` - Output definitions
  - `terraform/terraform.tfvars.example` - Configuration template
  - `terraform/.gitignore` - Security ignore rules
  - `terraform/README.md` - Complete setup guide

- **Pulumi Setup:**
  - `pulumi/__main__.py` - Python infrastructure code
  - `pulumi/requirements.txt` - Python dependencies
  - `pulumi/Pulumi.yaml` - Project configuration
  - `pulumi/Pulumi.dev.yaml` - Stack configuration
  - `pulumi/.gitignore` - Security ignore rules
  - `pulumi/README.md` - Complete setup guide

- **Documentation:**
  - `app_python/docs/LAB04.md` - This comprehensive report

### Learning Outcomes

1. **Terraform Skills:**
   - HCL syntax and structure
   - Provider configuration
   - Variables and outputs
   - State management
   - Declarative infrastructure approach

2. **Pulumi Skills:**
   - Python-based infrastructure
   - Stack configuration
   - Imperative programming for IaC
   - Configuration management in code
   - Output exports

3. **IaC Concepts:**
   - Declarative vs imperative philosophies
   - Infrastructure state tracking
   - Version control for infrastructure
   - Code organization and best practices
   - Security practices (credentials, state files)

### Conclusion

Both Terraform and Pulumi successfully manage the same local Vagrant VM infrastructure, demonstrating that the tool choice depends on team preferences, existing skills, and specific requirements rather than capabilities. Terraform's declarative approach and larger ecosystem make it ideal for most teams, while Pulumi's programming language integration excels for complex, logic-heavy infrastructure scenarios.

For Lab 5, the created VM will support Ansible configuration management, whether you choose to keep the same VM or redeploy using either Terraform or Pulumi.
