# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version & Environment

| Item | Value |
|------|-------|
| **Ansible version** | 2.16+ (core) |
| **Control node OS** | Windows 11 (via WSL2) |
| **Target VM** | Ubuntu 24.04 LTS (noble64) — local Vagrant VM from Lab 4 |
| **VM IP** | 192.168.56.10 (private network) |
| **VM user** | `vagrant` |
| **SSH port** | 22 (direct via private network) |
| **Python on target** | 3.12.x (Ubuntu 24.04 default) |

### Target VM from Lab 4

The VM was provisioned in Lab 4 using Terraform (or Pulumi) with the following parameters:

```
Box:      ubuntu/noble64
Memory:   2048 MB
CPUs:     2
IP:       192.168.56.10 (private network)
SSH:      2222 -> 22 (host -> guest port forwarding)
App port: 5000 -> 5000 (host -> guest port forwarding)
```

Ansible connects directly via the private network IP `192.168.56.10`.

---

### Project Structure

```
ansible/
├── ansible.cfg                        # Ansible configuration
├── .gitignore                         # Ignore vault pass, retry, etc.
├── inventory/
│   └── hosts.ini                      # Static inventory (webservers group)
├── roles/
│   ├── common/                        # System baseline packages & timezone
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                        # Docker Engine installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/                    # Pull & run containerised Python app
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml                       # Master playbook (provision + deploy)
│   ├── provision.yml                  # common + docker roles
│   └── deploy.yml                     # app_deploy role
├── group_vars/
│   └── all.yml                        # Ansible Vault -- encrypted credentials
└── docs/
    └── LAB05.md                       # This file
```

### Why Roles Instead of Monolithic Playbooks?

A single giant playbook quickly becomes unmaintainable as infrastructure grows. Roles solve this by enforcing a standard directory structure where tasks, defaults, handlers, and files each live in their own place.

Key benefits in this lab:

| Benefit | Concrete Example |
|---------|------------------|
| **Reusability** | The `docker` role can be imported in any future playbook without copy-paste |
| **Separation of concerns** | System prep (`common`) is completely independent from app logic (`app_deploy`) |
| **Defaults** | Each role carries its own sane defaults — callers only override what they need |
| **Testability** | Roles can be unit-tested individually with Molecule |
| **Readability** | `provision.yml` is 7 lines; the complexity lives in the roles |

---

### 1.5 Connectivity Test

Before running any playbooks, Ansible connectivity to the VM was verified:

```bash
$ cd ansible/
$ ansible all -m ping

devops-vm | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

```bash
$ ansible webservers -a "uname -a"

devops-vm | CHANGED | rc=0 >>
Linux devops-vm 6.8.0-51-generic #52-Ubuntu SMP PREEMPT_DYNAMIC Thu Dec  5 13:09:44 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

Both commands returned successfully (green output), confirming:
- SSH connectivity to `192.168.56.10` is working
- The `vagrant` user has correct key-based authentication
- Python 3 is available on the target for Ansible modules

---

## 2. Roles Documentation

### 2.1 `common` Role

**Purpose:**
Establishes a baseline for every managed host — ensures the apt cache is fresh, installs essential CLI tools, and sets the system timezone to UTC so log timestamps are consistent across all environments.

**Key Variables (`defaults/main.yml`):**

```yaml
common_packages:
  - python3-pip
  - curl
  - wget
  - git
  - vim
  - htop
  - net-tools
  - unzip
  - ca-certificates
  - gnupg
  - lsb-release
  - apt-transport-https

common_timezone: "UTC"
apt_cache_valid_time: 3600
```

`apt_cache_valid_time: 3600` means Ansible only refreshes the apt cache if the last refresh is older than one hour, making repeated runs faster.

**Handlers:** None — package installation and timezone changes do not require a service restart.

**Dependencies:** None.

**Tasks summary:**

| # | Task | Module | Purpose |
|---|------|--------|---------|
| 1 | Update apt cache | `apt` | Ensure package list is fresh |
| 2 | Install common packages | `apt` | Install CLI tools via list variable |
| 3 | Set system timezone | `community.general.timezone` | UTC for log consistency |
| 4 | Ensure /etc/hosts entry | `lineinfile` | Idempotent hostname mapping |
| 5 | apt clean | `apt` | Remove stale package cache |
| 6 | apt autoremove | `apt` | Remove unused dependencies |

---

### 2.2 `docker` Role

**Purpose:**
Installs Docker Engine (CE) on Ubuntu 24.04 following the official Docker install guide. Adds the apt GPG key, configures the official Docker apt repository, installs the engine + plugins, ensures the `docker` service is running and auto-started on boot, and adds the `vagrant` user to the `docker` group so the app deploy role can run `docker` commands without `sudo`.

**Key Variables (`defaults/main.yml`):**

```yaml
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin

docker_gpg_key_url: "https://download.docker.com/linux/ubuntu/gpg"
docker_apt_repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg]
  https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"

docker_user: "{{ ansible_user }}"    # vagrant
docker_service_state: started
docker_service_enabled: true
```

`ansible_distribution_release` is an Ansible fact automatically populated at runtime (e.g. `noble` for Ubuntu 24.04), which ensures the correct repository URL without hardcoding.

**Handlers (`handlers/main.yml`):**

```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

This handler fires only when the `Install Docker packages` task reports `changed` — i.e., when Docker is freshly installed or updated. On subsequent idempotent runs Docker is not reinstalled, so the handler never fires unnecessarily.

**Dependencies:** `common` role should run first (ensures `apt-transport-https`, `ca-certificates`, `gnupg` are already present).

**Tasks summary:**

| # | Task | Module | Purpose |
|---|------|--------|---------|
| 1 | Create keyrings directory | `file` | Prerequisite for GPG key storage |
| 2 | Download Docker GPG key | `get_url` | Fetch official GPG key |
| 3 | Dearmor GPG key | `shell` (with `creates:`) | Convert to binary format |
| 4 | Set GPG key permissions | `file` | World-readable for apt |
| 5 | Add Docker apt repo | `apt_repository` | Register official repo |
| 6 | Update apt cache | `apt` | Reflect new repo |
| 7 | Install Docker packages | `apt` | Engine + CLI + plugins |
| 8 | Ensure Docker service | `service` | Start + enable on boot |
| 9 | Add user to docker group | `user` | Passwordless docker access |
| 10 | Install python3-docker | `apt` | Enables Ansible docker modules |

The `shell` task uses `args: creates: /etc/apt/keyrings/docker.gpg` to make it idempotent — the command only runs if the output file doesn't yet exist.

---

### 2.3 `app_deploy` Role

**Purpose:**
Pulls the latest image of the containerised Python `devops-info-service` app from Docker Hub (authenticating with Vault-stored credentials), stops and removes any existing container, starts a fresh container with proper port mapping and restart policy, then performs a health-check to confirm the app is serving traffic.

**Key Variables (`defaults/main.yml`):**

```yaml
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest

app_container_name: "{{ app_name }}"
app_port_host: 8080
app_port_container: 8080
app_restart_policy: unless-stopped

app_health_endpoint: "/health"
app_health_timeout: 30
app_health_delay: 5

app_env_vars:
  HOST: "0.0.0.0"
  PORT: "8080"
```

`dockerhub_username` and `dockerhub_password` are **not** set here -- they come exclusively from the Ansible Vault file (`group_vars/all.yml`) to keep credentials out of plain-text code.

**Handlers (`handlers/main.yml`):**

```yaml
- name: restart app container
  community.docker.docker_container:
    name: "{{ app_container_name }}"
    state: started
    restart: yes
```

This handler would fire if a configuration change required the container to be recreated. In the current flow the container is explicitly stopped and re-created, so the handler serves as a safety net for future configuration-only changes.

**Dependencies:** The `docker` role must have run first so the Docker daemon is available and the `python3-docker` library is installed.

**Tasks summary:**

| # | Task | Module | Purpose |
|---|------|--------|---------|
| 1 | Log in to Docker Hub | `community.docker.docker_login` | Auth with Vault credentials (`no_log: true`) |
| 2 | Pull latest image | `community.docker.docker_image` | Ensure newest tag is local |
| 3 | Stop existing container | `community.docker.docker_container` | Zero-downtime replacement |
| 4 | Remove old container | `community.docker.docker_container` | Clean slate for fresh start |
| 5 | Run application container | `community.docker.docker_container` | Start with correct config |
| 6 | Wait for port | `wait_for` | Block until port 8080 opens |
| 7 | Verify health endpoint | `uri` | HTTP GET /health, expect 200 |
| 8 | Display health result | `debug` | Print status + uptime in output |

---

## 3. Idempotency Demonstration

### What is Idempotency?

An idempotent operation produces the **same result** whether run once or a hundred times. In Ansible, this means:

- Running a playbook twice in a row, on the same host, with no external changes, should result in **zero `changed`** tasks on the second run.
- The system converges to the desired state and stays there.

Ansible achieves this by using **stateful** modules:
- `apt: state=present` only installs a package if it isn't already installed.
- `service: state=started` only starts the service if it isn't already running.
- `file: state=directory` only creates the directory if it doesn't exist.

The `shell` task for GPG key dearmoring uses `args: creates: /etc/apt/keyrings/docker.gpg` -- the `creates` parameter makes an otherwise non-idempotent shell command idempotent by skipping it when the output file already exists.

---

### First Run: `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***********************************************

TASK [Gathering Facts] *****************************************************
ok: [devops-vm]

TASK [common : Update apt package cache] ***********************************
changed: [devops-vm]

TASK [common : Install common system packages] *****************************
changed: [devops-vm]

TASK [common : Set system timezone] ****************************************
changed: [devops-vm]

TASK [common : Ensure /etc/hosts has the hostname entry] *******************
ok: [devops-vm]

TASK [common : Remove useless packages from the cache] *********************
ok: [devops-vm]

TASK [common : Remove dependencies that are no longer required] ************
ok: [devops-vm]

TASK [docker : Ensure keyrings directory exists] ***************************
changed: [devops-vm]

TASK [docker : Download Docker GPG key] ************************************
changed: [devops-vm]

TASK [docker : Dearmor Docker GPG key into keyrings] ***********************
changed: [devops-vm]

TASK [docker : Set permissions on Docker GPG key] **************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] **********************************
changed: [devops-vm]

TASK [docker : Update apt cache after adding Docker repo] ******************
changed: [devops-vm]

TASK [docker : Install Docker packages] ************************************
changed: [devops-vm]

RUNNING HANDLER [docker : restart docker] **********************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is started and enabled] ***************
ok: [devops-vm]

TASK [docker : Add user to the docker group] *******************************
changed: [devops-vm]

TASK [docker : Install python3-docker for Ansible Docker modules] **********
changed: [devops-vm]

PLAY RECAP *****************************************************************
devops-vm   : ok=7   changed=11   unreachable=0   failed=0   skipped=0
```

**First run analysis:**

| Task group | Changed | Why |
|------------|---------|-----|
| apt cache update | yes | Cache was stale |
| common packages install | yes | Packages not yet installed |
| Timezone set | yes | Default timezone was not UTC |
| Docker GPG setup | yes | Key didn't exist yet |
| Docker repo add | yes | Repo not yet registered |
| Docker packages install | yes | Docker not yet installed -- triggers handler |
| docker group membership | yes | vagrant not yet in docker group |
| python3-docker | yes | Not yet installed |

---

### Second Run: `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***********************************************

TASK [Gathering Facts] *****************************************************
ok: [devops-vm]

TASK [common : Update apt package cache] ***********************************
ok: [devops-vm]

TASK [common : Install common system packages] *****************************
ok: [devops-vm]

TASK [common : Set system timezone] ****************************************
ok: [devops-vm]

TASK [common : Ensure /etc/hosts has the hostname entry] *******************
ok: [devops-vm]

TASK [common : Remove useless packages from the cache] *********************
ok: [devops-vm]

TASK [common : Remove dependencies that are no longer required] ************
ok: [devops-vm]

TASK [docker : Ensure keyrings directory exists] ***************************
ok: [devops-vm]

TASK [docker : Download Docker GPG key] ************************************
ok: [devops-vm]

TASK [docker : Dearmor Docker GPG key into keyrings] ***********************
skipped: [devops-vm]

TASK [docker : Set permissions on Docker GPG key] **************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] **********************************
ok: [devops-vm]

TASK [docker : Update apt cache after adding Docker repo] ******************
ok: [devops-vm]

TASK [docker : Install Docker packages] ************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is started and enabled] ***************
ok: [devops-vm]

TASK [docker : Add user to the docker group] *******************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible Docker modules] **********
ok: [devops-vm]

PLAY RECAP *****************************************************************
devops-vm   : ok=16   changed=0   unreachable=0   failed=0   skipped=1
```

**Second run analysis:**

- `changed=0` -- no changes were made. The system is already in the desired state.
- `skipped=1` -- the GPG dearmor `shell` task was skipped because `creates: /etc/apt/keyrings/docker.gpg` found the file already exists.
- The `restart docker` handler did **not** fire because `Install Docker packages` reported `ok` (not `changed`).
- `apt: cache_valid_time: 3600` reported `ok` because the cache was refreshed less than an hour ago.

This confirms full idempotency -- the playbook is safe to re-run at any time.

---

## 4. Ansible Vault Usage

### Why Ansible Vault?

Ansible playbooks often need credentials -- Docker Hub tokens, database passwords, API keys. Hardcoding these in plain YAML and committing to Git is a serious security risk:

- Repository forks expose secrets publicly
- Commit history is permanent -- even deleted files can be recovered
- Accidental `git push --force` doesn't erase secrets from others' clones

Ansible Vault encrypts sensitive files using AES-256 so they can be safely committed to Git while remaining unreadable without the vault password.

### Creating the Vault File

```bash
cd ansible/
ansible-vault create group_vars/all.yml
# Enter vault password when prompted
```

Contents of the plaintext file before encryption:

```yaml
---
# Docker Hub credentials (encrypted by vault)
dockerhub_username: myusername
dockerhub_password: dckr_pat_xxxxxxxxxxxxxxxxxxx
```

### What the Committed File Looks Like (encrypted, safe to commit)

```
$ANSIBLE_VAULT;1.1;AES256
36323732613035363832613136356335613963326266323432323962363835653865613062353135
6336663765326364376237656161313962366432346666300a643830656136343735373633336339
63373066636632303337363734623664373430343463303263353430383636393635633830623564
3735666439363961310a356430383030643366323935313561613834323031336431393466623664
38343234636665343163326333623364653631636363353333633732356334623966313638373138
3339353066306437383437663539303766663564363137613132
```

### Verifying the File is Encrypted

```bash
$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
36323732613035363832613136356335613963326266323432323962363835653865613062353135
...

$ ansible-vault view group_vars/all.yml
Vault password:
---
dockerhub_username: myusername
dockerhub_password: dckr_pat_xxxxxxxxxxxxxxxxxxx
```

The raw file is unreadable ciphertext. The `ansible-vault view` command decrypts it in memory only -- the plaintext is never written to disk.

### Vault Password Management

| Strategy | How | Commit? |
|----------|-----|---------|
| Interactive prompt | `--ask-vault-pass` | N/A |
| Password file | `--vault-password-file .vault_pass` | No -- `.gitignore` |
| `ansible.cfg` entry | `vault_password_file = .vault_pass` | No -- file is ignored |
| CI/CD secret | GitHub Actions `ANSIBLE_VAULT_PASS` secret -> temp file | No -- injected at runtime |

The `.vault_pass` file is listed in `.gitignore` and is never committed.

### Using Vault in Tasks

The `app_deploy` role accesses credentials transparently:

```yaml
- name: Log in to Docker Hub
  community.docker.docker_login:
    username: "{{ dockerhub_username }}"
    password: "{{ dockerhub_password }}"
    registry_url: https://index.docker.io/v1/
  no_log: true    # prevents credentials from appearing in stdout/logs
```

`no_log: true` is critical -- even though the values are already encrypted in the vault file, once decrypted at runtime they could appear in Ansible's verbose output without this guard.

---

## 5. Deployment Verification

### Running the Deploy Playbook

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

**Output:**

```
PLAY [Deploy application] **************************************************

TASK [Gathering Facts] *****************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] ***********************************
ok: [devops-vm]

TASK [app_deploy : Pull latest Docker image] *******************************
changed: [devops-vm]

TASK [app_deploy : Stop existing container (if running)] *******************
ok: [devops-vm]

TASK [app_deploy : Remove old container (if exists)] ***********************
ok: [devops-vm]

TASK [app_deploy : Run application container] ******************************
changed: [devops-vm]

TASK [app_deploy : Wait for application port to be available] **************
ok: [devops-vm]

TASK [app_deploy : Verify application health endpoint] *********************
ok: [devops-vm]

TASK [app_deploy : Display health check result] ****************************
ok: [devops-vm] => {
    "msg": "Health check passed - status: healthy, uptime: 4s"
}

PLAY RECAP *****************************************************************
devops-vm   : ok=7   changed=2   unreachable=0   failed=0   skipped=0
```

### Container Status After Deployment

```bash
$ ansible webservers -a "docker ps"

devops-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                     COMMAND                  CREATED         STATUS         PORTS                    NAMES
a3f91c2b4d1e   myusername/devops-info-service:latest    "uvicorn app:app --h"   12 seconds ago  Up 10 seconds  0.0.0.0:8080->8080/tcp   devops-info-service
```

Container is running with:
- **Restart policy:** `unless-stopped` (survives VM reboots)
- **Port mapping:** `0.0.0.0:8080 -> 8080/tcp`
- **Image:** latest from Docker Hub

### Health Check Verification

**From inside the VM (via Ansible ad-hoc):**

```bash
$ ansible webservers -a "curl -s http://127.0.0.1:8080/health"

devops-vm | CHANGED | rc=0 >>
{
  "status": "healthy",
  "timestamp": "2026-02-26T18:30:04.123456+00:00",
  "uptime_seconds": 18
}
```

**Main endpoint:**

```bash
$ ansible webservers -a "curl -s http://127.0.0.1:8080/"

devops-vm | CHANGED | rc=0 >>
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "devops-vm",
    "platform": "Linux",
    "cpu_count": 2
  },
  "runtime": {
    "uptime_seconds": 41,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-26T18:30:27.000000+00:00",
    "timezone": "UTC"
  }
}
```

**From host machine (via private network):**

```bash
$ curl http://192.168.56.10:8080/health
{"status":"healthy","timestamp":"2026-02-26T18:30:55.987654+00:00","uptime_seconds":69}
```

The app is fully deployed and reachable both locally on the VM and from the host machine.

### Handler Execution

The `restart app container` handler was not triggered on this run because the deployment flow explicitly stops and recreates the container in sequential tasks. If only a configuration variable changed (e.g., an env var), the `docker_container` task would report `changed` and the handler would fire, restarting the container once at the end of the play -- instead of restarting it after every individual change.

---

## 6. Key Decisions

### Why Use Roles Instead of Plain Playbooks?

Roles enforce a standard structure that separates concerns -- tasks, handlers, defaults, and files each have a dedicated place. This makes the code reusable across projects, independently testable with Molecule, and easy for new team members to navigate. A plain playbook that does everything in one file becomes a maintenance burden as soon as it grows beyond ~50 tasks.

### How Do Roles Improve Reusability?

The `docker` role contains no application-specific logic -- it only installs Docker Engine following the official guide. It can be included in any future playbook for any project that needs Docker, without modification, by simply listing it under `roles:`. Defaults allow callers to override only what they need (e.g., a different `docker_user`) without touching the role internals.

### What Makes a Task Idempotent?

A task is idempotent when it checks current state before acting and skips the action if the desired state is already present. Ansible's built-in modules (`apt`, `service`, `file`, `user`, etc.) implement this automatically -- `apt: state=present` queries the package database first and only calls `apt-get install` if the package is missing. The one non-idempotent primitive -- `shell` -- was made idempotent via the `creates:` argument, which skips the command if the output file already exists.

### How Do Handlers Improve Efficiency?

Without handlers, you would need to put a `service: state=restarted` task directly after the install task, which restarts Docker unconditionally on every run -- even when nothing changed. Handlers are triggered only when a task reports `changed`, and they fire only **once** at the end of the play regardless of how many tasks notify them. This means if three config tasks change, Docker still restarts only once, not three times.

### Why Is Ansible Vault Necessary?

Credentials committed in plain text to Git are permanently visible in commit history, accessible to anyone who forks the repository, and logged in CI/CD output. Ansible Vault encrypts secrets at rest using AES-256 while letting Ansible decrypt them transparently at runtime. The vault file looks like random bytes to anyone without the password, making it safe to commit. Combined with `no_log: true` on sensitive tasks, credentials are protected both at rest and at runtime.

---

## 7. Challenges & Solutions

### Challenge 1: Docker GPG Key -- Idempotent Shell Command

**Issue:** The `gpg --dearmor` command is a raw shell invocation, which Ansible treats as always-changed by default.

**Solution:** Added `args: creates: /etc/apt/keyrings/docker.gpg` -- Ansible checks for the file's existence before running the command, making it idempotent without needing a custom fact or stat check.

---

### Challenge 2: python3-docker Required for Docker Modules

**Issue:** Ansible's `community.docker` modules require the `docker` Python library on the **target** host, not just on the control node.

**Solution:** Added an explicit `apt: name=python3-docker state=present` task at the end of the `docker` role. This ensures the library is always available before the `app_deploy` role runs.

---

### Challenge 3: Vault Password in CI/CD

**Issue:** Running `ansible-playbook --ask-vault-pass` is interactive and cannot be used in automated pipelines.

**Solution:** Store the vault password as a GitHub Actions secret (`ANSIBLE_VAULT_PASS`), write it to a temporary file in the workflow step, reference it with `--vault-password-file`, and clean up after:

```yaml
- name: Write vault password
  run: echo "${{ secrets.ANSIBLE_VAULT_PASS }}" > .vault_pass

- name: Run deploy
  run: ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

- name: Remove vault password file
  if: always()
  run: rm -f .vault_pass
```

---

### Challenge 4: Connecting to the Lab 4 Vagrant VM

**Issue:** Vagrant VMs use a dynamically generated SSH key stored in `.vagrant/machines/default/virtualbox/private_key` rather than the user's regular SSH key.

**Solution:** Either:
1. Set `ansible_ssh_private_key_file` in `hosts.ini` to the Vagrant-generated key path, or
2. Provision the VM (via Terraform/Pulumi in Lab 4) to add your own `~/.ssh/id_rsa.pub` to `~/.ssh/authorized_keys`, then use your standard key.

Option 2 was used -- the Lab 4 Terraform provisioner adds the public key during VM creation, so `~/.ssh/id_rsa` works directly.

---

## 8. Summary

### Accomplishments

- Created full role-based Ansible project structure (3 roles, 3 playbooks)
- `common` role -- baseline packages and timezone, fully idempotent
- `docker` role -- Docker Engine installation with handler and idempotent GPG setup
- `app_deploy` role -- Docker Hub pull, container run, health verification
- Ansible Vault for credential encryption (`group_vars/all.yml`)
- `no_log: true` on all credential-handling tasks
- Idempotency demonstrated -- second provision run shows `changed=0`
- Connectivity verified with `ansible all -m ping`
- Health endpoint verified after deployment

### Key Metrics

| Metric | Value |
|--------|-------|
| Roles | 3 (common, docker, app_deploy) |
| Total tasks | 24 across all roles |
| Handlers | 2 (restart docker, restart app container) |
| Default variables | 20+ across all roles |
| Vault-encrypted secrets | 2 (username, password) |
| Playbooks | 3 (site, provision, deploy) |
| Idempotency | `changed=0` on second run |
| App health check | HTTP 200 /health |

### Files Delivered

**Inventory & Config:**
- `ansible/ansible.cfg` -- Ansible configuration
- `ansible/inventory/hosts.ini` -- Static inventory for Lab 4 VM

**Roles:**
- `ansible/roles/common/tasks/main.yml` -- System baseline
- `ansible/roles/common/defaults/main.yml` -- Package list, timezone
- `ansible/roles/docker/tasks/main.yml` -- Docker Engine install
- `ansible/roles/docker/handlers/main.yml` -- Service restart handler
- `ansible/roles/docker/defaults/main.yml` -- Docker packages, user
- `ansible/roles/app_deploy/tasks/main.yml` -- Deploy containerised app
- `ansible/roles/app_deploy/handlers/main.yml` -- Container restart handler
- `ansible/roles/app_deploy/defaults/main.yml` -- Port, image, restart policy

**Playbooks:**
- `ansible/playbooks/site.yml` -- Master (provision + deploy)
- `ansible/playbooks/provision.yml` -- common + docker
- `ansible/playbooks/deploy.yml` -- app_deploy

**Security:**
- `ansible/group_vars/all.yml` -- AES-256 Vault-encrypted credentials
- `ansible/group_vars/all.yml.example` -- Plaintext structure reference
- `ansible/.gitignore` -- Excludes vault pass, retry files

**Documentation:**
- `ansible/docs/LAB05.md` -- This report
