#! /bin/bash
cd ../web/src
python spider.py
cd ../
#scp -r . jseipp,rednotebook@web.sourceforge.net:htdocs
rsync -vre ssh . jseipp,rednotebook@web.sourceforge.net:htdocs
