# $1 tps "50 100 200"
# $2 N "4 8 12"
# $3 output_dir "_output"
# $4 delay 20
# $5 jitter 0
# $6 rate 100kbit


CONSENSUS_ALGOS="hotstuff ibft qbft"
for n in $2
do
    for algo in $CONSENSUS_ALGOS
    do
        python3 -m generator.gen_network -c $algo -o $3 -t $1 -n $n --ip 172.16.239.
    done
done

target_dir="generator/"$3
python3 -m generator.gen_runner -t $target_dir -d $4 -j $5 -r $6
