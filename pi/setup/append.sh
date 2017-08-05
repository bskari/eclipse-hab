#!/bin/bash

if [ $# -ne 2 ];
then
	echo 'Need two arguments'
	exit 1
fi

echo $2 >> $1
