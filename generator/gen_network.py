import sys
import os
import argparse
import json
import shutil
import yaml
import nginx

from pathlib import Path
from glob import glob
from distutils.dir_util import copy_tree
from copy import deepcopy
from dotenv import dotenv_values

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from generator.cfg_templates import *

PWD = Path(__file__).parent
dotenv_path = PWD / '../' / '.env'
_dotenv = dotenv_values(str(dotenv_path.resolve()))


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--consensus-algo', type=str, required=True)
parser.add_argument('-n', '--n-validators', type=int, required=True)
parser.add_argument('-o', '--output', type=Path, required=True)
parser.add_argument('-t', '--tps', type=int, required=True)
parser.add_argument('--cpu', type=str, default='3.00', required=True)
parser.add_argument('-d', '--delay', type=str)
parser.add_argument('-j', '--jitter', type=str)
parser.add_argument('-r', '--rate', type=str)
parser.add_argument('-i', '--ip', type=str, default='172.16.239.')
parser.add_argument('--disable-query', action='store_true')
args = parser.parse_args()

def generate_name(args):
    n_val_str = str(args.n_validators)
    tps_str = str(args.tps)

    name = f'{args.consensus_algo}_n={n_val_str}_tps={tps_str}'
    if args.delay or args.jitter or args.rate:
        name += '_net='
    if args.delay:
        name += f'd{args.delay}'
    if args.jitter:
        name += f'j{args.jitter}'
    if args.rate:
        name += f'r{args.rate}'
    
    return name


FILE_DIR = os.path.dirname(os.path.realpath(__file__))
GENESIS_DIR = Path(f'{FILE_DIR}/genesis/{args.consensus_algo}_{str(args.n_validators)}')
BLS_KEY_DIR = Path(f'{FILE_DIR}/bls_keys/{str(args.n_validators)}')  # Only used by hotstuff
TEMPLATE_DIR = Path(f'{FILE_DIR}/templates')
GENERATED_DIR = Path(f'{FILE_DIR}/{args.output}/')
OUTPUT_DIR = Path(
    f'{GENERATED_DIR}/{generate_name(args)}/'
)


def get_val_info(args) -> dict:
    # Generate val info
    val_info = {}
    for val_dir in glob(f'{GENESIS_DIR}/validator*'):
        val_idx = int(val_dir.split('validator')[-1])
        val_info[val_idx] = {}
        for file in Path(val_dir).glob('*'):
            fpath = Path(file)
            val_info[val_idx][fpath.name] = fpath.read_text()
    
    # Generate IP addresses
    for val_idx in range(args.n_validators):
        val_info[val_idx]['ip'] = args.ip + str(val_idx + 6)

    return val_info


def build_static_nodes(val_info: dict) -> list:
    # Build static-nodes.json
    enodes = []
    for val_dir in glob(f'{GENESIS_DIR}/validator*'):
        val_idx = int(val_dir.split('validator')[-1])
        nodekey_pub = val_info[val_idx]["nodekey.pub"]
        ip = val_info[val_idx]["ip"]
        enodes.append(
            f'enode://{nodekey_pub}@{ip}:30303'
        )

    return enodes


def build_genesis(args, val_info: dict) -> list:
    genesis_file = GENESIS_DIR / Path("goQuorum/genesis.json")
    with open(genesis_file, 'r', encoding='utf-8') as f:
        genesis = json.load(f)

        # Inject caliper contract deployer
        genesis["alloc"]["0x8fd250a1957c953efccf7c699ff5fd07ff0141f8"] = {
            "balance": "9999999999999999999999999999"
        }

        genesis["config"]["txnSizeLimit"] = 128
        genesis["config"]["maxCodeSizeConfig"] = [
            {
                "block": 0,
                "size": 128
            }
        ]

        block_period = 1
        timeout = 5
        if args.consensus_algo == "hotstuff":
            # Hotstuff uses QBFT genesis
            if "qbft" in genesis["config"]:
                del (genesis["config"]["qbft"])

            genesis["mixHash"] = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            genesis["config"]["isQuorum"] = True

            hotstuff_cfg = {
                "requesttimeoutmilliseconds": timeout * 1000,  # Matches ibft, qbft default
                "blockperiodseconds": block_period,
                "policy": "RoundRobin",
                "faultymode": "Disabled",

                # Get validator addresses
                "validators": [
                    f'0x{v["address"]}' for k, v in val_info.items()
                ]
            }
            genesis["config"]["hotstuff"] = hotstuff_cfg
        elif args.consensus_algo == "ibft":
            genesis["config"]["ibft"]["blockperiodseconds"] = block_period
            genesis["config"]["ibft"]["requesttimeoutseconds"] = timeout
        elif args.consensus_algo == "qbft":
            genesis["config"]["qbft"]["requesttimeoutseconds"] = timeout
            genesis["config"]["qbft"]["blockperiodseconds"] = block_period
            del(genesis["config"]["qbft"]["emptyblockperiodseconds"])

    return genesis


def load_template(args, genesis: dict, enodes: list):
    network_template = TEMPLATE_DIR / Path("network")
    copy_tree(
        str(network_template.resolve()),
        str(OUTPUT_DIR.resolve())
    )

    # Copy validator data
    nodes_dir = OUTPUT_DIR / Path("config/nodes")
    for val_dir in glob(f'{GENESIS_DIR}/validator*'):
        val_idx = int(val_dir.split("validator")[-1])
        val_path = Path(val_dir)

        new_val_dir = nodes_dir / Path(f'validator{val_idx}')
        os.makedirs(new_val_dir)
        copy_tree(
            str(val_path.resolve()),
            str(new_val_dir.resolve())
        )

        if args.consensus_algo == "hotstuff":
            # Copy BLS Keys
            pri_keypath = BLS_KEY_DIR / f"bls-private-key{val_idx}.json"
            pub_keypath = BLS_KEY_DIR / f"bls-public-key.json"

            shutil.copy(pri_keypath, new_val_dir / f"bls-private-key.json")
            shutil.copy(pub_keypath, new_val_dir)

    
    # Copy static nodes and genesis
    gq_data_dir = OUTPUT_DIR / Path("config/goquorum/data")
    with open(gq_data_dir / Path("genesis.json"), 'w') as f:
        json.dump(genesis, f, indent=4, sort_keys=True)
    with open(gq_data_dir / Path("static-nodes.json"), 'w') as f:
        json.dump(enodes, f, indent=4, sort_keys=True)
    with open(gq_data_dir / Path("permissioned-nodes.json"), 'w') as f:
        json.dump(enodes, f, indent=4, sort_keys=True)

def create_dotenv(args):
    dotenv_path = OUTPUT_DIR / Path(".env")
    with open(dotenv_path, "w") as f:
        f.write(f"GOQUORUM_CONS_ALGO={args.consensus_algo}\n")
        f.write(f"BLOCK_PERIOD=1\n")
        f.write(f"LOCK_FILE=.quorumDevQuickstart.lock\n")
        f.write(f"CALIPER_WORKSPACE_PATH=~/caliper-benchmarks\n")
        f.write(f"CONSENSUS_ALGO={args.consensus_algo}\n")
        f.write(f"N_VALIDATORS={args.n_validators}\n")
        f.write(f"TPS={args.tps}\n")
        f.write(f"CPU_LIMIT={args.cpu}\n")
        f.write(f"NET_IP={_dotenv['NET_IP']}\n")
        f.write(f"CAL_IP={_dotenv['CAL_IP']}\n")
        f.write(f"NET_PEM_FILE={_dotenv['NET_PEM_FILE']}\n")
        if args.delay:
            f.write(f"PUMBA_DELAY={args.delay}\n")
        if args.jitter:
            f.write(f"PUMBA_JITTER={args.jitter}\n")
        if args.rate:
            f.write(f"PUMBA_RATE=\"{args.rate}\"\n")

def edit_dockerfile(args):
    # Edit GQ Dockerfile
    df_path = OUTPUT_DIR / Path("config/goquorum/Dockerfile")
    with open(df_path, 'r') as f:
        df_text = f.readlines()

    with open(df_path, 'w') as f:
        f.writelines(df_text)

def edit_docker_compose(args, val_info: dict):
    dc_file = OUTPUT_DIR / Path("docker-compose.yml")
    with open(dc_file, "r") as f:
        try:
            dc = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    dc['services'] = {}
    dc['networks']['gq-net']['ipam']['config'][0]['subnet'] = f'{args.ip}0/24'

    # Add nginx to services
    nginx_svc = deepcopy(NGINX_TEMPLATE)
    _ip = args.ip + '5'
    nginx_svc['networks']['gq-net']['ipv4_address'] = _ip
    for val_idx in range(args.n_validators):
        validator_name = f"validator{val_idx}"
        nginx_svc['depends_on'][validator_name] = {"condition": "service_healthy"}
    dc['services']['nginx'] = nginx_svc

    # Add validators to services
    for val_idx in range(args.n_validators):
        validator_name = f"validator{val_idx}"
        validator_exposed_port = f'210{(val_idx + 1):02d}:8545/tcp'
        validator_keys_volume = f'./config/nodes/{validator_name}:/config/keys'
        validator_ip =  val_info[val_idx]['ip']

        val = deepcopy(COMPOSE_VALIDATOR_TEMPLATE)
        val['networks']['gq-net']['ipv4_address'] = validator_ip
        val['ports'][0] = validator_exposed_port
        val['volumes'][0] = validator_keys_volume
        val['container_name'] = validator_name
        val['deploy']['resources']['limits']['cpus'] = args.cpu
        # val['labels'] = [
        #     f'com.docker-tc.enabled=1',
        #     f'com.docker-tc.limit={args.rate}',
        #     # f'com.docker-tc.delay=20ms',
        # ]

        dc['services'][validator_name] = val

    # Update docker-compose.yml
    with open(dc_file, 'w') as f:
        yaml.dump(dc, f, default_flow_style=False)

def load_caliper():
    network_template = TEMPLATE_DIR / Path("caliper")
    copy_tree(
        str(network_template.resolve()),
        str(OUTPUT_DIR.resolve())
    )

def edit_testconfig(args):
    testcfg_path = OUTPUT_DIR / "testconfig.yaml"
    with open(testcfg_path, "r") as f:
        try:
            testcfg = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    testcfg['test']['workers']['number'] = min(args.n_validators, 8)

    # Clear rounds
    testcfg['test']['rounds'] = []

    if not args.disable_query:
        txn_types = ['open', 'query', 'transfer']
    else:
        txn_types = ['open', 'transfer']

    for txn_type in txn_types:
        round = deepcopy(ROUND_TEMPLATE)
        round['label'] = txn_type
        round['rateControl']['opts']['tps'] = args.tps

        tx_number = 1000
        round['txNumber'] = tx_number
        round['workload']['arguments']['numberOfAccounts'] = tx_number
        round['workload']['module'] = f'benchmarks/scenario/simple/{txn_type}.js'

        testcfg['test']['rounds'].append(round)
    
    # Caliper monitoring
    monitored_ips = []
    for val_idx in range(args.n_validators):
        monitored_ips.append(
            f'http://{_dotenv["NET_IP"]}:2375/validator{val_idx}'
        )
    testcfg['monitors']['resource'][0]['options']['containers'] = monitored_ips

    with open(testcfg_path, 'w') as f:
        yaml.dump(testcfg, f, default_flow_style=False)

def edit_networkconfig(val_info):
    net_cfg_path = OUTPUT_DIR / "networkconfig.json"
    with open(net_cfg_path, 'r', encoding='utf-8') as f:
        net_cfg = json.load(f)

    # Set url to net machine local ip
    net_cfg['ethereum']['url'] = f'ws://{_dotenv["NET_IP"]}:8080'

    with open(net_cfg_path, 'w', encoding='utf-8') as f:
        json.dump(net_cfg, f, indent=4, sort_keys=True)

def create_loadbalancer(val_info):
    c = nginx.Conf()

    events = nginx.Events()
    c.add(events)

    root = nginx.Http()

    _map = nginx.Map('$http_upgrade $connection_upgrade')
    _map.add(
        nginx.Key('default', 'upgrade'),
        nginx.Key("''", 'close')
    )
    root.add(_map)

    upstream = nginx.Upstream('websocket')
    for idx in range(min(args.n_validators, 8)):
        ip = val_info[idx]['ip']
        
        upstream.add(
            nginx.Key('server', f'{ip}:8546')
        )
    root.add(upstream)

    server = nginx.Server()
    server.add(nginx.Key('listen', 8000))
    server.add(
        nginx.Location(
            '/',
            nginx.Key('proxy_pass', 'http://websocket'),
            nginx.Key('proxy_http_version', '1.1'),
            nginx.Key('proxy_set_header', 'Upgrade $http_upgrade'),
            nginx.Key('proxy_set_header', 'Connection $connection_upgrade'),
            nginx.Key('proxy_set_header', 'Host $host'),
        )
    )
    root.add(server)
    c.add(root)

    nginx_dir = OUTPUT_DIR / 'nginx'
    os.makedirs(nginx_dir)
    conf_file = nginx_dir / 'nginx.conf'
    nginx.dumpf(c, conf_file)

def main(args):
    if not os.path.exists(GENERATED_DIR):
        os.makedirs(GENERATED_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    else:
        raise Exception(f'OUTPUT_DIR={OUTPUT_DIR} already exists!')

    val_info = get_val_info(args)
    enodes = build_static_nodes(val_info)
    genesis = build_genesis(args, val_info)

    load_template(args, genesis, enodes)

    create_dotenv(args)

    # Nginx LB
    create_loadbalancer(val_info)

    # Docker
    edit_dockerfile(args)
    edit_docker_compose(args, val_info)

    # Caliper
    load_caliper()

    edit_testconfig(args)
    edit_networkconfig(val_info)

if __name__ == '__main__':
    main(args)
