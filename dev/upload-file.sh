#! /bin/bash
set -e

if [[ -z "$1" ]]; then
    echo Please append the file you want to upload
    exit 2
fi

scp $1 jseipp,rednotebook@frs.sourceforge.net:/home/frs/project/r/re/rednotebook/
