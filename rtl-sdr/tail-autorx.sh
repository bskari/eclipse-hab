#!/bin/bash
echo "Current date is $(date -u)"
file="$(ls -t *log | head -n 1)"
echo "Reading from ${file}"
head -n 1 ${file}
tail -f ${file} | python tail.py
