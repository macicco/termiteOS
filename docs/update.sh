#!/bin/bash
make clean
cd ../../termiteOSdocs
git clone -b gh-pages --single-branch git@github.com:nachoplus/termiteOS.git html
cd ../termiteOS/docs
make html
make latexpdf
cd ../../termiteOSdocs/html
cp ../latex/termiteOS.pdf .
pwd
git add .
git commit -a -m "Updated documentation"
git push origin gh-pages
cd ../../termiteOS/docs
