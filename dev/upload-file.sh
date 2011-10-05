#! /bin/bash
set -e
rsync -vre ssh $1 jseipp,rednotebook@web.sourceforge.net:htdocs
