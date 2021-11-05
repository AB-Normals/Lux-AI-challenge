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

echo ${yellow}AB-Normals{rst} ${cyan}TOURNAMENT${rst}
echo
lux-ai-2021 --rankSystem="wins" --storeReplay=false --storeLogs=false  --tournament ./bots/first/main.py  ./bots/ymca/main.py  ./kits/python/simple/main.py ./bots/villages/main.py
