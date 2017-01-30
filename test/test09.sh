#!/bin/bash
#
# Create two branches and two tags.
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
    
    echo 'B' >>$Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - second'"
    
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
    
    runcmd echo 'D' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchA - second'"
    
    runcmd echo 'E' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchA - third'"
    
    runcmd echo 'F' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchA - fourth'"
    
    runcmd git checkout master
    runcmd git checkout -b branchB
    runcmd echo 'G' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - first'"
    
    runcmd echo 'H' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - second'"
    
    runcmd echo 'I' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - third'"
    
    runcmd echo 'J' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - fourth'"
    runcmd git tag -a 'v2.0a' -m "'Initial version.'"
    
    runcmd echo 'K' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - fifth'"
    
    runcmd echo 'L' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - sixth'"
    
    runcmd echo 'M' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'branchB - seventh'"
    
    runcmd git checkout master
    runcmd echo 'N' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - third'"

    runcmd echo 'O' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - fourth'"
fi

# ================================================================
# Report.
# ================================================================
echo ""
Purpose="3 branches, tags and branches, choose"
runcmd ../git2dot.py \
       $KeepOpt \
       -v \
       -v \
       -w 19 \
       --choose-branch 'branchA' \
       --choose-branch 'branchB' \
       --choose-branch 'branchC' \
       -l "'%s|%ci'" \
       -L "'graph[label=<<table border=\"0\"><tr><td border=\"1\" align=\"left\" balign=\"left\" bgcolor=\"lightyellow\"><font face=\"courier\" point-size=\"9\">Test:    $Name<br/>Purpose: $Purpose<br/>Dir:     $(pwd)<br/>Date:    $(date)</font></td></tr></table>>]'" \
       --png \
       --svg \
       --html $Name.html \
       --html-head "'<script src="svg-pan-zoom.min.js"></script>'" \
       $Name.dot

Finish
info 'done'
