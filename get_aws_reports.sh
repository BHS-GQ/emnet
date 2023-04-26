: '
$1 - Test directory (in AWS)
$2 - Target directory (local; in data/)
$3 - Reports directory (in AWS) (ex. /home/ubuntu/reports)
'


source ./.env

ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir -p $3; cd $1; ./report_fetcher.sh $3"
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir -p $3; cd $1; ./logs_fetcher.sh $3"
mkdir data/$2
scp -i $AWS_PEM_FILE -r ubuntu@$AWS_IP:$3/* data/$2
scp -i $AWS_PEM_FILE ubuntu@$AWS_IP:$1/*.log data/$2
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "rm -r $3"
(cd data/$2 && mkdir -p logs && tar -xzvf logs.tar.gz -C logs && rm logs.tar.gz)
