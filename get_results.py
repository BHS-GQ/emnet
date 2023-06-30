import subprocess
import paramiko
import argparse
import logging

from glob import glob
from pathlib import Path
from dotenv import dotenv_values

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', type=Path, required=True)
args = parser.parse_args()

PWD = Path(__file__).parent
dotenv_path = PWD / '.env'
CONFIG = dotenv_values(str(dotenv_path.resolve()))
DATA_DIR = PWD / 'data'


if __name__ == "__main__":
    host = CONFIG['NET_PUB_IP']
    keyfile = CONFIG['NET_PEM_FILE']
    username = 'ubuntu'
    
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, key_filename=keyfile)

    _stdin, _stdout, _stderr = client.exec_command(f'cd {args.target.name}; python3 fetch_results.py -o temp -l; tar -czvf temp.tar.gz temp')
    print(_stdout.read().decode())
    _stdin.close()

    ftp_client = client.open_sftp()
    output_file = DATA_DIR / 'temp.tar.gz'
    ftp_client.get(f'{args.target.name}/temp.tar.gz', str(output_file.resolve()))
    ftp_client.close()

    # cleanup
    _stdin, _stdout, _stderr = client.exec_command(f'cd {args.target.name}; rm -r temp; rm temp.tar.gz')
    print(_stdout.read().decode())
    _stdin.close()
    client.close()

    subprocess.run(['mkdir', args.target.name], cwd=str(DATA_DIR.resolve()))
    subprocess.run(['tar', '-xzvf', 'temp.tar.gz', '-C', args.target.name, '--strip-components', '1'], cwd=str(DATA_DIR.resolve()))
    subprocess.run(['rm', '-rf', 'temp.tar.gz'], cwd=str(DATA_DIR.resolve()))
