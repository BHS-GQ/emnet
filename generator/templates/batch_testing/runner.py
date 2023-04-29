import traceback
import subprocess
import logging
import time

from glob import glob
from pathlib import Path


PWD = Path(__file__).parent

def run_all():
    test_dirs = glob('./*/')
    for test_dir in test_dirs:
        test_dir = Path(test_dir).resolve()

        for idx in range(3): # todo: argparse
            logging.info(f"Starting {test_dir} Run {idx + 1}...")
            subprocess.run(['python3', 'test.py'], cwd=test_dir)
            subprocess.run(['docker', 'system', 'prune', '-f'], cwd=test_dir)
            time.sleep(5)

if __name__ == "__main__":
    try:
        run_all()
    except Exception as e:
        logging.error(traceback.format_exc())

    # todo: cleanup
