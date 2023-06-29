# HotStuff Emulated Network

## Generating Tests

Use `gen_tests.py`. Examples below:

```bash
local:~/emnet$ python3 gen_tests.py -t 300 -n 16 -c "2.50" -a "hotstuff" "qbft" -r 5mbit 10mbit 20mbit 50mbit
```

```bash
local:~/emnet$ python3 gen_tests.py -t 400 -n 4 8 16 -c "2.50" -a "ibft" "qbft" -d 25 50 100
```

## Uploading Tests

Update `.env`. Run `upload_test.py`:

```bash
local:~/emnet$ python3 upload_test.py -t generator/<test_dir_name>
```

## Running Tests

On the network machine, run a `tmux` session in the test directory and run the ff:

```bash
network-machine:~/<test_dir>$ python3 runner.py
```

You can optionally append `sudo shutdown -h now` to shutdown the VM after a test.

```bash
network-machine:~/<test_dir>$ python3 runner.py; sudo shutdown -h now
```

## Getting Results

```bash
local:~/emnet$ python3 get_results.py -t <test_dir_name>
```

## Generating Plots

In the `data/` subdir:

```bash
local:~/emnet/data$ python3 to_csv.py -t <test_dir_name>
local:~/emnet/data$ python3 gen_plots.py -t <test_dir_name> -k <test_type>
```

Where `<test_type>` can be:

- `rate_limit`
- `scalability`
- `tps` (WIP)

Note that `to_csv.py` skips failed tests. `gen_plots.py` only considers data poitns with 3 runs or more.

## Experiment Logs

Logs of the experiments can be found [here](https://drive.google.com/file/d/11bjGytybFbMGvbteNQo6xXYYx9IW399u/view?usp=sharing)
