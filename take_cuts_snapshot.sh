#!/bin/bash
RSYNC=/usr/bin/rsync
RSYNCARGS="-c -a "

print_usage(){
    echo "Usage: $0 <source_dir> <dest_dir> [<label>]"
    exit 1
}

if [ $# -ne 2 ] && [ $# -ne 3 ] ; then
    print_usage
fi

SOURCE=$1
DEST=$2
if [ ! -d $SOURCE ] || [ ! -d $DEST ] ; then
    echo "ERROR: $SOURCE or $DEST is not a directory!"
    print_usage
fi

LABEL=$3
if [ -z "$LABEL" ] ; then
    LABEL=`/bin/date "+%y%m%d"`
fi

#remove the destination dated directory if it already exists
if [ -d $DEST/$LABEL ] ; then  
    echo "Removing existing directory $DEST/$LABEL..."
    rm -rf $DEST/$LABEL
fi

#look for an existing directory to hard link against
LINKDEST=`ls -tC $DEST/ | awk '{print $1}'`
LINKDESTCMD="--link-dest=${DEST}/${LINKDEST}"
if [ -z "$LINKDEST" ] ; then
    LINKDESTCMD=""
fi

#perform the sync
echo "Syncing $SOURCE to $DEST/$LABEL..."
CMD="$RSYNC $RSYNCARGS $LINKDESTCMD $SOURCE/ $DEST/$LABEL/"
echo "rsync cmd is $CMD"
$CMD

retval=$?
if [ $retval -ne 0 ] ; then
    echo "There was an error $retval with the snapshot!"
    exit $retval
else
    echo "Done!"
fi

exit 0
