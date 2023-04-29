import traceback
import subprocess
import logging
import time

from glob import glob
from pathlib import Path
from dotenv import dotenv_values


PWD = Path(__file__).parent

def run_all():
    prev_consensus = ''
    test_dirs = glob('./*/').sort()
    for test_dir in test_dirs:
        td_path = Path(test_dir)
        td_full = td_path.resolve()
        for idx in range(3): # todo: argparse
            logging.info(f"Starting {td_full} Run {idx + 1}...")
            subprocess.run(['python3', 'test.py'], cwd=td_full)
            time.sleep(5)

        _dotenv_path = td_path / '.env'
        _dotenv = dotenv_values(str(_dotenv_path.resolve()))
        if prev_consensus != _dotenv['CONSENSUS_ALGO']:
            subprocess.run(['docker', 'system', 'prune', '-f'], cwd=td_full)

        prev_consensus = _dotenv['CONSENSUS_ALGO']        


if __name__ == "__main__":
    try:
        run_all()
    except Exception as e:
        logging.error(traceback.format_exc())

    # todo: cleanup
