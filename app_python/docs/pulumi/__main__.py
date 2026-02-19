import pulumi
import pulumi_vagrant as vagrant

# Configuration
config = pulumi.Config()

# Read variables from Pulumi config
vagrant_box = config.get("vagrant_box") or "ubuntu/noble64"
memory_mb = config.get_int("memory_mb") or 2048
cpu_count = config.get_int("cpu_count") or 2
vm_hostname = config.get("vm_hostname") or "devops-vm"
vm_private_ip = config.get("vm_private_ip") or "192.168.56.10"
ssh_host_port = config.get_int("ssh_host_port") or 2222
app_port_host = config.get_int("app_port_host") or 5000
vm_user = config.get("vm_user") or "vagrant"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"

# Create Vagrant VM resource
vm = vagrant.Vm(
    "devops-lab04-vm",
    box=vagrant_box,
    hostname=vm_hostname,
    memory=memory_mb,
    cpus=cpu_count,
    # Network configuration - private network
    network={
        "type": "private_network",
        "ip": vm_private_ip,
    },
    # Port forwarding for SSH
    ports=[
        {
            "guest": 22,
            "host": ssh_host_port,
            "host_ip": "127.0.0.1",
            "auto_correct": True,
        },
        {
            "guest": 5000,
            "host": app_port_host,
            "host_ip": "127.0.0.1",
            "auto_correct": True,
        },
    ],
    # Synced folder
    synced_folders=[
        {
            "source": ".",
            "destination": "/vagrant",
            "disabled": False,
        },
    ],
    opts=pulumi.ResourceOptions(depends_on=[])
)

# VM metadata/tags
vm.add_tags({
    "name": "devops-lab04-vm",
    "environment": "lab",
    "managed_by": "Pulumi",
    "lab": "Lab04-IaC",
})

# Export outputs
pulumi.export("vm_hostname", vm_hostname)
pulumi.export("vm_private_ip", vm_private_ip)
pulumi.export("vm_memory_mb", memory_mb)
pulumi.export("vm_cpus", cpu_count)
pulumi.export("ssh_host_port", ssh_host_port)
pulumi.export("app_port_host", app_port_host)

# Export connection information
pulumi.export("ssh_connection_local", f"ssh -p {ssh_host_port} {vm_user}@127.0.0.1")
pulumi.export("ssh_connection_private", f"ssh {vm_user}@{vm_private_ip}")
pulumi.export("app_access_url", f"http://127.0.0.1:{app_port_host}")

# Export comprehensive setup info
pulumi.export("vm_setup_info", {
    "name": vm_hostname,
    "ip": vm_private_ip,
    "ssh_via_ip": f"ssh {vm_user}@{vm_private_ip}",
    "ssh_via_port": f"ssh -p {ssh_host_port} {vm_user}@127.0.0.1",
    "ssh_port": ssh_host_port,
    "app_port": app_port_host,
    "memory": f"{memory_mb} MB",
    "cpus": cpu_count,
    "box": vagrant_box,
})
