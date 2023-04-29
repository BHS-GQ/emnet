: '
-t TPS "50 100 200"
-n Ns "4 8 12"
-o output_dir "_output"
-d delay "20"
-j jitter "0"
-r rate "10mbit"
-c cpu "2.00"
'

while getopts ":t:n:o:d:j:r:" opt; do
  case $opt in
    t) all_tps="$OPTARG"
    ;;
    n) all_n="$OPTARG"
    ;;
    o) output_dir="$OPTARG"
    ;;
    d) delay="$OPTARG"
    ;;
    j) jitter="$OPTARG"
    ;;
    r) rate="$OPTARG"
    ;;
    c) cpu="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done


CONSENSUS_ALGOS="hotstuff ibft qbft"
for n in $all_n
do
    for algo in $CONSENSUS_ALGOS
    do
      for tps in $all_tps
      do
        python3 -m generator.gen_network \
          -c $algo \
          -o $output_dir \
          -t $tps \
          -n $n \
          -d $delay \
          -j $jitter \
          -r $rate \
          --ip 172.16.239. \
          --disable-query \
          --cpu $cpu
      done
    done
done

target_dir="generator/"$output_dir
python3 -m generator.gen_runner -t $target_dir
