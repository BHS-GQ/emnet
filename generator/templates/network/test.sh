source ./.env

./run.sh

sleep 5

pumba --log-level debug netem --tc-image gaiadocker/iproute2 --duration 1h delay --time $1 --jitter $2 "re2:validator." &
pumba_delay_pid=$!
pumba --log-level debug netem --tc-image gaiadocker/iproute2 --duration 1h rate -r $3 "re2:validator." &
pumba_rate_pid=$!

test_dir=$(pwd)
cal_cfg_path=$test_dir/testconfig.yaml
net_cfg_path=$test_dir/networkconfig.json

sleep 20

(cd $CALIPER_WORKSPACE_PATH && npx caliper launch manager --caliper-workspace $CALIPER_WORKSPACE_PATH --caliper-benchconfig $cal_cfg_path --caliper-networkconfig $net_cfg_path) 

report_path=$CALIPER_WORKSPACE_PATH/report.html
mv $report_path .

kill $pumba_delay_pid
kill $pumba_rate_pid

sleep 5

./remove.sh
