#! /bin/bash
cd ../web
#scp -r . jseipp,rednotebook@web.sourceforge.net:htdocs
rsync -vre ssh . jseipp,rednotebook@web.sourceforge.net:htdocs
