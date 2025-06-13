````

````python
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/app/api/endpoints/__init__.py</vscode_codeblock_uri>````

````python
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/app/models/__init__.py</vscode_codeblock_uri>````

````python
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/app/schemas/__init__.py</vscode_codeblock_uri>````

````python
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/app/services/__init__.py</vscode_codeblock_uri>````

````python
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/app/core/__init__.py</vscode_codeblock_uri>````

# Local Kubernetes cluster configuration using Terraform and Kind

````terraform
<vscode_codeblock_uri>file:///c%3A/Users/syass/OneDrive/Pulpit/PracaInz/ClusterMaster/backend/templates/local_cluster.tf.j2</vscode_codeblock_uri># Local Kubernetes cluster configuration
resource "null_resource" "local_cluster" {
  provisioner "local-exec" {
    command = <<-EOT
      # Create Kind cluster
      kind create cluster --name {{ cluster_name }} --kubeconfig {{ kubeconfig_path }}
      
      # Configure cluster with {{ node_count }} nodes
      echo "Cluster {{ cluster_name }} created with {{ node_count }} nodes"
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kind delete cluster --name {{ cluster_name }}"
  }
}

output "cluster_name" {
  value = "{{ cluster_name }}"
}

output "kubeconfig_path" {
  value = "{{ kubeconfig_path }}"
}
`````