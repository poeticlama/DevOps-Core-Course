variable "vagrant_box" {
  description = "Vagrant box image to use"
  type        = string
  default     = "ubuntu/noble64"  # Ubuntu 24.04 LTS
}

variable "box_version" {
  description = "Version of the Vagrant box"
  type        = string
  default     = ">= 1.0"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "devops-lab04-vm"
}

variable "vm_hostname" {
  description = "Hostname inside the VM"
  type        = string
  default     = "devops-vm"
}

variable "memory_mb" {
  description = "Memory allocated to the VM in MB"
  type        = number
  default     = 2048  # 2 GB
}

variable "cpu_count" {
  description = "Number of vCPUs"
  type        = number
  default     = 2
}

variable "vm_private_ip" {
  description = "Private IP address for the VM"
  type        = string
  default     = "192.168.56.10"
}

variable "vm_netmask" {
  description = "Netmask for the private network"
  type        = string
  default     = "255.255.255.0"
}

variable "ssh_host_port" {
  description = "Host port to forward SSH (guest port 22)"
  type        = number
  default     = 2222
}

variable "app_port_host" {
  description = "Host port to forward app port (guest port 5000)"
  type        = number
  default     = 5000
}

variable "vm_user" {
  description = "Default user in the Vagrant box"
  type        = string
  default     = "vagrant"
  sensitive   = false
}

variable "vagrant_default_password" {
  description = "Default password for Vagrant user"
  type        = string
  default     = "vagrant"
  sensitive   = true
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key to add to VM"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key for provisioning"
  type        = string
  default     = "~/.ssh/id_rsa"
  sensitive   = true
}

variable "synced_folder_source" {
  description = "Source folder on host machine"
  type        = string
  default     = "."
}

variable "synced_folder_dest" {
  description = "Destination folder in VM"
  type        = string
  default     = "/vagrant"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "lab"
}
