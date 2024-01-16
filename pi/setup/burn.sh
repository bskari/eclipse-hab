#!/bin/bash
set -u

if [ "${USER}" != 'root' ];
then
    echo 'Please run as root'
    exit 1
fi

if [ "$#" -ne 2 ];
then
    echo "Usage: $0 <raspbian-litebian-file.tgz.zip.img> </dev/sdcard>"
    exit 1
fi

deflate=''
if [ -n "$(echo $1 | grep -P 'gz$')" ];
then
    if [ -n "$(echo $1 | grep -P '(tgz|tar.gz)$')" ];
    then
        deflate='tar -xOzf'
        size="$(gzip -l $1 | grep 'tar$' | awk '{print $2}')"
    elif [ -n "$(echo $1 | grep -P 'gz')" ];
    then
        deflate='gzip -c'
        size="$(gzip -l $1 | grep 'img$' | awk '{print $2}')"
    fi
elif [ -n "$(echo $1 | grep -P 'zip$')" ];
then
    deflate='unzip -p'
    size="$(unzip -l $1 | grep 'img$' | awk '{print $1}')"
elif [ -n "$(echo $1 | grep -P 'img$')" ];
then
    deflate='cat'
    size=$(ls -l | awk '{print $5}')
elif [ -n "$(echo $1 | grep -P 'xz')" ];
then
    deflate='xz --decompress --stdout'
    mibs="$(xz -l $1 | grep 'img' | grep MiB | awk '{print $5}')"
    size="$(echo ${mibs} '*1024*1024' | bc | cut -d '.' -f 1)"
else
    echo 'Invalid file format?'
    exit 1
fi

echo "$2" | grep '/dev/mmcblk'
if [ "$?" -ne 0 ];
then
    echo 'Possibly invalid SD block device, aborting'
    exit 1
fi

if [ -z "${size}" ];
then
    echo "Invalid size: \"${size}\""
    exit 1
fi

set -e
echo "Running $deflate $1 | pv -s ${size} | dd of=$2 bs=1M"
echo 'Press enter to continue'
read

if [ -z "$(which pv)" ];
then
    $deflate $1 | dd of=$2 bs=1M
else
    $deflate $1 | pv -s "${size}" | dd of=$2 bs=1M
fi

