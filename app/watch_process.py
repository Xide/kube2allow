
import sys
import json
import logging
import subprocess
from kubernetes import client, config, watch



CAPS_MAPPING = None
with open('caps_mapping.json', 'r') as f:
    CAPS_MAPPING = json.load(f)

logging.getLogger().setLevel(logging.INFO)
config.load_incluster_config()
v1 = client.CoreV1Api()


def parse_stream(pod_name, pod_namespace, container_name, process, infos):
    if 'syscalls' not in infos.keys():
        infos['syscalls'] = set()
    while process.poll() is None:
        x = process.stderr.readline().decode('ascii')
        if ']' in x:
            x = x.split(']')[1].lstrip()
        try:
            x = x.split(' ')[1]
        except:
            continue
        if '(' not in x:
            continue
        syscall = x.split('(')[0]
        if syscall not in infos['syscalls']:
            logging.info("New syscall detected for pod {}:{} = {}".format(pod_name, pod_namespace, syscall))
            infos['syscalls'].add(syscall)
            update_cm(pod_name, pod_namespace, container_name, infos)

def write_cm(name, pod_namespace, container_name, data):
    cm_name = 'k2a-{}-{}'.format(name, container_name)
    logging.info("Writing configmap datas for pod {}:{}".format(name, pod_namespace))
    cm = client.V1ConfigMap()
    cm.data = data
    cm.metadata = client.V1ObjectMeta(
        name=cm_name,
        namespace=pod_namespace,
        labels={
            "k8s-app": "kube2allow",
        }
    )
    cm.metadata.name = cm_name
    try:
        v1.delete_namespaced_config_map(cm_name, pod_namespace)
    except:
        pass
    logging.debug('creating configmap {}'.format(cm_name))
    resp = v1.create_namespaced_config_map(pod_namespace, cm)

def update_cm(pod, pod_namespace, container_name, infos):
    caps = {}
    for sc in infos['syscalls']:
        for c in CAPS_MAPPING[sc]:
            if c not in caps.keys():
                caps[c] = set()
            caps[c].add(sc)
    for c in caps.keys():
        caps[c] = list(caps[c])
    logging.info("capabilities for pod {} : {}".format(pod, caps))
    cm_data = {
        'capabilities': json.dumps({
            'drop': ['all'],
            'add': list(
                map(
                    # Fix in order to remove CAP_ prefix, which is auto appended
                    # on cloud providers such as GKE.
                    lambda x: x.lstrip('CAP_'),
                    caps.keys()
                )
            )
        }),
        'required_by': json.dumps(caps)
    }

    write_cm(pod, pod_namespace, container_name, cm_data)


def main(pod_name, pod_namespace, container_name, pid):
    logging.info('starting to trace pod {} : {}'.format(pod_name, pid))
    p = subprocess.Popen(
        ['/usr/bin/strace', '-q', '-t', '-f', '-p', pid],
        stderr=subprocess.PIPE
    )
    parse_stream(pod_name, pod_namespace, container_name, p, {})

if __name__ == '__main__':
    POD_NAME = sys.argv[1]
    POD_NAMESPACE = sys.argv[2]
    CONTAINER_NAME = sys.argv[3]
    PID = sys.argv[4]

    main(POD_NAME, POD_NAMESPACE, CONTAINER_NAME, PID)