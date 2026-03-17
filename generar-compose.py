'''
Este archivo se encarga de generar un archivo docker-compose-dev.yaml 
a partir de los parámetros recibidos del archivo bash (nombre y cantidad de clientes).
'''

import sys
import yaml

def main():
    file_name = sys.argv[1]
    client_count = int(sys.argv[2])

    data = {
        "name": "tp0",
        "services": {}
    }

    data["services"]["server"] = {
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

    for i in range(1, client_count+1):
        data["services"][f"client{i}"] = {
            "container_name": f"client{i}",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": [
                f"CLI_ID={i}"
                "NOMBRE=Santiago Lionel"
                "APELLIDO=Lorca"
                "DOCUMENTO=30904465"
                "NACIMIENTO=1999-03-17"
                "NUMERO=7574"
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

    data["networks"] = {
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

    with open(file_name, "w") as f:
        yaml.dump(data, f, sort_keys=False)

main()