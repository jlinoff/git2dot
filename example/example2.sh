#!/bin/bash
#
# This script generates the example data in the local directory.
# Note that is creates and then deletes a local git repository.
#
rm -rf .git

git init

echo 'A' >example2.txt
git add example2.txt
git commit -m 'master - first'
sleep 1

echo 'B' >>example2.txt
git add example2.txt
git commit -m 'master - second'
sleep 1

# tag the basis for all of the branches
git tag -a 'v1.0' -m 'Initial version.'
git tag -a 'v1.0a' -m 'Another version.'

git checkout -b branchX1
git checkout master
git checkout -b branchX2

git checkout master
git checkout -b branchA
echo 'C' >> example2.txt
git add example2.txt
git commit -m 'branchA - first'
sleep 1

echo 'D' >> example2.txt
git add example2.txt
git commit -m 'branchA - second'
sleep 1

echo 'E' >> example2.txt
git add example2.txt
git commit -m 'branchA - third'
sleep 1

echo 'F' >> example2.txt
git add example2.txt
git commit -m 'branchA - fourth'
sleep 1

git checkout master
git checkout -b branchB
echo 'G' >> example2.txt
git add example2.txt
git commit -m 'branchB - first'
sleep 1

echo 'H' >> example2.txt
git add example2.txt
git commit -m 'branchB - second'
sleep 1

echo 'I' >> example2.txt
git add example2.txt
git commit -m 'branchB - third'
sleep 1

echo 'J' >> example2.txt
git add example2.txt
git commit -m 'branchB - fourth'
sleep 1
git tag -a 'v2.0a' -m 'Initial version.'

echo 'K' >> example2.txt
git add example2.txt
git commit -m 'branchB - fifth'
sleep 1

echo 'L' >> example2.txt
git add example2.txt
git commit -m 'branchB - sixth'
sleep 1

echo 'M' >> example2.txt
git add example2.txt
git commit -m 'branchB - seventh'
sleep 1

git checkout master
echo 'N' >> example2.txt
git add example2.txt
git commit -m 'master - third'
sleep 1

echo 'O' >> example2.txt
git add example2.txt
git commit -m 'master - fourth'

../git2dot.py --graph-label 'graph[label="example2 - full initial state"]' --png --svg --html example2-1.html example2-1.dot
../git2dot.py --graph-label 'graph[label="example2 - compressed initial state"]' --crunch --squash --png --svg --html example2-2.html example2-2.dot
../git2dot.py --graph-label 'graph[label="example2 - full pruned state"]' --choose-branch 'branchA' --choose-tag 'tag: v2.0a' --png --svg --html example2-3.html example2-3.dot
../git2dot.py --graph-label 'graph[label="example2 - compressed pruned state"]' --choose-branch 'branchA' --choose-tag 'tag: v2.0a' --crunch --squash --png --svg --html example2-4.html example2-4.dot

osType=$(uname)
case "$osType" in
    Darwin)
        open -a Preview example2-1.dot.png
        open -a Preview example2-2.dot.png
        open -a Preview example2-3.dot.png
        open -a Preview example2-4.dot.png
        ;;
    Linux)
        display example2-1.dot.png
        display example2-2.dot.png
        display example2-3.dot.png
        display example2-4.dot.png
        ;;
    *)
        ;;
esac

cat <<EOF

Example2 data has been created.

To access the graphs, start the server:

   \$ # Start the server
   \$ ./webserver.py 8090

Then navigate to the following URLs in your favorite browser.

   http://localhost:8090/example2-1.html
   http://localhost:8090/example2-2.html
   http://localhost:8090/example2-3.html
   http://localhost:8090/example2-4.html

EOF

rm -rf .git
