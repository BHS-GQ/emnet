import time
import subprocess
import logging
import os
import argparse
import json
import traceback
import re

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

if args.output:
    RESULTS_DIR = PWD / args.output
else:
    max_report_idx = 0
    report_dirs = glob(f'{PWD}/report_*')
    if len(report_dirs) > 0: 
        report_idx = [
            int(rdir.split('_')[-1])
            for rdir in report_dirs
        ]
        max_report_idx = max(report_idx)
    RESULTS_DIR = PWD / f'report_{max_report_idx + 1}'

pumba_proc = None
pumba_log = open('pumba.log', 'w')

def run_test():
    # Start network
    run_path = PWD / 'run.sh'
    subprocess.run([str(run_path.resolve())])

    time.sleep(5)
    # Run pumba netem
    delay_flag, rate_flag = False, False
    if 'PUMBA_DELAY' in CONFIG:
        delay_val = CONFIG['PUMBA_DELAY'].split('ms')[0]
        pumba = [
            'pumba', '--log-level', 'debug',
            'netem',
            '--tc-image', 'gaiadocker/iproute2',
            '--duration', '1h',
            'delay',
            '--time', delay_val,
            '--jitter', '0',
            're2:validator.'
        ]
        delay_flag = True
    elif 'PUMBA_RATE' in CONFIG:
        pumba = [
            'pumba', '--log-level', 'debug', 
            'netem',
            '--tc-image', 'gaiadocker/iproute2',
            '--duration', '1h',
            'rate',
            '-r', CONFIG['PUMBA_RATE'],
            're2:validator.'
        ]
        rate_flag = True
    
    pumba_flag = delay_flag or rate_flag
    if delay_flag and rate_flag:
        raise Exception('Both pumba delay and rate provided!')
    elif pumba_flag:
        pumba_proc = subprocess.Popen(
            pumba,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        tc_started = 0
        for line in pumba_proc.stdout:
            line = line.decode()
            print(line, end='')
            msg_starting = re.findall(
                'msg="tc container created, starting it"',
                line
            )
            if len(msg_starting) > 0:
                tc_started += 1
                if tc_started == int(CONFIG['N_VALIDATORS']):
                    print('All tc containers started. Running Caliper...')
                    break

    time.sleep(20)

    # Run Caliper
    full_caliper_ws_path = str(CALIPER_WORKSPACE_PATH.expanduser())
    subprocess.run([
        'npx', 'caliper', 'launch', 'manager',
        '--caliper-workspace', full_caliper_ws_path,
        '--caliper-benchconfig', str(CALIPER_TEST_CFG),
        '--caliper-networkconfig', str(CALIPER_NET_CFG)
    ],
    cwd=full_caliper_ws_path)

    # Shutdown everything
    if pumba_flag:
        pumba_proc.terminate()
        pumba_proc.wait()
        pumba_log.close()

    remove_path = PWD / 'remove.sh'
    subprocess.run([str(remove_path.resolve())])

def main():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    else:
        raise Exception('Test results dir already exists!')

    # Run test proper and time it    
    start = time.time()
    run_test()
    end = time.time()
    elapsed = end - start
    CONFIG['TIME_TAKEN'] = elapsed

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

        if pumba_proc is not None:
            pumba_proc.terminate()
            pumba_proc.wait()
            pumba_log.close()
        subprocess.run(['./remove.sh'])
