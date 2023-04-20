COMPOSE_VALIDATOR_TEMPLATE = {
    'build': {'context': 'config/goquorum'},
    'environment': ['GOQUORUM_CONS_ALGO=${GOQUORUM_CONS_ALGO}',
                    'BLOCK_PERIOD=${BLOCK_PERIOD}',
                    'GOQUORUM_GENESIS_MODE=standard'],
    'expose': [30303, 8545, 9545],
    'healthcheck': {
        'interval': '3s',
        'retries': 10,
        'start_period': '5s',
        'test': [
            'CMD',
            'wget',
            '--spider',
            '--proxy',
            'off',
            'http://localhost:8545',
            ],
        'timeout': '3s',
        },
    'networks': {'gq-net': {'ipv4_address': ''}},
    'ports': ['21001:8545/tcp', 30303, 9545],
    'restart': 'on-failure',
    'volumes': ['', './logs/quorum:/var/log/quorum/',
                './config/permissions:/permissions'],
    'deploy': {'resources': {'limits': {'cpus': '2.50',
               'memory': '4G'}, 'reservations': {'memory': '4G'}}},
    }

ROUND_TEMPLATE = {  # must match numberOfAccounts
    'label': 'query',
    'rateControl': {'opts': {'tps': 100}, 'type': 'fixed-rate'},
    'txNumber': 0,
    'workload': {'arguments': {'initialMoney': 10000,
                 'moneyToTransfer': 100, 'numberOfAccounts': 0},
                 'module': ''},
    }
