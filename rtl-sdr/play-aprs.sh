#!/bin/bash
if [ -f 'squelch-level.txt' ] ;
then
	squelch_level="$(cat squelch-level.txt)"
else
	squelch_level='0'
fi

if [ -f 'ppm-error.txt' ] ;
then
	ppm_error="$(cat ppm-error.txt)"
else
	ppm_error='0'
fi

rtl_fm_command="rtl_fm -f 144.390M -s 22050 -l ${squelch_level} -p ${ppm_error} -"
play_command='play -r 24k -t raw -e s -b 16 -c 1 -V1 -'
echo "${rtl_fm_command} | ${play_command}"
${rtl_fm_command} | ${play_command}
