import time
import subprocess
import logging
import os
import argparse
import json
import traceback

from glob import glob
from pathlib import Path
from dotenv import dotenv_values

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=Path)
parser.add_argument('--logs', action='store_true')
args = parser.parse_args()


CONFIG = dotenv_values('.env')
TEST_DIR = Path(__file__).parent
CALIPER_TEST_CFG = (TEST_DIR / 'testconfig.yaml').resolve()
CALIPER_NET_CFG = (TEST_DIR / 'networkconfig.json').resolve()
CALIPER_WORKSPACE_PATH = Path(CONFIG['CALIPER_WORKSPACE_PATH'])

if args.output:
    REPORT_LOGS_DIR = TEST_DIR / args.output
else:
    max_report_idx = 0
    report_dirs = glob(f'{TEST_DIR}/report_*')
    if len(report_dirs) > 0: 
        report_dirs.sort()
        max_report_idx = int(report_dirs[-1].split('_')[-1])
    REPORT_LOGS_DIR = TEST_DIR / f'report_{max_report_idx + 1}'

procs = []

def main():
    if not os.path.exists(REPORT_LOGS_DIR):
        os.makedirs(REPORT_LOGS_DIR)
    else:
        raise Exception('Test report+logs dir already exists!')

    # Start network
    subprocess.run(['./run.sh'])

    time.sleep(30)

    # Run Caliper
    full_caliper_ws_path = str(CALIPER_WORKSPACE_PATH.expanduser())
    subprocess.run([
        'npx', 'caliper', 'launch', 'manager',
        '--caliper-workspace', full_caliper_ws_path,
        '--caliper-benchCONFIG', str(CALIPER_TEST_CFG),
        '--caliper-networkCONFIG', str(CALIPER_NET_CFG)
    ],
    cwd=full_caliper_ws_path)

    subprocess.run(['./remove.sh'])
    
    # Get report and logs
    report_path = CALIPER_WORKSPACE_PATH / 'report.html'
    target_path = REPORT_LOGS_DIR / 'report.html'
    subprocess.run(['mv', str(report_path.expanduser()), str(target_path.expanduser())])

    if args.logs:
        logs_dir = TEST_DIR / 'logs' / 'quorum'
        output_path = REPORT_LOGS_DIR / 'logs.tar.gz'
        subprocess.run(['tar', '-czvf', str(output_path.expanduser()), str(logs_dir.expanduser())])
    
    # Write test params
    params_file = REPORT_LOGS_DIR / 'params.json'
    with open(params_file, 'w') as f:
        json.dump(CONFIG, f, indent=4, sort_keys=False)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(traceback.format_exc())

        for proc in procs:
            proc.terminate()
            proc.wait()
        subprocess.run(['./remove.sh'])