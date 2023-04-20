import os
import argparse
import json

from pprint import pprint
from pathlib import Path
from glob import glob
from distutils.dir_util import copy_tree


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--consensus-algo', type=str, required=True)
parser.add_argument('-n', '--n-validators', type=int, required=True)
parser.add_argument('-o', '--output', type=Path, required=True)
parser.add_argument('-t', '--tps', nargs='+', required=True)
parser.add_argument('-i', '--ip', type=str, default='172.16.239.')
args = parser.parse_args()


FILE_DIR = os.path.dirname(os.path.realpath(__file__))
GENESIS_DIR = Path(f'{FILE_DIR}/genesis/{args.consensus_algo}_{args.n_validators}')
BLS_KEY_DIR = Path(f'{FILE_DIR}/bls_keys/{args.n_validators}')  # Only used by hotstuff
TEMPLATE_DIR = Path(f'{FILE_DIR}/templates')
GENERATED_DIR = Path(f'{FILE_DIR}/generated')
OUTPUT_DIR = Path(
    f'{GENERATED_DIR}/{args.consensus_algo}_n={args.n_validators}_tps={",".join(args.tps)}'
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


def load_template():
    network_template = TEMPLATE_DIR / Path("network")
    copy_tree(
        str(network_template.resolve()),
        str(OUTPUT_DIR.resolve())
    )

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
    load_template()

if __name__ == '__main__':
    main(args)
