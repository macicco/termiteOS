#!/bin/bash
make html
cd ../../termiteOSdocs/html
git add .
git commit -a -m "Updated documentation"
git push origin gh-pages
cd ../../termiteOS/docs
