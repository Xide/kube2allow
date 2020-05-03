import os
import sys
import json
import time
import select
import signal
import logging
import subprocess
from kubernetes import client, config, watch

logging.getLogger().setLevel(logging.INFO)
current_subprocs = set()
config.load_incluster_config()
v1 = client.CoreV1Api()

def signal_handler(sig, frame):
    logging.error('You pressed Ctrl+C!')
    for p in current_subprocs:
        pgid = os.getpgid(p.pid)
        logging.info('Killing subprocess group {}'.format(pgid))
        os.killpg(pgid, signal.SIGKILL) 
    time.sleep(10)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def prepare_strace(pod_name, pod_namespace, container_name, pid):
    logging.info('starting to trace pod {} : {}'.format(pod_name, pid))
    p = subprocess.Popen([
            '/usr/local/bin/python', 
            '/watch_process.py', 
            pod_name, 
            pod_namespace, 
            container_name, 
            str(pid)
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    current_subprocs.add(p)

def filter_containers(pods_it, watched):
    NODE_NAME = os.environ['NODE_NAME']
    for i in pods_it:
        if i.spec.node_name != NODE_NAME:
            # Skip watch for pods that are not on this node
            continue
        if 'k8s-app' in i.metadata.labels.keys() and i.metadata.labels['k8s-app'] == 'kube2allow':
            # Skip self monitoring
            continue
        if i.status.container_statuses is None:
            # Containers not ready
            continue
        for x in i.status.container_statuses:
            cid = x.container_id
            if not cid or 'docker://' not in cid:
                logging.warning('Not a docker container : {}. Skipping.'.format(cid))
                continue
            cid = cid[9:]
            cname = x.name if x.name is not None else 'container'
            if cid in watched:
                continue
            for dir_name in os.listdir('/proc'):
                try:
                    pid = int(dir_name)
                except:
                    pass
                else:
                    pcid = None
                    try:
                        with open('/proc/{}/cmdline'.format(pid), 'r') as proc_command:
                            if cid in proc_command.read():
                                watched.add(cid)
                                pcid = cid
                        if pcid is not None:
                            prepare_strace(
                                i.metadata.name, 
                                i.metadata.namespace, 
                                cname, 
                                pid
                            )
                    except:
                        pass
    return watched

def stream_watcher():
    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces, watch=True):
        yield event['object']

if __name__ == '__main__':
    watched = set()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    watched = filter_containers(ret.items, watched)
    filter_containers(stream_watcher(), watched)
