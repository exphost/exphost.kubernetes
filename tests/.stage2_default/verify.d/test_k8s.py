kubectl = {}
def kubectl_cmd(host, cmd):
    if not kubectl.get((host,cmd)):
        kubectl[(host,cmd)] = host.ansible(
          "command",
          "/var/lib/rancher/rke2/bin/kubectl --kubeconfig /etc/rancher/rke2/rke2.yaml {command}".format(command=cmd),
          become=True,
          become_user="root",
          check=False,
        )
    return kubectl[(host,cmd)]
def test_nodes_count(host):
    assert len(kubectl_cmd(host, "get nodes")['stdout_lines']) == 5

def test_nodes_ready(host):
    assert "NotReady" not in kubectl_cmd(host, "get nodes")['stdout']

def test_node_exporter_has_metrics(host):
    assert "node_cpu_guest_seconds_total" in host.check_output("curl localhost:9100/metrics")
