import pandas as pd
import matplotlib.pyplot as plt
import json

from glob import glob
from copy import deepcopy
from pathlib import Path
from bs4 import BeautifulSoup


TEST_DIR = '/home/derick/eth1/emnet/data/_n=12,16_tps=100,150,200_pumbaproc/'

dfs = []
result_dirs = glob(f'{TEST_DIR}/*/report_*/')
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
        df_open_perf['Traffic In [MB]'].sum(), df_trans_perf['Traffic In [MB]'].sum()
    ]
    df.loc[:, 'Total Traffic Out [MB]'] = [
        df_open_perf['Traffic Out [MB]'].sum(), df_trans_perf['Traffic Out [MB]'].sum()
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
PLOT_DESIGNS = {
    'Consensus': {        
        'hotstuff': {'color': 'cornflowerblue'},
        'ibft': {'color': 'orange'},
        'qbft': {'color': 'orangered'}
    },
    'N': {
        '4': {'marker': 'o', 'ls': 'solid'},
        '8': {'marker': 'x', 'ls': 'dashed'},
        '12': {'marker': '^', 'ls': ':'},
        '16': {'marker': 's', 'ls': 'dashdot'}
    }
}

transaction_types = ['open','transfer']
for transaction_type in transaction_types:
    _df = master_df.copy()
    _df = _df.loc[_df['Name'] == transaction_type]
    _df = _df.loc[_df['r_idx'] == '1']
    fig, ax = plt.subplots(figsize=(10,8))
    ax.set_xlim([0, 210])
    ax.set_ylim([0, 210])
    for key, grp in _df.groupby(['Consensus', 'N']):
        grp = grp.sort_values(by=['Send Rate (TPS)'])
        ax.plot(
            grp['Send Rate (TPS)'],
            grp['Throughput (TPS)'],
            color=PLOT_DESIGNS['Consensus'][key[0]]['color'],
            marker=PLOT_DESIGNS['N'][key[1]]['marker'],
            linestyle=PLOT_DESIGNS['N'][key[1]]['ls'],
            linewidth=1,
            label=f"{key[0]}_{key[1]}"
        )
    ax.set_title(f'Send Rate (TPS) vs. Throughput (ms) of {transaction_type}')
    ax.set_xlabel('Send Rate (TPS)')
    ax.set_ylabel('Throughput (TPS)')

    ax.legend()
    plt.show()

# for transaction_type in transaction_types:
#     df = master_df.copy()
#     df = df.loc[df['Name'] == transaction_type]
#     fig, ax = plt.subplots(figsize=(10,8))
#     for key, grp in df.groupby(['Consensus', 'N', 'True TPS']):
#         ax.plot(
#             grp['Send Rate (TPS)'],
#             grp['Avg Latency (s)'],
#             color=PLOT_DESIGNS['Consensus'][key[0]]['color'],
#             marker=PLOT_DESIGNS['N'][key[1]]['marker'],
#             linestyle=PLOT_DESIGNS['N'][key[1]]['ls'],
#             linewidth=1,
#             label=f"{key[0]}_{key[1]}"
#         )
#     ax.set_title(f'Send Rate (TPS) vs. Latency (TPS) of {transaction_type}')
#     ax.set_xlabel('Send Rate (TPS)')
#     ax.set_ylabel('Avg Latency (s)')

#     ax.legend()
#     plt.show()