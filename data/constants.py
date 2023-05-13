TEST_ID_COLS = ['Name', 'n', 'algo', 'tps_param', 'cpu_limit', 'delay', 'rate_limit']

PLOT_DESIGNS = {
    'algo': {        
        'hotstuff': {'color': 'tab:blue', 'marker': 'o', 'ls': 'solid'},
        'ibft': {'color': 'tab:green', 'marker': 'x', 'ls': 'dashed'},
        'qbft': {'color': 'tab:orange', 'marker': '^', 'ls': ':'}
    },
    'n': {
        '4': {'marker': 'o', 'ls': 'solid'},
        '8': {'marker': 'x', 'ls': 'dashed'},
        '12': {'marker': '^', 'ls': ':'},
        '16': {'marker': 's', 'ls': 'dashdot'}
    }
}

COLS_TO_NUMERIC = [
    'CPU%(avg)',
    'CPU%(max)',
    'Traffic In [MB]',
    'Traffic Out [MB]',
]

ALL_TXN_TYPES = ['open', 'transfer']

CSV_NAME = 'compiled.csv'

PLOT_KWARGS = {
    'scalability': {
        'tput': {
            'groupby_cols': ['algo', 'tps_param'],
            'x_col': 'n',
            'x_label': '# of Validators',
            'y_col': 'tput_mean',
            'y_label': 'Throughput (TPS)',
            'y_range': [0, 400],
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'scale',
            'boxplot': True
        },
        'latency': {
            'groupby_cols': ['algo', 'tps_param'],
            'x_col': 'n',
            'x_label': '# of Validators',
            'y_col': 'lat_mean',
            'y_label': 'Latency (ms)',
            'y_range': [1, 3],
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'scale',
            'boxplot': True
        },
        'neto': {
            'groupby_cols': ['algo', 'tps_param'],
            'x_col': 'n',
            'x_label': '# of Validators',
            'y_col': 'neto_mean',
            'y_label': 'Network Out (MB)',
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'scale',
        },
        'cpu': {
            'groupby_cols': ['algo', 'tps_param'],
            'x_col': 'n',
            'x_label': '# of Validators',
            'y_col': 'cpu_max_avg',
            'y_label': 'Max. CPU Usage (% of total)',
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'scale',
        },
    },
    'rate_limit': {
        'tput': {
            'groupby_cols': ['algo', 'n', 'tps_param'],

            'x_col': 'rate_limit',
            'x_label': 'Rate Limit (mbit/s)',
            'y_col': 'tput_mean',
            'y_label': 'Throughput (TPS)',
            'y_range': [0, 400],
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'rate',
            'boxplot': True,
        },
        'latency': {
            'groupby_cols': ['algo', 'n', 'tps_param'],

            'x_col': 'rate_limit',
            'x_label': 'Rate Limit (mbit/s)',
            'y_col': 'lat_mean',
            'y_label': 'Latency (ms)',
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'rate',
        },
        'neto': {
            'groupby_cols': ['algo', 'n', 'tps_param'],

            'x_col': 'rate_limit',
            'x_label': 'Rate Limit (mbit/s)',
            'y_col': 'neto_mean',
            'y_label': 'Network Out (MB)',
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'rate',
        },
        'cpu': {
            'groupby_cols': ['algo', 'n', 'tps_param'],

            'x_col': 'rate_limit',
            'x_label': 'Rate Limit (mbit/s)',
            'y_col': 'cpu_max_avg',
            'y_label': 'Max. CPU Usage (% of total)',
            'transaction_types': ['open', 'transfer'],
            'img_fname': 'rate',
        },
    }
}