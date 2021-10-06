#!/bin/bash

if [ ! -z $1 ]
then
  cd bots/$1
  tar -czvf $1.tar.gz *
  mv $1.tar.gz ../../submits/
else
  echo "usage: submit.sh BOT"
fi
