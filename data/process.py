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


parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', type=Path, required=True)
args = parser.parse_args()

TEST_DIR = args.target
PLOT_DESIGNS = {
    'Consensus': {        
        'hotstuff': {'color': 'tab:blue'},
        'ibft': {'color': 'tab:green'},
        'qbft': {'color': 'tab:orange'}
    },
    'N': {
        '4': {'marker': 'o', 'ls': 'solid'},
        '8': {'marker': 'x', 'ls': 'dashed'},
        '12': {'marker': '^', 'ls': ':'},
        '16': {'marker': 's', 'ls': 'dashdot'}
    }
}


def compile_reports():
    dfs = []
    result_dirs = glob(f'{str(TEST_DIR.resolve())}/*/report_*/')
    for result_dir in result_dirs:
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

        to_numeric_cols = [
            'CPU%(avg)',
            'CPU%(max)',
            'Traffic In [MB]',
            'Traffic Out [MB]'
        ]
        tables = soup.findAll("table")
        df_open_perf = pd.read_html(str(tables[3]))[0]
        df_open_perf[to_numeric_cols] = df_open_perf[to_numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)
        df_trans_perf = pd.read_html(str(tables[6]))[0]
        df_trans_perf[to_numeric_cols] = df_trans_perf[to_numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)

        df.loc[:, 'Max Validator CPU%(max)'] = [
            df_open_perf['CPU%(max)'].max(), df_trans_perf['CPU%(max)'].max()
        ]
        df.loc[:, 'Max Validator CPU%(avg)'] = [
            df_open_perf['CPU%(avg)'].max(), df_trans_perf['CPU%(avg)'].max()
        ]
        df.loc[:, 'Total Traffic In [MB]'] = [
            df_open_perf['Traffic In [MB]'].sum(),
            df_trans_perf['Traffic In [MB]'].sum()
        ]
        open_o_sum = df_open_perf.loc[df_open_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
        trans_o_sum = df_trans_perf.loc[df_trans_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
        df.loc[:, 'Total Traffic Out [MB]'] = [
            open_o_sum,
            trans_o_sum
        ]
        df.loc[:, 'Normalized Traffic Out [MB]'] = [  # todo: is this a useful metric?
            open_o_sum / df_open_perf.loc[df_open_perf['Name'] == '/nginx', 'Traffic In [MB]'][0],
            trans_o_sum / df_trans_perf.loc[df_trans_perf['Name'] == '/nginx', 'Traffic In [MB]'][0]
        ]
        df.loc[:, 'N'] = [test_params['N_VALIDATORS']] * 2
        df.loc[:, 'Consensus'] = [test_params['CONSENSUS_ALGO']] * 2
        df.loc[:, 'True TPS'] = [test_params['TPS']] * 2
        df.loc[:, 'CPU Limit'] = [test_params['CPU_LIMIT']] * 2
        df.loc[:, 'Delay'] = [test_params['PUMBA_DELAY']] * 2
        df.loc[:, 'Jitter'] = [test_params['PUMBA_JITTER']] * 2
        df.loc[:, 'Rate'] = [test_params['PUMBA_RATE']] * 2
        df.loc[:, 'r_idx'] = [result_idx] * 2
        
        dfs.append(df)

    master_df = pd.concat(dfs)

    return master_df


def make_line_plot(
    df: pd.DataFrame,
    groupby_cols: list,
    x_col: str,
    x_label: str,
    y_col: str,
    y_label: str,
    file_tag: str,
    transaction_types: list,
    img_dir: Path,
):
    for transaction_type in transaction_types:
        _df = df.copy()
        _df = _df.loc[_df['Name'] == transaction_type]
        _df = _df.groupby(['N', 'Consensus', 'True TPS', 'CPU Limit', 'Delay', 'Jitter', 'Rate'])
        _df = _df[y_col].mean().reset_index()
        fig, ax = plt.subplots(figsize=(10,8))
        for key, grp in _df.groupby(groupby_cols):
            grp = grp.sort_values(by=[x_col])
            ax.plot(
                grp[x_col],
                grp[y_col],
                color=PLOT_DESIGNS['Consensus'][key[0]]['color'],
                marker=PLOT_DESIGNS['N'][key[1]]['marker'],
                linestyle=PLOT_DESIGNS['N'][key[1]]['ls'],
                linewidth=1,
                label=f"{key[0]}_{key[1]}"
            )
        ax.set_title(f'{x_label} vs. {y_label} of {transaction_type}')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        ax.legend()
        img_path = img_dir / f'{file_tag}_{transaction_type}.png'
        plt.savefig(img_path)


def generate_plots(df):
    plots_dir = TEST_DIR / 'plots'
    if os.path.exists(plots_dir):
        shutil.rmtree(plots_dir, ignore_errors=True)
    os.makedirs(plots_dir)

    # throughput plots
    make_line_plot(
        df,
        ['Consensus', 'N'],
        'True TPS',
        'Send Rate (TPS)',
        'Throughput (TPS)',
        'Avg. Throughput (TPS)',
        'throughput',
        ['open', 'transfer'],
        plots_dir,
    )

    # latency plots
    make_line_plot(
        df,
        ['Consensus', 'N'],
        'True TPS',
        'Send Rate (TPS)',
        'Avg Latency (s)',
        'Avg. Latency (s)',
        'latency',
        ['open', 'transfer'],
        plots_dir,
    )

    # metrics plots
    make_line_plot(
        df,
        ['Consensus', 'N'],
        'True TPS',
        'Send Rate (TPS)',
        'Total Traffic Out [MB]',
        'Total Network Out (MB)',
        'traffic_out',
        ['open', 'transfer'],
        plots_dir,
    )
    make_line_plot(
        df,
        ['Consensus', 'N'],
        'True TPS',
        'Send Rate (TPS)',
        'Max Validator CPU%(max)',
        'Average Max. CPU%',
        'cpu_max',
        ['open', 'transfer'],
        plots_dir,
    )


if __name__ == "__main__":
    df_compiled = compile_reports()
    compiled_csv = TEST_DIR / 'compiled.csv'
    df_compiled.to_csv(compiled_csv)

    generate_plots(df_compiled)
