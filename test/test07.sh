#!/bin/bash
#
# Verify that changeids processing works.
#

# ================================================================
# Includes
# ================================================================
Location="$(cd $(dirname $0) && pwd)"
source $Location/test-utils.sh

# ================================================================
# Create the repo.
# ================================================================
if (( Keep )) ; then
    runcmd git init

    echo 'A' >$Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - first'"
    runcmd sleep 1
    
    echo 'B' >>$Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - second'" -m "'Change-Id: I001'"
    runcmd sleep 1
    
    # tag the basis for all of the branches
    runcmd git tag -a 'v1.0' -m "'Initial version.'"
    runcmd git tag -a 'v1.0a' -m "'Another version.'"
    
    runcmd git checkout -b branchX1
    runcmd git checkout master
    runcmd git checkout -b branchX2
    
    runcmd git checkout master
    runcmd git checkout -b branchA
    runcmd echo 'C' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchA - first'"
    runcmd sleep 1
    
    runcmd echo 'B' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchA - second'" -m "'Change-Id: I001'"
    runcmd sleep 1
    
    runcmd git checkout master
    runcmd git checkout -b branchB
    runcmd echo 'E' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - first'"
    runcmd sleep 1
    
    runcmd echo 'F' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - second'"
    runcmd sleep 1
    
    runcmd echo 'B' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - third'" -m "'Change-Id: I001'"
    runcmd sleep 1
    
    runcmd echo 'H' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - fourth'" -m "'Change-Id: I002'"
    runcmd sleep 1
    
    runcmd echo 'I' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - fifth'"
    runcmd sleep 1
    
    runcmd echo 'J' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - sixth'"
    runcmd sleep 1
    
    runcmd echo 'K' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - seventh'"
    runcmd sleep 1
    
    runcmd git checkout master
    runcmd echo 'L' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - third'"
fi

# ================================================================
# Report.
# ================================================================
echo ""
Purpose="3 branches, no squash, tags and branches, splines=true, cnode and mnode"
runcmd ../git2dot.py \
       $KeepOpt \
       -v \
       -v \
       -w 19 \
       --cnode "'[label=\"{label}\", shape=\"diamond\", color=\"magenta\"]'" \
       --mnode "'[label=\"{label}\", shape=\"diamond\", color=\"green\"]'" \
       -D '@CHID@' "'Change-Id: I([a-z0-9]+)'" \
       -l "'%s|%ci|@CHID@'" \
       -L "'graph[label=<<table border=\"0\"><tr><td border=\"1\" align=\"left\" balign=\"left\" bgcolor=\"lightyellow\"><font face=\"courier\" point-size=\"9\">Test:    $Name<br/>Purpose: $Purpose<br/>Dir:     $(pwd)<br/>Date:    $(date)</font></td></tr></table>>]'" \
       --html $Name.html \
       --dot-option "'splines=\"true\"'" \
       -s \
       --png \
       --svg \
       $Name.dot

Finish
info 'done'
