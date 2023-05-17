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
    total_tests = 0
    for test_dir in test_dirs:
        td_path = Path(test_dir)
        td_full = td_path.resolve()
        
        _dotenv_path = td_path / '.env'
        _dotenv = dotenv_values(str(_dotenv_path.resolve()))
        ca_id = (_dotenv['CONSENSUS_ALGO'], _dotenv['N_VALIDATORS'])
        print(ca_id)
        if prev_consensus != ca_id :
            print("Pruning!")
            subprocess.run(['docker', 'system', 'prune', '-f'], cwd=td_full)

        runs = 5
        for idx in range(runs): # todo: argparse
            print(f"Starting {td_full} Run {idx + 1}...")
            total_tests += 1
            # Timeout after 10 mins
            subprocess.run(['python3', 'test.py'], cwd=td_full, timeout=float(60*10))
            time.sleep(1)

        prev_consensus = ca_id
    print(total_tests)


if __name__ == "__main__":
    try:
        run_all()
    except Exception as e:
        logging.error(traceback.format_exc())

    # todo: cleanup
