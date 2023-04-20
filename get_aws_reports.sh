# $1 ip
# $2 .pem file
# $3 test_dir (in aws)
# $4 reports_dir (in aws) - /home/ubuntu/reports

ssh -i $2 ubuntu@${1} "mkdir -p $4; cd $3; ./report_fetcher.sh $4"
mkdir data/_tmp
scp -i $2 -r ubuntu@${1}:$4/* data/_tmp
ssh -i $2 ubuntu@${1} "rm -r $4"
