: '
$1 - Test directory (local)
$2 - Output test directory (in AWS)
'


source ./.env

tar -czvf tests.tar.gz $1
scp -i $AWS_PEM_FILE tests.tar.gz ubuntu@$AWS_IP:/home/ubuntu/

ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "mkdir $2"
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP "tar -xzvf tests.tar.gz -C $2 --strip-components=2"
ssh -i $AWS_PEM_FILE ubuntu@$AWS_IP 'rm -f tests.tar.gz'
rm -f tests.tar.gz
