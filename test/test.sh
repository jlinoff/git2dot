#!/bin/bash
#
# Run all of the tests.
#

# ================================================================
# Functions
# ================================================================
function Fail() {
    (( Failed++ ))
    (( Total++ ))
    local Tid="$1"
    local Memo="$2"
    printf "test:%03d:%s:failed %s\n" $Total "$Tid" "$Memo"
}

function Pass() {
    (( Passed++ ))
    (( Total++ ))
    local Tid="$1"
    local Memo="$2"
    printf "test:%03d:%s:passed %s\n" $Total "$Tid" "$Memo"
}

# ================================================================
# Main
# ================================================================
Passed=0
Failed=0
Total=0

for t in $(ls -1 test[0-9][0-9]*.sh) ; do
    Test=$(echo "$t" | sed -e 's/\.sh//')
    n=0
    Log=$Test.log
    ./$t false > $Log 2>&1
    st=$?
    if (( $st )) ; then
        Fail $Test "Run failed with status $st - see $Log"
    else
        Pass $Test "Run passed"
        (( n++ ))
    fi

    # Filter out the date info.
    DiffLog=$Test.difflog
    grep -v 'graph\[label' $Test.dot > $Test.dot.filter
    grep -v 'graph\[label' $Test.dot.gold > $Test.dot.gold.filter
    diff $Test.dot.filter $Test.dot.gold.filter > $DiffLog 2>&1
    st=$?
    if (( $st )) ; then
        Fail $Test "Diff failed with status $st - see $DiffLog"
    else
        Pass $Test "Diff passed"
        (( n++ ))
    fi

    if (( n == 2 )) ; then
        # Everything passed - clean up.
        rm -f $Log $DiffLog $Test.dot $Test.dot.png $Test.dot.svg $Test.txt $Test.html $Test.*.filter
    fi
done

echo
printf "test:total:passed  %3d\n" $Passed
printf "test:total:failed  %3d\n" $Failed
printf "test:total:summary %3d\n" $Total

echo
if (( Failed )) ; then
    echo "FAILED"
else
    echo "PASSED"
fi
exit $Failed
