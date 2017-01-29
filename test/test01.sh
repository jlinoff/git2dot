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
    Input=""
    runcmd git init
    
    echo 'A' >$Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - first'"
    
    echo 'B' >>$Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - second'"
    
    # tag the basis for all of the branches
    runcmd git tag -a 'v0.1' -m "'Initial version.'"
    
    runcmd git checkout master
    runcmd echo 'L' '>>' $Name.txt
    runcmd git add $Name.txt
    runcmd git commit -m "'master - third'"
fi

# ================================================================
# Report.
# ================================================================
echo ""
Purpose="3 commits on master, 1 tag"
runcmd ../git2dot.py \
       $KeepOpt \
       -v \
       -v \
       -w 19 \
       -l "'%h|%s|%ci'" \
       -L "'graph[label=<<table border=\"0\"><tr><td border=\"1\" align=\"left\" balign=\"left\" bgcolor=\"lightyellow\"><font face=\"courier\" point-size=\"9\">Test:    $Name<br/>Purpose: $Purpose<br/>Dir:     $(pwd)<br/>Date:    $(date)</font></td></tr></table>>]'" \
       --png \
       --svg \
       --html $Name.html \
       --html-head "'<script src="svg-pan-zoom.min.js"></script>'" \
       $Name.dot

Finish
info 'done'

