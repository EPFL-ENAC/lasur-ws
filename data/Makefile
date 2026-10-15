version=$(shell date +%FT%H:%M)
bucket=10208-fcd9acb029f419e6493edf97f4592b96
folder=lasur-ws

help:
	@echo s3://${bucket}/${folder}/

cdn:
	s3cmd put --recursive --acl-public --guess-mime-type geneva s3://${bucket}/${folder}/${version}/
