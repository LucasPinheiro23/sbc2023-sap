#!/bin/bash

cd output
read -p "WARNING: Delete all content within %cd% and subfolders (y/n)? " input

if [$input -eq "y"]
then
    # find . -type f -delete
    echo "Deleting..."
else
    echo "Aborting"

cd ..
