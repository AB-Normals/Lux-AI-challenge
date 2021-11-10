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

usage="usage: run.sh [--docker] BOT1 [BOT2]"

RUNMODE="local"

if [ $# -eq 1 ]
then
    ARG1=bots/$1/main.py
    BOT1=$1
    ARG2=kits/python/simple/main.py
    BOT2='simple(kit)'
elif [ $# -lt 4 ]
then
    if [ "$1" = "--docker" ]
    then
        RUNMODE="docker"
        ARG1=bots/$2/main.py
        BOT1=$2
        if [ ! -z $3 ]
        then
            ARG2=bots/$3/main.py
            BOT2=$3
        else
            ARG2=kits/python/simple/main.py
            BOT2='simple(kit)'
        fi
    elif [ $# -eq 2 ]
    then
        ARG1=bots/$1/main.py
        BOT1=$1
        ARG2=bots/$2/main.py
        BOT2=$2
    else
        RUNMODE="none"
        echo "ERR: invalid parameters"
        echo ${usage}
    fi
else
    RUNMODE="none"
    echo "ERR: invalid number of parameters"
    echo ${usage}
fi

if [ "${RUNMODE}" = "local" ]
then
    echo Competition: ${yellow}${BOT1}${rst} vs ${cyan}${BOT2}${rst}
    echo
    lux-ai-2021 ${ARG1} ${ARG2} --python=python3 --out=replays/${BOT1}_vs_${BOT2}.json
elif [ "${RUNMODE}" = "docker" ]
then
    echo ${red}              RUN ON DOCKER${rst}
    echo ${blue}              -------------${rst}
    echo Competition: ${yellow}${BOT1}${rst} vs ${cyan}${BOT2}${rst}
    echo
    ./cli.sh ${ARG1} ${ARG2} --python=python3 --out=replays/${BOT1}_vs_${BOT2}.json
fi