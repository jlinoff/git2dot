# Utilities used by the macports tools.

# ================================================================
# Functions
# ================================================================
# Print an info message with context (caller line number)
function info() {
    local Msg="$*"
    echo -e "INFO:${BASH_LINENO[0]}: $Msg"
}

# Print a warning message with context (caller line number)
function warn() {
    local Msg="$*"
    echo -e "WARNING:${BASH_LINENO[0]}: $Msg"
}

# Print an error message and exit.
function err() {
    local Msg="$*"
    echo -e "ERROR:${BASH_LINENO[0]}: $Msg"
    exit 1
}

# Run a command with decorations.
function runcmd() {
    local Cmd="$*"
    local LineNum=${BASH_LINENO[0]}
    echo
    echo "INFO:${LineNum}: cmd.run=$Cmd"
    eval "$Cmd"
    local st=$?
    echo "INFO:${LineNum}: cmd.status=$st"
    if (( st )) ; then
        echo "ERROR:${LineNum}: command failed"
        exit 1
    fi
}

# Run a command but allow the user to specify an acceptable
# return code range.
function runcmdst() {
    local Lower=$1
    local Upper=$2
    shift
    shift
    local Cmd="$*"
    local LineNum=${BASH_LINENO[0]}
    echo
    echo "INFO:${LineNum}: cmd.run=$Cmd"
    eval "$Cmd"
    local st=$?
    echo "INFO:${LineNum}: cmd.status=$st OK=[$Lower..$Upper]"
    if (( st < Lower )) || (( st > Upper )) ; then
        echo "ERROR:${LineNum}: command failed"
        exit 1
    fi
}

# Display a PNG file.
function displayPNG() {
    local osType=$(uname | tr '[:upper:]' '[:lower:]')
    case "$osType" in
        'darwin')
            runcmd open -a Preview $*
            ;;
        'linux')
            runcmd display $*
            ;;
        *)
            err "unknown OS '$osType'"
            ;;
    esac
}

function Finish() {
    # Popup the display.
    if (( $Display )) ; then
        displayPNG $Name.dot.png
    fi
    
    # Display the git data.
    if (( Keep )) ; then
        echo ""
        runcmd git log --graph --oneline --decorate --all
    fi
}

# ================================================================
# Pre-flight setup.
# ================================================================
Name=$(basename "$0" | cut -d. -f1)
Display=1
KeepFile="$Name.dot.keep"
KeepOpt="-i $Name.dot.keep"
Keep=0

# Force the test no matter what.
if [[ "$TEST_FORCE" == "1" ]] ; then
    rm -rf .git
    rm -f $KeepFile
fi

if [ ! -f "$KeepFile" ] ; then
    # Keep the data from this run which
    # means that the .git repo has to be
    # re-generated.
    KeepOpt="--keep"
    Keep=1
fi

if (( $# > 0 )) ; then
    arg1=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    case "$arg1" in
        f|false|0)
            Display=0
            ;;
        *)
            ;;
    esac
fi

if (( Keep )) ; then
    # We only care about the .git repo if
    # the user needs to generate the keep
    # data.
    if [ -d .git ] ; then
        err '.git exists, you must remove it to continue'
    fi
fi

