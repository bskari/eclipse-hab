#!/bin/bash

grep 'Banner' /etc/ssh/sshd_config | grep '#'
if [ $? -eq 1 ] ;
then
	echo 'Appending banner config to SSHD'
	echo 'Banner /etc/banner/' >> /etc/ssh/sshd_config
else
	echo 'Banner already configured'
fi
