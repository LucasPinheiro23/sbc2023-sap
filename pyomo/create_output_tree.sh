#!/bin/bash

if [ ${pwd##*/} == "pyomo" ]; then

    mkdir output
    cd output

    mkdir 10x10
    cd 10x10
    mkdir d0.1
    mkdir d0.2
    mkdir d0.3
    mkdir d0.4
    mkdir d0.5
    mkdir d0.6
    mkdir d0.7
    mkdir d0.8
    mkdir d0.9
    cd ..

    mkdir 15x15
    cd 15x15
    mkdir d0.1
    mkdir d0.2
    mkdir d0.3
    mkdir d0.4
    mkdir d0.5
    mkdir d0.6
    mkdir d0.7
    mkdir d0.8
    mkdir d0.9
    cd ..

    mkdir 20x20
    cd 20x20
    mkdir d0.1
    mkdir d0.2
    mkdir d0.3
    mkdir d0.4
    mkdir d0.5
    mkdir d0.6
    mkdir d0.7
    mkdir d0.8
    mkdir d0.9
    cd ..

    mkdir 25x25
    cd 25x25
    mkdir d0.1
    mkdir d0.2
    mkdir d0.3
    mkdir d0.4
    mkdir d0.5
    mkdir d0.6
    mkdir d0.7
    mkdir d0.8
    mkdir d0.9
    cd ..

    mkdir logs
    cd logs
        mkdir 10x10
        cd 10x10
        mkdir d0.1
        mkdir d0.2
        mkdir d0.3
        mkdir d0.4
        mkdir d0.5
        mkdir d0.6
        mkdir d0.7
        mkdir d0.8
        mkdir d0.9
        cd ..

        mkdir 15x15
        cd 15x15
        mkdir d0.1
        mkdir d0.2
        mkdir d0.3
        mkdir d0.4
        mkdir d0.5
        mkdir d0.6
        mkdir d0.7
        mkdir d0.8
        mkdir d0.9
        cd ..

        mkdir 20x20
        cd 20x20
        mkdir d0.1
        mkdir d0.2
        mkdir d0.3
        mkdir d0.4
        mkdir d0.5
        mkdir d0.6
        mkdir d0.7
        mkdir d0.8
        mkdir d0.9
        cd ..

        mkdir 25x25
        cd 25x25
        mkdir d0.1
        mkdir d0.2
        mkdir d0.3
        mkdir d0.4
        mkdir d0.5
        mkdir d0.6
        mkdir d0.7
        mkdir d0.8
        mkdir d0.9
        cd ..
    cd ..
    cd ..
    echo "Output folder tree created successfully!"
else
    echo "Aborting. Please initiate this script within pyomo root folder."
fi
