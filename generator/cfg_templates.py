COMPOSE_VALIDATOR_TEMPLATE = {
    "build": {"context": "config/goquorum"},
    "environment": [
        "GOQUORUM_CONS_ALGO=${GOQUORUM_CONS_ALGO}",
        "BLOCK_PERIOD=${BLOCK_PERIOD}",
        "GOQUORUM_GENESIS_MODE=standard",
    ],
    "expose": [30303, 8545, 9545],
    "healthcheck": {
        "interval": "3s",
        "retries": 10,
        "start_period": "5s",
        "test": [
            "CMD",
            "wget",
            "--spider",
            "--proxy",
            "off",
            "http://localhost:8545",
        ],
        "timeout": "3s",
    },
    "networks": {"gq-net": {"ipv4_address": ""}},
    "ports": ["21001:8545/tcp", 30303, 9545],
    "restart": "on-failure",
    "volumes": [
        "",
        "./logs/quorum:/var/log/quorum/",
        "./config/permissions:/permissions",
    ],
    "deploy": {
        "resources": {
            "limits": {"cpus": "2.00", "memory": "4G"},
            "reservations": {"memory": "4G"},
        }
    },
}

PUMBA_DELAY_TEMPLATE = {'command': '--log-level=debug netem --tc-image="gaiadocker/iproute2" --duration=1h delay --time={time} --jitter={jitter} "re2:validator."',
                              'container_name': 'pumba_delay',
                              'depends_on': {},
                              'image': 'gaiaadm/pumba',
                              'volumes': ['/var/run/docker.sock:/var/run/docker.sock']}

PUMBA_RATE_TEMPLATE = {'command': '--log-level=debug netem --tc-image="gaiadocker/iproute2" --duration=1h rate -r={rate} "re2:validator."',
                             'container_name': 'pumba_rate',
                             'depends_on': {},
                             'image': 'gaiaadm/pumba',
                             'volumes': ['/var/run/docker.sock:/var/run/docker.sock']}


NGINX_TEMPLATE = {
    "image": "nginx:latest",
    "container_name": "nginx",
    "restart": "unless-stopped",
    "depends_on": {},
    "expose": [8000, 443],
    "ports": ["8080:8000"],
    "volumes": ["./nginx/nginx.conf:/etc/nginx/nginx.conf"],
    "networks": {"gq-net": {"ipv4_address": ""}},
}


ROUND_TEMPLATE = {
    "label": "",
    "rateControl": {"opts": {"tps": 100}, "type": "fixed-rate"},
    "txNumber": 0,
    "workload": {
        "arguments": {
            "initialMoney": 10000,
            "moneyToTransfer": 100,
            "numberOfAccounts": 0,
        },
        "module": "",
    },
}
