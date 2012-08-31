#!/bin/sh
#ps2png script by Ian Hutchinson 1999; use at your own risk.
#You need Ghostscript and the netpbm utilities installed. 
if [ $# -lt 2 ] ; then
       echo " Usage: ps2png <file.ps> <file.png> [<icon.png>]" 1>&2
       exit 1
else 
    echo "Calling ghostscript to convert, please wait ..." >&2
    filein=$1
# The following uses the internal gs driver but does no cropping etc.
    gs -sDEVICE=png256 -sOutputFile=$2 -sNOPAUSE -q $filein -c showpage -c quit
    # gs -sDEVICE=ppmraw -sOutputFile=- -sNOPAUSE -q $filein -c showpage -c quit | pnmcrop| pnmmargin -white 10 | pnmtopng >$2
    shift 2
    if [ $# -eq 1 ] ;then
# Make an icon file.
       gs -sDEVICE=ppmraw -sOutputFile=- -sNOPAUSE -r12 -q $filein -c showpage -c quit | pnmcrop|  pnmtopng >$1
    fi
fi

