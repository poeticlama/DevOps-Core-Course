# Ansible Configuration - Lab 6: Advanced Ansible & CI/CD

This directory contains all Ansible automation code for Lab 6, including refactored roles with blocks/tags, Docker Compose deployment, wipe logic, and CI/CD integration.

## Quick Start

### Prerequisites
- Ansible 2.16+
- Docker and Docker Compose installed on target VM
- Python 3.12+
- SSH access to target servers

### Installation
```bash
# Install Ansible
pip install ansible

# Install required collections
ansible-galaxy collection install community.docker community.general

# Decrypt vault (if needed)
ansible-vault view group_vars/all.yml --vault-password-file ~/.vault_pass
```

### Basic Commands

**Provision servers (install Docker and common packages):**
```bash
ansible-playbook playbooks/provision.yml \
  -i inventory/hosts.ini \
  --vault-password-file ~/.vault_pass
```

**Deploy application with Docker Compose:**
```bash
ansible-playbook playbooks/deploy.yml \
  -i inventory/hosts.ini \
  --vault-password-file ~/.vault_pass
```

**List all available tags:**
```bash
ansible-playbook playbooks/provision.yml --list-tags
```

**Run only Docker installation:**
```bash
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

**Skip package installation:**
```bash
ansible-playbook playbooks/provision.yml --skip-tags "packages"
```

## Directory Structure

```
ansible/
├── ansible.cfg                    # Ansible configuration
├── .gitignore                     # Ignore secrets and temp files
├── inventory/
│   └── hosts.ini                  # Inventory: servers and groups
├── group_vars/
│   ├── all.yml                    # Encrypted vault with credentials
│   └── all.yml.example            # Example (unencrypted)
├── roles/
│   ├── common/                    # Common system setup
│   │   ├── tasks/main.yml         # Refactored with blocks/tags
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   │
│   ├── docker/                    # Docker Engine installation
│   │   ├── tasks/main.yml         # Refactored with rescue/always
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   │
│   └── web_app/                   # Application deployment (NEW)
│       ├── tasks/
│       │   ├── main.yml           # Docker Compose deployment
│       │   └── wipe.yml           # Safe cleanup logic
│       ├── templates/
│       │   └── docker-compose.yml.j2  # Jinja2 template
│       ├── meta/main.yml          # Role dependencies
│       ├── handlers/main.yml
│       └── defaults/main.yml
│
├── playbooks/
│   ├── provision.yml              # System provisioning
│   ├── deploy.yml                 # Application deployment
│   └── site.yml                   # Complete site playbook
│
└── docs/
    └── LAB06.md                   # Comprehensive lab report
```

## Lab 6 Tasks

### Task 1: Blocks & Tags (2 pts)

Both `common` and `docker` roles refactored with:
- **Blocks** for logical task grouping
- **Rescue** sections for error handling
- **Always** sections for cleanup/logging
- **Tags** for selective execution

**Tags available:**
- `packages` - Package installation
- `docker_install` - Docker packages only
- `docker_config` - Docker configuration only
- `docker` - All Docker tasks
- `common` - All common tasks

**Testing:**
```bash
# Run only packages installation
ansible-playbook playbooks/provision.yml --tags "packages"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Run only Docker installation and skip configuration
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

### Task 2: Docker Compose Migration (3 pts)

- Renamed `app_deploy` role to `web_app`
- Created Docker Compose template (`docker-compose.yml.j2`)
- Added role dependencies (docker → web_app)
- Replaced individual `docker run` with declarative Compose deployment
- Healthcheck built into compose template

**Testing:**
```bash
# First deployment
ansible-playbook playbooks/deploy.yml
# Output: Multiple "changed" tasks

# Second deployment (idempotent)
ansible-playbook playbooks/deploy.yml
# Output: All "ok" (no changes)

# Verify application
curl http://192.168.56.10:8000/health
```

### Task 3: Wipe Logic (2.5 pts)

Safe cleanup with **double-gating** protection:
1. **Variable gate:** `web_app_wipe=true` (conscious decision)
2. **Tag gate:** `--tags web_app_wipe` (explicit command)

**Wipe scenarios:**

```bash
# Normal deployment (safe, no wipe)
ansible-playbook playbooks/deploy.yml

# Wipe only (remove app)
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Clean reinstall (wipe → deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# Safety check (wipe blocked without variable)
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# Result: Wipe skipped, app still running
```

### Task 4: CI/CD Integration (2.5 pts)

GitHub Actions workflow (`.github/workflows/ansible-deploy.yml`):

1. **Lint Job** - Syntax checking with ansible-lint
2. **Deploy Job** - Runs playbook on self-hosted runner
3. **Verify Job** - Health check curl requests

**Setup required:**
1. Self-hosted runner on target VM
2. GitHub Secrets:
   - `ANSIBLE_VAULT_PASSWORD` - Vault decryption
   - `SSH_PRIVATE_KEY` - SSH authentication

**Trigger:**
- Push to master/main branch with ansible/ changes

## Configuration

### Inventory Setup

Edit `inventory/hosts.ini`:
```ini
[webservers]
devops-vm ansible_host=192.168.56.10 ansible_user=vagrant
```

Test with:
```bash
ansible all -i inventory/hosts.ini -m ping
```

### Vault Setup

**Initialize vault:**
```bash
# First time - create password
ansible-vault create group_vars/all.yml
```

**Edit existing vault:**
```bash
ansible-vault edit group_vars/all.yml
```

**Required variables in vault:**
```yaml
dockerhub_username: your_username
dockerhub_password: your_password
```

**Provide password when running:**
```bash
# Option 1: Interactive prompt
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Option 2: Password file
echo "your-password" > ~/.vault_pass
ansible-playbook playbooks/deploy.yml --vault-password-file ~/.vault_pass

# Option 3: Environment variable (CI/CD)
export ANSIBLE_VAULT_PASSWORD="your-password"
ansible-playbook playbooks/deploy.yml
```

### Ansible Configuration

`ansible.cfg` includes:
```ini
[defaults]
inventory = inventory/hosts.ini
become_method = sudo
host_key_checking = False
```

## Docker Compose Template Variables

Template uses variables from role defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `docker_compose_version` | 3.8 | Compose API version |
| `app_name` | devops-info-service | Service name |
| `docker_image` | username/devops-info-service | Docker Hub image |
| `docker_tag` | latest | Image version |
| `app_port_host` | 8000 | Host port |
| `app_port_container` | 8000 | Container port |
| `compose_project_dir` | /opt/devops-info-service | Project directory |

**Override defaults:**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "app_port_host=9000 app_port_container=9000"
```

## Role Dependencies

The `web_app` role automatically includes `docker` role:
- Ensures Docker installed before deploying app
- Execution order: docker role → web_app role
- Prevents deployment on systems without Docker

## Troubleshooting

### Vault Password Issues
```bash
# Test vault access
ansible-vault view group_vars/all.yml --vault-password-file ~/.vault_pass

# Re-encrypt if changed
ansible-vault rekey group_vars/all.yml
```

### Connection Issues
```bash
# Test SSH connectivity
ansible all -i inventory/hosts.ini -m ping

# Debug connection
ansible all -i inventory/hosts.ini -vvv -m ping
```

### Docker Compose Issues
```bash
# Check compose file validity
cd /opt/devops-info-service
docker-compose config

# View container logs
docker-compose logs devops-info-service

# Restart service
docker-compose restart
```

### Application Not Responding
```bash
# Check container status
docker ps | grep devops-info-service

# View application logs
docker logs devops-info-service

# Test health endpoint
curl -v http://192.168.56.10:8000/health
```

## Best Practices Applied

✅ **Error Handling**
- Rescue blocks for expected failures
- Always blocks for guaranteed cleanup
- Comprehensive logging to temp files

✅ **Idempotency**
- Tasks can run repeatedly without side effects
- Safe for automated CI/CD execution
- Detects unnecessary changes

✅ **Security**
- Sensitive data in Vault (encrypted)
- Least privilege principle
- Secrets not logged in output

✅ **Maintainability**
- Clear variable names and documentation
- Logical task grouping with blocks
- Comments explaining complex logic

✅ **Scalability**
- Role reusability (web_app for any app)
- Jinja2 templating for flexibility
- Proper dependency management

## Lab 6 Report

Comprehensive documentation in `docs/LAB06.md`:
- Detailed explanation of blocks and tags
- Docker Compose migration rationale
- Wipe logic safety mechanisms
- CI/CD integration architecture
- Testing procedures and validation
- Research question answers
- Design decision justification

## Next Steps (Bonus)

### Bonus 1: Multi-App Deployment (1.5 pts)
- Deploy multiple applications simultaneously
- Different ports, volumes, configurations
- Single playbook for all apps
- Independent update and wipe per app

### Bonus 2: GitHub Actions Matrix (1 pt)
- Parallel deployment of multiple apps
- Environment-specific configuration
- Conditional workflows per app

## Files Committed (Lab 6)

```
✓ ansible/roles/common/tasks/main.yml           # Refactored
✓ ansible/roles/docker/tasks/main.yml           # Refactored
✓ ansible/roles/web_app/                        # NEW role
✓ ansible/roles/web_app/meta/main.yml           # Dependencies
✓ ansible/roles/web_app/templates/docker-compose.yml.j2
✓ ansible/roles/web_app/tasks/wipe.yml
✓ ansible/roles/web_app/tasks/main.yml          # Updated
✓ ansible/roles/web_app/defaults/main.yml       # Updated
✓ ansible/playbooks/deploy.yml                  # Updated
✓ .github/workflows/ansible-deploy.yml          # NEW CI/CD
✓ ansible/docs/LAB06.md                         # NEW Report
```

**NOT committed (secrets):**
- `ansible/group_vars/all.yml` (use Vault, not plain text)
- `.vault_pass` (never commit passwords)
- Private SSH keys
- Docker credentials

## Resources

- [Ansible Official Documentation](https://docs.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [Docker Compose Module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_v2_module.html)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)

---

**Lab 6 Status:** ✅ Complete  
**All Tasks Implemented:** ✓  
**Ready for CI/CD:** ✓  
**Production-Ready:** ✓

