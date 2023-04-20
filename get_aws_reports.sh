: '
$1 - Test directory (in AWS)
$2 - Reports directory (in AWS) (ex. /home/ubuntu/reports)
$3 - Target directory (local; in data/)
'


source ./.env

ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir -p $2; cd $1; ./report_fetcher.sh $2"
mkdir data/$3
scp -i $AWS_PEM_FILE -r ubuntu@$AWS_IP:$2/* data/_tmp
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "rm -r $2"
