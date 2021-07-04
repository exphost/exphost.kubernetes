import time
import json
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

def test_metallb_service_ip(host):
    kubectl_cmd(host, "create service loadbalancer test-service --tcp=80:80")
    time.sleep(2)
    service_ip = kubectl_cmd(host, "get service test-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}'")['stdout']
    kubectl_cmd(host, "delete service test-service")
    assert service_ip.startswith("127.5.0")

def test_metallb_service_ip(host):
    service_ip = kubectl_cmd(host, "-n monitoring get services kube-prometheus-prometheus -o jsonpath='{.spec.clusterIP}'")['stdout']
    output = json.loads(host.check_output('curl -s "{service_ip}:9090/api/v1/query?query=up"'.format(service_ip=service_ip)))
    for i in filter(lambda x: x['metric']['service'] in ["kube-prometheus-kube-controller-manager", "kube-prometheus-node-exporter", "kube-prometheus-kube-scheduler"], output['data']['result']):
        assert i['value'][1] == '1', "%s target is down"%i['metric']['service']
