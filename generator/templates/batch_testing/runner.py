import traceback
import subprocess
import logging
import time

from glob import glob
from pathlib import Path
from dotenv import dotenv_values


PWD = Path(__file__).parent

def run_all():
    prev_consensus = ()
    test_dirs = glob('./*/')
    test_dirs.sort()
    for test_dir in test_dirs:
        td_path = Path(test_dir)
        td_full = td_path.resolve()
        for idx in range(3): # todo: argparse
            logging.info(f"Starting {td_full} Run {idx + 1}...")
            # Timeout after 10 mins
            subprocess.run(['python3', 'test.py'], cwd=td_full, timeout=float(60*10))
            time.sleep(5)

        _dotenv_path = td_path / '.env'
        _dotenv = dotenv_values(str(_dotenv_path.resolve()))
        ca_id = (_dotenv['CONSENSUS_ALGO'], _dotenv['N_VALIDATORS'])
        if prev_consensus != ca_id :
            subprocess.run(['docker', 'system', 'prune', '-f'], cwd=td_full)

        prev_consensus = ca_id

if __name__ == "__main__":
    try:
        run_all()
    except Exception as e:
        logging.error(traceback.format_exc())

    # todo: cleanup
