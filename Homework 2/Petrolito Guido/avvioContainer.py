import subprocess
import time

ES_CONTAINER = "es-container"
ES_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch:8.14.3"

def avvia_container():
    """Avvia il container Elasticsearch se non esiste o non è in esecuzione."""
    #print("Controllo stato del container Elasticsearch...")
    containers = subprocess.getoutput("docker ps -a --format '{{.Names}}'").splitlines()

    if ES_CONTAINER in containers:
        running = subprocess.getoutput(f"docker inspect -f '{{{{.State.Running}}}}' {ES_CONTAINER}")
        if running != "true":
            # print("Riavvio del container...")
            subprocess.run(["docker", "start", ES_CONTAINER])
    else:
        # print("Il container non esiste. Lo creo da zero...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", ES_CONTAINER,
            "-p", "9200:9200",
            "-e", "discovery.type=single-node",
            "-e", "xpack.security.enabled=false",
            ES_IMAGE
        ])
    # print("Attendo che Elasticsearch sia pronto")
    time.sleep(15)
