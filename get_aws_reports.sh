: '
$1 - Test directory (in AWS)
$2 - Reports directory (in AWS) (ex. /home/ubuntu/reports)
$3 - Target directory (local; in data/)
'


source ./.env

ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir -p $2; cd $1; ./report_fetcher.sh $2"
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir -p $2; cd $1; ./logs_fetcher.sh $2"
mkdir data/$3
scp -i $AWS_PEM_FILE -r ubuntu@$AWS_IP:$2/* data/$3
scp -i $AWS_PEM_FILE ubuntu@$AWS_IP:$1/*.log data/$3
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "rm -r $2"
(cd data/$3 && mkdir -p logs && tar -xzvf logs.tar.gz -C logs)
