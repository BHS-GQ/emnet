import sys
import os
import argparse
import json
import shutil
import yaml

from pprint import pprint
from pathlib import Path
from glob import glob
from distutils.dir_util import copy_tree
from copy import deepcopy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from generator.cfg_templates import *


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--consensus-algo', type=str, required=True)
parser.add_argument('-n', '--n-validators', type=int, required=True)
parser.add_argument('-o', '--output', type=Path, required=True)
parser.add_argument('-t', '--tps', nargs='+', type=int, required=True)
parser.add_argument('-i', '--ip', type=str, default='172.16.239.')
args = parser.parse_args()


FILE_DIR = os.path.dirname(os.path.realpath(__file__))
GENESIS_DIR = Path(f'{FILE_DIR}/genesis/{args.consensus_algo}_{args.n_validators}')
BLS_KEY_DIR = Path(f'{FILE_DIR}/bls_keys/{args.n_validators}')  # Only used by hotstuff
TEMPLATE_DIR = Path(f'{FILE_DIR}/templates')
GENERATED_DIR = Path(f'{FILE_DIR}/{args.output}')
_tmp_tps = ",".join(map(str, args.tps))
OUTPUT_DIR = Path(
    f'{GENERATED_DIR}/{args.consensus_algo}_n={args.n_validators}_tps={_tmp_tps}'
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
        val_info[val_idx]['ip'] = args.ip + str(val_idx + 5)

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
        genesis["alloc"]["0xfe3b557e8fb62b89f4916b721be55ceb828dbd73"] = {
            "balance": "1000000000000000000000000000"
        }

        if args.consensus_algo == "hotstuff":
            # Hotstuff uses QBFT genesis
            if "qbft" in genesis["config"]:
                del (genesis["config"]["qbft"])

            genesis["mixHash"] = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            genesis["config"]["isQuorum"] = True

            hotstuff_cfg = {
                "requesttimeoutmilliseconds": 10000,  # Matches ibft, qbft default
                "blockperiodseconds": 1,
                "policy": "RoundRobin",
                "faultymode": "Disabled",

                # Get validator addresses
                "validators": [
                    f'0x{v["address"]}' for k, v in val_info.items()
                ]
            }
            genesis["config"]["hotstuff"] = hotstuff_cfg

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

def edit_dockerfile(args):
    # Edit GQ Dockerfile
    df_path = OUTPUT_DIR / Path("config/goquorum/Dockerfile")
    with open(df_path, 'r') as f:
        df_text = f.readlines()

    if args.consensus_algo == 'hotstuff':
        df_text[2] = 'FROM --platform=linux/amd64 derick/hsqfinal:0.0.0\n'
    else:
        df_text[2] = 'FROM --platform=linux/amd64 quorumengineering/quorum:22.7.4\n'

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

    tx_duration = 10
    # Clear rounds
    testcfg['test']['rounds'] = []

    for tps in args.tps:
        round = deepcopy(ROUND_TEMPLATE)
        round['label'] = 'open'
        round['rateControl']['opts']['tps'] = tps

        tx_number = tps * tx_duration
        round['txNumber'] = tx_number
        round['workload']['arguments']['numberOfAccounts'] = tx_number
        round['workload']['module'] = 'benchmarks/scenario/simple/open.js'

        testcfg['test']['rounds'].append(round)

    for tps in args.tps:
        round = deepcopy(ROUND_TEMPLATE)
        round['label'] = 'query'
        round['rateControl']['opts']['tps'] = tps

        tx_number = tps * tx_duration
        round['txNumber'] = tx_number
        round['workload']['arguments']['numberOfAccounts'] = tx_number
        round['workload']['module'] = 'benchmarks/scenario/simple/query.js'

        testcfg['test']['rounds'].append(round)

    for tps in args.tps:
        round = deepcopy(ROUND_TEMPLATE)
        round['label'] = 'transfer'
        round['rateControl']['opts']['tps'] = tps

        tx_number = tps * tx_duration
        round['txNumber'] = tx_number
        round['workload']['arguments']['numberOfAccounts'] = tx_number
        round['workload']['module'] = 'benchmarks/scenario/simple/transfer.js'

        testcfg['test']['rounds'].append(round)

    with open(testcfg_path, 'w') as f:
        yaml.dump(testcfg, f, default_flow_style=False)

def edit_networkconfig(val_info):
    net_cfg_path = OUTPUT_DIR / "networkconfig.json"
    with open(net_cfg_path, 'r', encoding='utf-8') as f:
        net_cfg = json.load(f)

        net_cfg["ethereum"]["contractDeployerAddress"] = val_info[0]["accountAddress"]
        net_cfg["ethereum"]["fromAddress"] = val_info[0]["accountAddress"]

    with open(net_cfg_path, 'w', encoding='utf-8') as f:
        json.dump(net_cfg, f, indent=4, sort_keys=True)


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

    # Docker
    edit_dockerfile(args)
    edit_docker_compose(args, val_info)

    # Caliper
    load_caliper()

    edit_testconfig(args)
    edit_networkconfig(val_info)

    # test.sh

if __name__ == '__main__':
    main(args)
