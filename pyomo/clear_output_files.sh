#!/bin/bash

cd output
read -p "WARNING: Delete all content within $PWD and subfolders (y/n)? " input

ans="y"

if [ "$input" == "$ans" ]; then
    find . -type f -delete -print
    echo "Deleting..."
else
    echo "Aborting"
fi

cd ..
