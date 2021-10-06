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

if [ ! -z $2 ]
then
  ARG2=bots/$2/main.py
  BOT2=$2
else
  ARG2=kits/python/simple/main.py
  BOT2='simple(kit)'
fi

if [ ! -z $1 ]
then
  echo Competition: ${yellow}$1${rst} vs ${cyan}${BOT2}${rst}
  echo
  lux-ai-2021 bots/$1/main.py ${ARG2} --python=python3 --out=replays/$1_vs_${BOT2}.json
else
  echo "usage: run.sh BOT1 [BOT2]"
fi