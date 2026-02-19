terraform {
  required_version = ">= 1.0"
  required_providers {
    vagrantfile = {
      source = "bmatcuk/vagrant"
      # Version constraint: allows compatible versions
    }
  }
}

provider "vagrant" {
  # No additional configuration needed for local Vagrant
}

# Create an Ubuntu VM with Vagrant
resource "vagrant_vm" "devops_vm" {
  box           = var.vagrant_box
  box_version   = var.box_version
  hostname      = var.vm_hostname
  memory        = var.memory_mb
  cpus          = var.cpu_count
  
  # Network configuration
  network = [{
    type      = "private_network"
    ip        = var.vm_private_ip
    name      = "eth1"
    auto_config = true
  }]

  # Forwarded ports for accessibility
  # Port 22 (SSH) - usually available on host
  # Port 5000 - for future application deployment
  forwarded_port = [{
    guest      = 22
    host       = var.ssh_host_port
    host_ip    = "127.0.0.1"
    auto_correct = true
  }, {
    guest      = 5000
    host       = var.app_port_host
    host_ip    = "127.0.0.1"
    auto_correct = true
  }]

  # Synced folder - share code between host and VM
  synced_folder {
    source      = var.synced_folder_source
    destination = var.synced_folder_dest
    disabled    = false
  }

  # Provisioning - install and configure SSH
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -qq",
      "sudo apt-get install -y openssh-server openssh-client",
      "sudo systemctl enable ssh",
      "sudo systemctl start ssh",
      "mkdir -p ~/.ssh",
      "chmod 700 ~/.ssh"
    ]

    connection {
      type        = "ssh"
      user        = var.vm_user
      private_key = var.ssh_private_key_path != "" ? file(var.ssh_private_key_path) : null
      host        = self.machine_name
      timeout     = "2m"
    }
  }

  # Add SSH public key to .ssh/authorized_keys
  provisioner "remote-exec" {
    inline = [
      "echo '${file(var.ssh_public_key_path)}' >> ~/.ssh/authorized_keys",
      "chmod 600 ~/.ssh/authorized_keys"
    ]

    connection {
      type        = "ssh"
      user        = var.vm_user
      password    = var.vagrant_default_password
      host        = self.machine_name
      timeout     = "2m"
    }
  }

  # Assign static IP address
  provisioner "remote-exec" {
    inline = [
      "echo 'auto eth1' | sudo tee -a /etc/network/interfaces",
      "echo 'iface eth1 inet static' | sudo tee -a /etc/network/interfaces",
      "echo '  address ${var.vm_private_ip}' | sudo tee -a /etc/network/interfaces",
      "echo '  netmask ${var.vm_netmask}' | sudo tee -a /etc/network/interfaces",
    ]

    connection {
      type        = "ssh"
      user        = var.vm_user
      private_key = file(var.ssh_private_key_path)
      host        = self.machine_name
      timeout     = "2m"
    }
  }

  tags = {
    Name        = var.vm_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Lab         = "Lab04-IaC"
  }
}
