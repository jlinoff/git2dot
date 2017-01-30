#!/bin/bash
#
# This script generates the example data in the local directory.
# Note that is creates and then deletes a local git repository.
#
rm -rf .git

git init

echo 'A' >README
git add README
git commit -m 'master - first'
sleep 1

echo 'B' >>README
git add README
git commit -m 'master - second' -m 'Change-Id: I001'
sleep 1

# tag the basis for all of the branches
git tag -a 'v1.0' -m 'Initial version.'
git tag -a 'v1.0a' -m 'Another version.'

git checkout -b branchX1
git checkout master
git checkout -b branchX2

git checkout master
git checkout -b branchA
echo 'C' >> README
git add README
git commit -m 'branchA - first'
sleep 1

echo 'B' >> README
git add README
git commit -m 'branchA - second' -m 'Change-Id: I001'
sleep 1

git checkout master
git checkout -b branchB
echo 'E' >> README
git add README
git commit -m 'branchB - first'
sleep 1

echo 'F' >> README
git add README
git commit -m 'branchB - second'
sleep 1

echo 'B' >> README
git add README
git commit -m 'branchB - third' -m 'Change-Id: I001'
sleep 1

echo 'H' >> README
git add README
git commit -m 'branchB - fourth' -m 'Change-Id: I002'
sleep 1

echo 'I' >> README
git add README
git commit -m 'branchB - fifth'
sleep 1

echo 'J' >> README
git add README
git commit -m 'branchB - sixth'
sleep 1

echo 'K' >> README
git add README
git commit -m 'branchB - seventh'
sleep 1

git checkout master
echo 'L' >> README
git add README
git commit -m 'master - third'

git log --graph --oneline --decorate --all

../git2dot.py --png --svg --html example.html example.dot
../git2dot.py --squash --png --svg --html example1.html example1.dot
../git2dot.py --crunch --squash --png --svg --html example2.html example2.dot

osType=$(uname)
case "$osType" in
    Darwin)
        open -a Preview example.dot.png
        open -a Preview example1.dot.png
        open -a Preview example2.dot.png
        ;;
    Linux)
        display example.dot.png
        display example1.dot.png
        display example2.dot.png
        ;;
    *)
        ;;
esac

cat <<EOF

Example data has been created.

To access the graphs, start the server:

   \$ # Start the server
   \$ ./webserver.py 8090

Then navigate to the following URLs in your favorite browser.

   http://localhost:8090/example.html
   http://localhost:8090/example1.html   
   http://localhost:8090/example2.html   

EOF

rm -rf .git
