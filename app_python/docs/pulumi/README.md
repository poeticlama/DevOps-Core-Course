# Pulumi Configuration for Lab 4

This directory contains Pulumi infrastructure code to provision and manage a local Ubuntu VM using Vagrant with Python. This demonstrates the imperative approach to Infrastructure as Code.

## Prerequisites

1. **Pulumi CLI** (3.x+)
   ```bash
   # macOS/Linux
   brew install pulumi
   
   # Windows (via Chocolatey)
   choco install pulumi
   
   # Or download from: https://www.pulumi.com/docs/install/
   ```

2. **Python** (3.8+)
   ```bash
   # Check version
   python --version
   ```

3. **Vagrant** (2.3+)
   ```bash
   # macOS/Linux
   brew install vagrant
   
   # Windows
   choco install vagrant
   ```

4. **VMware or VirtualBox**
   - VMware Fusion (macOS) or VMware Workstation (Windows)
   - Or VirtualBox (free, cross-platform)

5. **SSH Key Pair**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

## Setup Steps

### 1. Download Vagrant Box (First Time Only)

```bash
vagrant box add ubuntu/noble64
```

### 2. Create Python Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Installs:
- pulumi (core framework)
- pulumi-vagrant (provider for Vagrant)

### 4. Initialize Pulumi Stack

```bash
# This creates a new stack (first time only)
pulumi stack init dev

# Or select existing stack
pulumi stack select dev
```

### 5. Configure Stack Settings

```bash
# Set configuration values
pulumi config set vagrant_box ubuntu/noble64
pulumi config set memory_mb 2048
pulumi config set cpu_count 2
pulumi config set vm_hostname devops-vm
pulumi config set vm_private_ip 192.168.56.10
pulumi config set ssh_host_port 2222
pulumi config set app_port_host 5000
pulumi config set vm_user vagrant
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
```

### 6. Preview Changes

```bash
pulumi preview
```

Shows what will be created:
- VM resource name
- Configuration properties
- Network ports
- Output values

**Expected output:**
```
Previewing update (dev)

View Live: https://app.pulumi.com/...

     Type                         Name
 +   pulumi:pulumi:Stack          devops-lab04-iac-dev
 +   └─  vagrant:vm:Vm           devops-lab04-vm

Resources:
    + 1 to create

Operations:
    + 1 new
```

### 7. Deploy Infrastructure

```bash
pulumi up
```

When prompted, confirm with `yes` to create resources.

**Process:**
1. Creates Vagrant VM
2. Allocates memory and CPUs
3. Configures networking
4. Sets up port forwarding
5. Exports outputs

**Expected duration:** 1-3 minutes

**Output includes:**
```
Outputs:
    app_access_url: "http://127.0.0.1:5000"
    ssh_connection_local: "ssh -p 2222 vagrant@127.0.0.1"
    ssh_connection_private: "ssh vagrant@192.168.56.10"
    ssh_host_port: 2222
    vm_cpus: 2
    ...
```

### 8. Test VM Access

```bash
# Get outputs
pulumi stack output

# SSH into VM
ssh -p 2222 vagrant@127.0.0.1

# When prompted for password
vagrant  # (default Vagrant password)
```

### 9. Verify Functionality

```bash
# Test SSH connectivity
ssh -p 2222 vagrant@127.0.0.1 "uname -a"

# Check VM IP
ssh vagrant@192.168.56.10 "ip addr"

# Test port forwarding
curl http://127.0.0.1:5000  # (will fail until app is running)
```

## File Structure

```
pulumi/
├── __main__.py              # Infrastructure code (Python)
├── requirements.txt         # Python dependencies
├── Pulumi.yaml             # Project configuration
├── Pulumi.dev.yaml         # Development stack config
├── .gitignore              # Git ignore patterns
├── README.md               # This file
└── venv/                   # (auto-created) Virtual environment
```

## Infrastructure Code Explanation

### Resource Declaration

```python
vm = vagrant.Vm(
    "devops-lab04-vm",          # Logical resource name
    box=vagrant_box,             # Vagrant box image
    hostname=vm_hostname,        # VM hostname
    memory=memory_mb,            # RAM allocation
    cpus=cpu_count,              # vCPU count
    network={...},               # Private network
    ports=[...],                 # Port forwarding
    synced_folders=[...],        # Shared folders
)
```

### Configuration via Code

Unlike Terraform's declarative approach, Pulumi uses Python:

```python
# Read from stack configuration
config = pulumi.Config()
memory_mb = config.get_int("memory_mb") or 2048

# Use in resource definition
memory=memory_mb,

# Conditional logic is native Python
if memory_mb < 1024:
    pulumi.warn("Memory less than 1 GB, may cause issues")
```

### Output Export

```python
# Export computed values
pulumi.export("vm_private_ip", vm_private_ip)
pulumi.export("ssh_connection_local", 
    f"ssh -p {ssh_host_port} {vm_user}@127.0.0.1"
)
```

## Common Commands

### View Stack Information

```bash
pulumi stack
```

Shows:
- Stack name
- Region/location
- Creation date
- Resource counts

### List Resources

```bash
pulumi stack --show-urns
```

Shows all created resources and their unique identifiers.

### View Outputs

```bash
pulumi stack output
# or
pulumi stack output <output_name>
```

### Get Specific Output

```bash
# Get SSH connection command
pulumi stack output ssh_connection_local

# Get VM IP
pulumi stack output vm_private_ip
```

### Update Configuration

```bash
pulumi config set memory_mb 4096
pulumi up
```

Re-deploys with new configuration.

### Destroy Infrastructure

```bash
pulumi destroy
```

Removes the VM and all resources.

When prompted, confirm with `yes`.

### Clear Stack

```bash
# Remove stack from Pulumi
pulumi stack rm dev
```

## Configuration Settings

All settings defined in `Pulumi.yaml` and `Pulumi.dev.yaml`:

| Setting | Default | Purpose |
|---------|---------|---------|
| vagrant_box | ubuntu/noble64 | Ubuntu 24.04 LTS |
| memory_mb | 2048 | RAM allocation |
| cpu_count | 2 | vCPU count |
| vm_hostname | devops-vm | VM hostname |
| vm_private_ip | 192.168.56.10 | Private network IP |
| ssh_host_port | 2222 | SSH port forwarding |
| app_port_host | 5000 | App port forwarding |
| vm_user | vagrant | Default user |
| ssh_public_key_path | ~/.ssh/id_rsa.pub | SSH key location |

## Comparison with Terraform

### Similarities

Both create identical infrastructure:
- Same VM specifications
- Same networking configuration
- Same port forwarding
- Same outputs

### Differences

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python (imperative) |
| **Code structure** | Separate files (main, variables, outputs) | Single Python program |
| **Logic** | Limited (count, for_each) | Full Python language |
| **Testing** | External | Native unit tests |
| **Configuration** | tfvars file | Pulumi stack YAML |
| **Secrets** | State file | Pulumi encrypted |
| **Learning curve** | Moderate | Easy (if you know Python) |

### When to Use Each

**Use Terraform when:**
- Working with multiple machines/teams
- Infrastructure mostly declarative
- Need large ecosystem of modules
- Language-agnostic approach preferred

**Use Pulumi when:**
- Complex logic required
- Team knows programming languages
- Want IDE autocomplete/type checking
- Need to unit test infrastructure

## Accessing the VM

### Method 1: SSH via Localhost

```bash
pulumi stack output ssh_connection_local | xargs ssh
```

### Method 2: SSH via Private IP

```bash
pulumi stack output ssh_connection_private | xargs ssh
```

### Method 3: Manual SSH

```bash
ssh -p 2222 vagrant@127.0.0.1
```

## Troubleshooting

### Issue: Pulumi stack not found

**Solution:**
```bash
pulumi stack init dev
pulumi stack select dev
```

### Issue: Virtual environment not activated

**Solution:**
```bash
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Issue: Provider not installed

**Solution:**
```bash
pulumi plugin install resource vagrant 1.0.0
```

Or reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: Vagrant box not found

**Solution:**
```bash
vagrant box add ubuntu/noble64
```

### Issue: SSH connection timeout

**Solution:**
- Ensure Vagrant VM is running: `vagrant status`
- Check SSH port: `pulumi stack output ssh_host_port`
- Verify key permissions: `chmod 600 ~/.ssh/id_rsa`

## Best Practices

1. **Use configuration files** instead of hardcoding values
   ```python
   config = pulumi.Config()
   memory = config.get_int("memory_mb")  # ✓
   # vs
   memory = 2048  # ✗
   ```

2. **Protect sensitive data**
   ```bash
   pulumi config set --secret db_password "secret123"
   ```

3. **Use resource dependencies**
   ```python
   opt_args = pulumi.ResourceOptions(depends_on=[network])
   ```

4. **Add descriptive outputs**
   ```python
   pulumi.export("connection_info", {
       "host": vm_ip,
       "port": ssh_port,
       "user": vm_user,
   })
   ```

5. **Validate configuration**
   ```python
   if memory_mb < 1024:
       raise ValueError("Minimum 1 GB memory required")
   ```

## Next Steps

After VM creation:

1. Proceed to Lab 5 (Ansible) for configuration management
2. Deploy applications using Docker containers
3. Set up monitoring and logging
4. Explore Pulumi automation API for advanced orchestration

## References

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi Python SDK](https://www.pulumi.com/docs/languages-sdks/python/)
- [Pulumi Vagrant Provider](https://www.pulumi.com/registry/packages/vagrant/)
- [Vagrant Documentation](https://www.vagrantup.com/docs/)
