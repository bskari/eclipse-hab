#!/bin/bash
if [ $# -ne 1 ] ;
then
    echo "Usage: $0 frequency"
    echo "e.g.: monitor.sh 144.390M"
    exit 1
fi
frequency=$1

if [ -f 'ppm-error.txt' ] ;
then
	ppm_error="$(cat ppm-error.txt)"
else
	ppm_error='0'
fi

rtl_fm_command="rtl_fm -f ${frequency} -p ${ppm_error} -"
direwolf_command='direwolf -c sdr.conf -r 24000 -D 1 -t 0 -l . -'
echo "${rtl_fm_command} | ${direwolf_command}"
${rtl_fm_command} | ${direwolf_command}
