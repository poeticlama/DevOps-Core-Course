output "vm_id" {
  description = "ID of the created Vagrant VM"
  value       = vagrant_vm.devops_vm.id
}

output "vm_hostname" {
  description = "Hostname of the virtual machine"
  value       = vagrant_vm.devops_vm.hostname
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = var.vm_private_ip
}

output "vm_memory" {
  description = "Memory allocated to the VM"
  value       = "${var.memory_mb} MB"
}

output "vm_cpus" {
  description = "Number of CPUs"
  value       = var.cpu_count
}

output "ssh_connection_local" {
  description = "SSH connection command via localhost (from host machine)"
  value       = "ssh -p ${var.ssh_host_port} ${var.vm_user}@127.0.0.1"
}

output "ssh_connection_private" {
  description = "SSH connection command via private IP (from host machine)"
  value       = "ssh ${var.vm_user}@${var.vm_private_ip}"
}

output "app_access_url" {
  description = "URL to access application running on port 5000"
  value       = "http://127.0.0.1:${var.app_port_host}"
}

output "synced_folder_info" {
  description = "Information about synced folder"
  value = {
    host_path = var.synced_folder_source
    vm_path   = var.synced_folder_dest
    note      = "Changes in host folder will be reflected in VM"
  }
}

output "vm_setup_info" {
  description = "Complete VM setup information"
  value = {
    name        = vagrant_vm.devops_vm.hostname
    ip          = var.vm_private_ip
    ssh_via_ip  = "ssh ${var.vm_user}@${var.vm_private_ip}"
    ssh_via_port = "ssh -p ${var.ssh_host_port} ${var.vm_user}@127.0.0.1"
    ssh_port    = var.ssh_host_port
    app_port    = var.app_port_host
    memory      = "${var.memory_mb} MB"
    cpus        = var.cpu_count
    box         = var.vagrant_box
  }
}
