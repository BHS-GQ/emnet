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
TAR_FILE = 'test.tar.gz'


if __name__ == "__main__":
    # tar tests
    tar_test = subprocess.run(['tar', '-czvf', TAR_FILE, args.target])
    logging.info(tar_test.args)

    host = CONFIG['AWS_IP']
    keyfile = CONFIG['AWS_PEM_FILE']
    username = 'ubuntu'
    
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, key_filename=keyfile)

    ftp_client = client.open_sftp()
    ftp_client.put(TAR_FILE, f'/home/ubuntu/{TAR_FILE}')
    ftp_client.close()

    _stdin, _stdout,_stderr = client.exec_command(f'mkdir {args.target.name}')
    _stdin, _stdout,_stderr = client.exec_command(f'tar -xzvf {TAR_FILE} -C {args.target.name} --strip-components=2')
    _stdin, _stdout,_stderr = client.exec_command(f'rm -f {TAR_FILE}')
    _stdin.close()

    client.close()

    subprocess.run(['rm', '-f', TAR_FILE])
