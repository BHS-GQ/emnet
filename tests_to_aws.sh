# $1 ip
# $2 test_dir
# $3 .pem file
# $4 output_dir (in aws)

tar -czvf tests.tar.gz $2
scp -i $3 tests.tar.gz ubuntu@${1}:/home/ubuntu/

ssh -i $3 ubuntu@${1} "mkdir $4"
ssh -i $3 ubuntu@${1} "tar -xzvf tests.tar.gz -C $4 --strip-components=2"
ssh -i $3 ubuntu@${1} 'rm -f tests.tar.gz'
rm -f tests.tar.gz
