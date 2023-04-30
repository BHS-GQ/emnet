import time
import subprocess
import logging
import os
import argparse
import json
import traceback
import paramiko

from glob import glob
from pathlib import Path
from dotenv import dotenv_values

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=Path)
parser.add_argument('--logs', action='store_true')
args = parser.parse_args()


PWD = Path(__file__).parent
dotenv_path = PWD / '.env'
CONFIG = dotenv_values(str(dotenv_path.resolve()))
CALIPER_TEST_CFG = (PWD / 'testconfig.yaml').resolve()
CALIPER_NET_CFG = (PWD / 'networkconfig.json').resolve()
CALIPER_WORKSPACE_PATH = Path(CONFIG['CALIPER_WORKSPACE_PATH'])
TAR_FILE = 'test.tar.gz'
TEST_DIR = os.getcwd().split('/')[-1]

if args.output:
    RESULTS_DIR = PWD / args.output
else:
    max_report_idx = 0
    report_dirs = glob(f'{PWD}/report_*')
    if len(report_dirs) > 0: 
        report_dirs.sort()
        max_report_idx = int(report_dirs[-1].split('_')[-1])
    RESULTS_DIR = PWD / f'report_{max_report_idx + 1}'

procs = []

def main():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    else:
        raise Exception('Test report+logs dir already exists!')
    
    # tar test directory
    tar_test = subprocess.run(['tar', '-czvf', f"../{TAR_FILE}", f"../{TEST_DIR}"])

    # Connect to net machine
    ssh = paramiko.SSHClient()
    k = paramiko.RSAKey.from_private_key_file(CONFIG['NET_PEM_FILE'])
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CONFIG['NET_IP'], username="ubuntu", pkey=k)

    # Pass network files
    sftp = ssh.open_sftp()
    sftp.put(f"../{TAR_FILE}", f'/home/ubuntu/{TAR_FILE}')
    sftp.close()

    _stdin, _stdout,_stderr = ssh.exec_command(f'tar -xvzf {TAR_FILE}')
    time.sleep(5) # tar is incomplete without a sleep
    _stdin, _stdout,_stderr = ssh.exec_command(f'rm -f {TAR_FILE}')
    _stdin.close()
    ssh.close()

    # Start network
    # assumes that required dependencies are already installed in net machine
    run_path = PWD / 'run.sh'
    subprocess.run([str(run_path.resolve())])

    time.sleep(30)

    # Run Caliper
    full_caliper_ws_path = str(CALIPER_WORKSPACE_PATH.expanduser())
    subprocess.run([
        'npx', 'caliper', 'launch', 'manager',
        '--caliper-workspace', full_caliper_ws_path,
        '--caliper-benchconfig', str(CALIPER_TEST_CFG),
        '--caliper-networkconfig', str(CALIPER_NET_CFG)
    ],
    cwd=full_caliper_ws_path)

    remove_path = PWD / 'remove.sh'
    subprocess.run([str(remove_path.resolve())])
    
    # Get report and logs
    report_path = CALIPER_WORKSPACE_PATH / 'report.html'
    target_path = RESULTS_DIR / 'report.html'
    subprocess.run(['mv', str(report_path.expanduser()), str(target_path.expanduser())])

    if args.logs:
        logs_dir = PWD / 'logs' / 'quorum'
        output_path = RESULTS_DIR / 'logs.tar.gz'
        subprocess.run(['tar', '-czvf', str(output_path.expanduser()), str(logs_dir.expanduser())])
    
    # Write test params
    params_file = RESULTS_DIR / 'params.json'
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
