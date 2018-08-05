#!/bin/bash

SCRIPT=github-backup.py
BIN=/usr/bin/github-backup

install -m 777 $SCRIPT $BIN && echo "Installed as $BIN"
