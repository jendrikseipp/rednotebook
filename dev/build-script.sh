#!/bin/bash
echo Please, enter the version number
read VERSION
echo "Hi $VERSION!"

cd ../
#sudo rm -r dist/
rm -r dist/

# Force recalculation of files so that none is missed
rm MANIFEST 

python setup.py sdist

if [ -d releases/ ]; then
    # directory exists
    echo "releases dir exists"
else
    # make dir
    mkdir releases/
fi

#Move files
cp -f dist/rednotebook-$VERSION.tar.gz releases/

cd releases/

# Example: rsync -avP -e ssh FILE jsmith,fooproject@frs.sourceforge.net:/home/frs/project/f/fo/fooproject/Rel_1/
#rsync -avP -e ssh rednotebook_$VERSION-1_all.deb rednotebook-$VERSION.tar.gz jseipp@frs.sourceforge.net:uploads/
#rsync -avP -e ssh rednotebook-$VERSION.tar.gz jseipp@frs.sourceforge.net:uploads/
#rsync -avP -e ssh rednotebook-$VERSION.tar.gz jseipp,rednotebook@frs.sourceforge.net:/home/frs/project/r/re/rednotebook/


