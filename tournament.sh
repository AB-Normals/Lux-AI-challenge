#!/bin/bash

#define colors for 'echo' command
# NOTE : '\033[1..m' are light version of the color
black=`tput setaf 0`
red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
blue=`tput setaf 4`
magenta=`tput setaf 5`
cyan=`tput setaf 6`
white=`tput setaf 7`
rst=`tput sgr0` # No Color


args=""

for FILE in ./bots/*
do
    args="${args} ${FILE}/main.py"
done


if [ "$1" = "--docker" ] 
then
    echo ${yellow}AB-Normals{rst} ${cyan}TOURNAMENT${rst} -- ${red}ON DOCKER${rst} 
    echo
    ./cli.sh --rankSystem="wins" --storeReplay=false --storeLogs=false  --tournament $args
elif [ -z $1 ]
then
    echo ${yellow}AB-Normals{rst} ${cyan}TOURNAMENT${rst}
    echo
    lux-ai-2021 --rankSystem="wins" --storeReplay=false --storeLogs=false  --tournament $args
else
    echo "ERR: invalid parameter"
    echo "usage: tournament [--docker]"
fi