# Terraform Configuration for Lab 4

This directory contains Terraform configuration to provision a local Ubuntu VM using Vagrant and manage it with Infrastructure as Code (IaC) principles.

## Prerequisites

1. **Terraform** (1.0+)
   ```bash
   # macOS/Linux
   brew install terraform
   
   # Windows (via Chocolatey)
   choco install terraform
   
   # Or download from: https://www.terraform.io/downloads
   ```

2. **Vagrant** (2.3+)
   ```bash
   # macOS/Linux
   brew install vagrant
   
   # Windows (via Chocolatey)
   choco install vagrant
   
   # Or download from: https://www.vagrantup.com/downloads
   ```

3. **VMware or VirtualBox**
   - VMware Fusion (macOS) or VMware Workstation (Windows)
   - Or VirtualBox (free, cross-platform)

4. **SSH Key Pair**
   ```bash
   # Generate if you don't have one
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

## Setup Steps

### 1. Clone/Extract Vagrant Box (First Time Only)

```bash
# Download Ubuntu box
vagrant box add ubuntu/noble64
```

### 2. Configure Terraform Variables

```bash
# Copy example to actual config
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your settings
# Adjust paths and settings as needed
```

### 3. Initialize Terraform

```bash
terraform init
```

This downloads required provider plugins:
- vagrant provider for Terraform

**Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of bmatcuk/vagrant...
- Installing bmatcuk/vagrant v4.1.0...
Terraform has been successfully configured!
```

### 4. Validate Configuration

```bash
terraform validate
```

Checks syntax and resource definitions.

### 5. Plan Infrastructure Changes

```bash
terraform plan
```

**Output shows:**
- Resources to be created
- VM configuration (memory, CPUs, ports)
- Provisioning steps

**Expected output:**
```
Plan: 1 to add, 0 to change, 0 to destroy.
```

### 6. Apply Configuration

```bash
terraform apply
```

When prompted, confirm with `yes` to proceed.

**Process:**
1. Creates Vagrant VM
2. Allocates resources (2 GB RAM, 2 CPUs)
3. Configures network (private IP: 192.168.56.10)
4. Provisions SSH access
5. Displays output information

**Expected duration:** 2-5 minutes (first run with box download may take longer)

**Output includes:**
```
Outputs:

ssh_connection_local = "ssh -p 2222 vagrant@127.0.0.1"
ssh_connection_private = "ssh vagrant@192.168.56.10"
vm_private_ip = "192.168.56.10"
vm_setup_info = {
  ...
}
```

### 7. Verify VM Access

```bash
# Test SSH connection
ssh -p 2222 vagrant@127.0.0.1

# Or from private network
ssh vagrant@192.168.56.10
```

When prompted for password, enter: `vagrant`

### 8. Test Network Connectivity

```bash
# Check if ports are forwarded
curl http://127.0.0.1:5000  # (will fail until app is running, but proves port works)

# Access via private IP
ping 192.168.56.10
```

## File Structure

```
terraform/
├── main.tf                      # Vagrant VM resource and provisioning
├── variables.tf                 # Input variable declarations
├── outputs.tf                   # Output values and connection info
├── terraform.tfvars.example     # Example variable values
├── .gitignore                   # Git ignore patterns
├── README.md                    # This file
└── .terraform/                  # (auto-created) Provider plugins
    └── providers/
```

## Configuration Details

### VM Specifications

| Setting | Value | Purpose |
|---------|-------|---------|
| Box | ubuntu/noble64 | Ubuntu 24.04 LTS |
| Memory | 2048 MB | 2 GB RAM |
| CPUs | 2 | Dual-core |
| Private IP | 192.168.56.10 | Internal network |
| SSH Port (host) | 2222 | Forward to guest 22 |
| App Port (host) | 5000 | Forward to guest 5000 |

### Key Variables (terraform.tfvars)

- `vagrant_box`: Vagrant box image (default: ubuntu/noble64)
- `memory_mb`: RAM allocation (default: 2048 MB)
- `cpu_count`: vCPU count (default: 2)
- `vm_private_ip`: IP address on private network
- `ssh_public_key_path`: Path to your SSH public key

## Common Commands

### Destroy Infrastructure

```bash
terraform destroy
```

Removes the VM and all resources created by Terraform.

### Show Current State

```bash
terraform state show vagrant_vm.devops_vm
```

Displays detailed information about the created VM.

### Show Outputs

```bash
terraform output
```

Displays all output values (IPs, connection commands, etc.)

### Format Code

```bash
terraform fmt -recursive
```

Auto-formats Terraform files for consistency.

## Accessing the VM

### Method 1: SSH via Localhost

```bash
ssh -p 2222 vagrant@127.0.0.1
```

Use after port forwarding is active.

### Method 2: SSH via Private IP

```bash
ssh vagrant@192.168.56.10
```

Direct connection on private network (requires bridged networking).

### Method 3: Vagrant Built-in

```bash
vagrant ssh
```

Requires vagrant directory context.

## Troubleshooting

### Issue: Vagrant box not found

**Solution:**
```bash
vagrant box add ubuntu/noble64
```

### Issue: Port already in use

**Solution:**
Change `ssh_host_port` in terraform.tfvars to an available port (e.g., 2223)

### Issue: SSH key permission denied

**Solution:**
Ensure SSH key permissions are correct:
```bash
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### Issue: Terraform state lock

**Solution:**
```bash
terraform force-unlock <LOCK_ID>
```

## Security Considerations

1. **Credentials in tfvars**: Add `terraform.tfvars` to `.gitignore`
2. **SSH Keys**: Keep private keys secure (chmod 600)
3. **Default Password**: Change Vagrant default password in production
4. **Network Access**: Restrict SSH port access if exposed externally

## Next Steps

After VM creation:

1. Proceed to Task 2 (Pulumi) to recreate same infrastructure
2. Install Lab 5 (Ansible) configuration management tools
3. Deploy applications using docker containers
4. Monitor and manage with Terraform state

## References

- [Terraform Documentation](https://www.terraform.io/docs)
- [Vagrant Documentation](https://www.vagrantup.com/docs)
- [Bmatcuk Vagrant Provider](https://registry.terraform.io/providers/bmatcuk/vagrant/latest/docs)
