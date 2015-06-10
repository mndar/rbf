#!/usr/bin/bash
FILE=$1
EXPANDBY=$2
fallocate -o $(stat -c%s $FILE) $FILE -l $EXPANDBY

