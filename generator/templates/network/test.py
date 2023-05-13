import time
import subprocess
import logging
import os
import argparse
import json
import traceback
import re
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

    time.sleep(5) # change this for delay tests

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
            're2:validator.',
            # 're2:(validator.|nginx)',
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


    ssh_client = paramiko.SSHClient()
    k = paramiko.RSAKey.from_private_key_file(CONFIG['NET_PEM_FILE'])
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(CONFIG['CAL_IP'], username="ubuntu", pkey=k)

    # Pass network files
    sftp = ssh_client.open_sftp()
    sftp.put(f"./networkconfig.json", f'/home/ubuntu/networkconfig.json')
    sftp.put(f"./testconfig.yaml", f'/home/ubuntu/testconfig.yaml')
    sftp.close()

    time.sleep(15)

    # Run Caliper
    #   assumes you have a local git clone of caliper repo with checkout tag of v0.5.0 
    #   with proper fix to remote monitoring line bug: https://github.com/hyperledger/caliper/issues/1493
    caliper_cmd = ' '.join([
        'cd caliper-benchmarks;',
        'node', '/home/ubuntu/caliper/packages/caliper-cli/caliper.js', 'launch', 'manager',
        '--caliper-workspace', '/home/ubuntu/caliper-benchmarks',
        '--caliper-benchconfig', '/home/ubuntu/testconfig.yaml',
        '--caliper-networkconfig', '/home/ubuntu/networkconfig.json',
    ])
    _stdin, _stdout, _stderr = ssh_client.exec_command(caliper_cmd)
    exit_status = _stdout.channel.recv_exit_status()

    # Shutdown everything
    if pumba_flag:
        pumba_proc.terminate()
        pumba_proc.wait()
        pumba_log.close()

    remove_path = PWD / 'remove.sh'
    subprocess.run([str(remove_path.resolve())])

    # Get report
    #   todo: logs
    _stdin, _stdout,_stderr = ssh_client.exec_command('rm /home/ubuntu/testconfig.yaml /home/ubuntu/networkconfig.json')
    exit_status = _stdout.channel.recv_exit_status()
    target_path = RESULTS_DIR / 'report.html'
    sftp = ssh_client.open_sftp()
    sftp.get('/home/ubuntu/caliper-benchmarks/report.html', str(target_path.expanduser()))
    sftp.close()
    ssh_client.close()


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
