#!/bin/bash

cd output
read -p "WARNING: Delete all content within $PWD and subfolders (y/n)? " input

if [ "$input" == "y" ]; then
    find . -type f -delete -print
    echo "Deleting..."
else
    echo "Aborting"
fi

cd ..
