import time
import subprocess
import logging
import os
import argparse
import json
import traceback

from pathlib import Path
from dotenv import dotenv_values

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=Path, required=True)
parser.add_argument('--logs', action='store_true')
args = parser.parse_args()


CONFIG = dotenv_values('.env')
TEST_DIR = Path(__file__).parent
REPORT_LOGS_DIR = TEST_DIR / args.output
CALIPER_TEST_CFG = (TEST_DIR / 'testconfig.yaml').resolve()
CALIPER_NET_CFG = (TEST_DIR / 'networkconfig.json').resolve()
CALIPER_WORKSPACE_PATH = Path(CONFIG['CALIPER_WORKSPACE_PATH'])


procs = []

def main():
    if not os.path.exists(REPORT_LOGS_DIR):
        os.makedirs(REPORT_LOGS_DIR)
    else:
        raise Exception('Test report+logs dir already exists!')

    # Start network
    subprocess.run(['./run.sh'])

    time.sleep(5)

    # Run pumba netem
    pumba_delay, pumba_rate = None, None
    if CONFIG['PUMBA_DELAY'] != '0' or CONFIG['PUMBA_JITTER'] != '0':
        pumba_delay = subprocess.Popen([
            'pumba', '--log-level', 'debug',
            'netem',
            '--tc-image', 'gaiadocker/iproute2',
            '--duration', '1h',
            'delay',
            '--time', CONFIG['PUMBA_DELAY'],
            '--jitter', CONFIG['PUMBA_JITTER'],
            're2:validator.'
        ])
        procs.append(pumba_delay)

    if 'PUMBA_RATE' in CONFIG:
        pumba_rate = subprocess.Popen([
            'pumba', '--log-level', 'debug', 
            'netem',
            '--tc-image', 'gaiadocker/iproute2',
            '--duration', '1h',
            'rate',
            '-r', CONFIG['PUMBA_RATE'],
            're2:validator.'
        ])
        procs.append(pumba_rate)

    time.sleep(20)

    # Run Caliper
    full_caliper_ws_path = str(CALIPER_WORKSPACE_PATH.expanduser())
    subprocess.run([
        'npx', 'caliper', 'launch', 'manager',
        '--caliper-workspace', full_caliper_ws_path,
        '--caliper-benchCONFIG', str(CALIPER_TEST_CFG),
        '--caliper-networkCONFIG', str(CALIPER_NET_CFG)
    ],
    cwd=full_caliper_ws_path)

    # Shutdown everything
    if pumba_delay is not None:
        pumba_delay.terminate()
        pumba_delay.wait()
    if pumba_rate is not None:
        pumba_rate.terminate()
        pumba_delay.wait()

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
