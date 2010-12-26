#! /bin/bash
cd ../web
#scp -r . jseipp,rednotebook@web.sourceforge.net:htdocs
rsync -re ssh . jseipp,rednotebook@web.sourceforge.net:htdocs
