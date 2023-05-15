import pandas as pd
import matplotlib.pyplot as plt
import json
import argparse
import os
import shutil

from glob import glob
from copy import deepcopy
from pathlib import Path
from bs4 import BeautifulSoup

from constants import *

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', type=Path, required=True)
args = parser.parse_args()


def parse_rate_limit(rlim: str) -> int:
    if 'mbit' in rlim:
        num = int(rlim.split('mbit')[0])
        mbits = num
    elif 'kbit' in rlim:
        num = int(rlim.split('kbit')[0])
        mbits = num / 1000
    elif 'gbit' in rlim:
        num = int(rlim.split('gbit')[0])
        mbits = num * 1e3
    return mbits


def get_new_cols(df: pd.DataFrame, new_cols: dict, test_params: dict, r_idx: int):
    df[COLS_TO_NUMERIC] = df[COLS_TO_NUMERIC].apply(pd.to_numeric, errors='coerce', axis=1)

    new_cols['cpu_max_all'].append(df['CPU%(max)'].max())
    new_cols['cpu_max_avg_all'].append(df['CPU%(avg)'].max())

    net_i_sum = df.loc[df['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
    new_cols['neti_total_mb'].append(net_i_sum)

    net_o_sum = df.loc[df['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
    new_cols['neto_total_mb'].append(net_o_sum)

    new_cols['n'].append(test_params['N_VALIDATORS'])
    new_cols['algo'].append(test_params['CONSENSUS_ALGO'])
    new_cols['tps_param'].append(int(test_params['TPS']))
    new_cols['cpu_limit'].append(test_params['CPU_LIMIT'])
    new_cols['r_idx'].append(r_idx)

    if 'PUMBA_DELAY' in test_params:
        new_cols['delay'].append(test_params['PUMBA_DELAY'])
    else:
        new_cols['delay'].append(None)
    if 'PUMBA_RATE' in test_params:
        rate_limit_converted = parse_rate_limit(test_params['PUMBA_RATE'])
        new_cols['rate_limit'].append(rate_limit_converted)
    else:
        new_cols['rate_limit'].append(None)
    
    return


def compile_reports():
    dfs = []
    result_dirs = glob(f'{str(args.target.resolve())}/*/report_*/')
    print(args.target.resolve())
    for result_dir in result_dirs:
        print(f'Processing {result_dir}...')
        rd_path = Path(result_dir)
        result_idx = rd_path.name.split('_')[-1]
        report_file = rd_path / 'report.html'
        params_file = rd_path / 'params.json'

        with open(report_file, 'r') as f:
            soup = BeautifulSoup(f, "html.parser")
        with open(params_file, 'r') as f:
            test_params = json.load(f)

        # Process results
        summary = soup.find(id="benchmarksummary").table
        df = pd.read_html(str(summary))[0]

        failed_test = False
    
        successful_txn_types = df['Name'].values
        failed_txn_types = set(ALL_TXN_TYPES) - set(successful_txn_types)
        if len(failed_txn_types) > 0:
            print(f'Failed {", ".join(failed_txn_types)}!')
        if len(failed_txn_types) > 1:
            failed_test = True


        for ttype in successful_txn_types:
            failed_txns = df[df['Name'] == ttype]['Fail'].values[0]
            if failed_txns > 0:
                print(f'Failed {ttype}: {failed_txns} txns failed!')
                failed_test = True

        if failed_test:
            print(f'Skipping test...')
            continue

        new_cols: dict = {
            'cpu_max_all': [],
            'cpu_max_avg_all': [],
            'neti_total_mb': [],
            'neto_total_mb': [],
            'n': [],
            'algo': [],
            'tps_param': [],
            'cpu_limit': [],
            'delay': [],
            'rate_limit': [],
            'r_idx': [],
        }

        tables = soup.findAll("table")
        if 'open' in successful_txn_types:
            df_open_perf = pd.read_html(str(tables[3]))[0]
            get_new_cols(df_open_perf, new_cols, test_params, result_idx)
        if 'transfer' in successful_txn_types:
            df_trans_perf = pd.read_html(str(tables[6]))[0]
            get_new_cols(df_trans_perf, new_cols, test_params, result_idx)

        for key, value in new_cols.items():
            df.loc[:, key] = value

        dfs.append(df)

    master_df = pd.concat(dfs)
    master_df = master_df.fillna(value=0)

    return master_df


if __name__ == "__main__":
    df_compiled = compile_reports()
    compiled_csv = args.target / CSV_NAME
    df_compiled.to_csv(compiled_csv)
