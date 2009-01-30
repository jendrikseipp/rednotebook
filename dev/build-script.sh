#!/bin/bash
echo Please, enter the version number
read VERSION
echo "Hi $VERSION!"

cd ../
sudo rm -r dist/

python setup.py sdist
python setup.py bdist_rpm

cd dist/
sudo alien -gk rednotebook-$VERSION-1.noarch.rpm
sudo cp ../debian/control rednotebook-$VERSION/debian/
cd rednotebook-$VERSION
sudo debian/rules binary
cd ../

#Move files
cp -f rednotebook_$VERSION-1_all.deb ../releases/
cp -f rednotebook-$VERSION.tar.gz ../releases/

cd ../releases/

rsync -avP -e ssh rednotebook_$VERSION-1_all.deb rednotebook-$VERSION.tar.gz jseipp@frs.sourceforge.net:uploads/



