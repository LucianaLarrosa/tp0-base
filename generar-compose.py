import sys
import yaml

def create_client(n):
    return {
        "container_name": f"client{n}",
        "image": "client:latest",
        "entrypoint": "/client",
        "environment": [
            f"CLI_ID={n}"
        ],
        "networks": [
            "testing_net"
        ],
        "depends_on": [
            "server"
        ],
        "volumes": [
            "./client/config.yaml:/config.yaml"
        ]
    }

def create_server():
    return {
        "container_name": "server",
        "image": "server:latest",
        "entrypoint": "python3 /main.py",
        "environment": [
            "PYTHONUNBUFFERED=1"
        ],
        "networks": [
            "testing_net"
        ],
        "volumes": [
            "./server/config.ini:/config.ini"
        ]
    }

def create_network():
    return {
        "testing_net": {
            "ipam": {
                "driver": "default",
                "config": [
                    {
                        "subnet": "172.25.125.0/24"
                    }
                ]
            }
        }
    }

def main():
    file_name = sys.argv[1]
    client_count = int(sys.argv[2])

    data = {
        "name": "tp0",
        "services": {
            "server": create_server(),
        },
        "networks": create_network()
    }

    for i in range(1, client_count+1):
        data["services"][f"client{i}"] = create_client(i)

    with open(file_name, "w") as f:
        yaml.dump(data, f, sort_keys=False)

main()