#!/bin/bash

# python ./separateDuplicateFiles.py -u /src/data/knownFiles.json \
#     -df /src/data/duplicateFiles.json \
#     -d /src/data/duplicates \
#     -i /src/data/test1 /src/data/test2

# python ./separateDuplicateFiles.py -u /media/vijay/Data/Pictures/logs/knownFiles.json \
#     -df /media/vijay/Data/Pictures/logs/duplicateFiles.json \
#     -d /media/vijay/Data/Pictures/duplicates \
#     -i /media/vijay/Data/Pictures/organize /media/vijay/Data/Pictures/staging

## After refactor
# python ./separateDuplicateFiles.py \
#     -d /tmp/duplicates \
#     -i /tmp/profiler \
#     -l /tmp/logs \

#python ./separateDuplicateFiles.py \
    #-d /media/vijay/Data/Pictures/duplicates \
    #-i /media/vijay/Data/Pictures/organize /media/vijay/Data/Pictures/staging \
    #-l /media/vijay/Data/Pictures/logs

# python ./separateDuplicateFiles.py \
#     -d /media/vijay/Data/Pictures/duplicates \
#     -i /media/vijay/Data/Pictures/staging /media/vijay/FACEAFABCEAF5E9F/101ND750 /media/vijay/FACEAFABCEAF5E9F/2015_07_10_Shanthi_Babyshower \
#         /media/vijay/FACEAFABCEAF5E9F/2016_09_18_Srihan_Birthday /media/vijay/FACEAFABCEAF5E9F/backedupPicsFromVibbhu /media/vijay/FACEAFABCEAF5E9F/backup3 \
#         /media/vijay/FACEAFABCEAF5E9F/phonePics /media/vijay/FACEAFABCEAF5E9F/uniqueFiles /media/vijay/FACEAFABCEAF5E9F/uniqueFiles_ /media/vijay/FACEAFABCEAF5E9F/vbaiyyacarbon/IndiaTrip2017pic \
#     -k /media/vijay/Data/Pictures/logs/knownFiles_2018-04-04-13-00-56.json \

# python ./separateDuplicateFiles.py \
#     -d /media/vijay/Data/Pictures/duplicates \
#     -i /media/vijay/FACEAFABCEAF5E9F/101ND750/ \
#     -k /media/vijay/Data/Pictures/logs/knownFiles_2018-04-08-05-28-38.json \
#     -l /media/vijay/Data/Pictures/logs

# sleep 3600

#python ./separateDuplicateFiles.py \
    #-d /media/vijay/Media1/duplicates/ \
    #-i /media/vijay/Data/Pictures/organize \
        #/media/vijay/Data/Pictures/staging \
        #/media/vijay/FACEAFABCEAF5E9F/Pictures_need_sorting \
        #/media/vijay/Data/Pictures/maybeDuplicates \
        #/media/vijay/FACEAFABCEAF5E9F/maybeDuplicates \
        #/media/vijay/Data/Pictures/duplicates \
        #/media/vijay/FACEAFABCEAF5E9F/duplicates \
    #-l /media/vijay/Data/Pictures/logs

#python ./separateDuplicateFiles.py \
#    -d /media/vijay/FACEAFABCEAF5E9F/duplicates \
#    -i /media/vijay/Data/Pictures/organize \
#        /media/vijay/Data/Pictures/staging \
#        /media/vijay/FACEAFABCEAF5E9F/Pictures_need_sorting \
#    -l /media/vijay/Data/Pictures/logs

#python ./separateDuplicateFiles.py \
#    -d /media/vijay/FACEAFABCEAF5E9F/duplicates \
#    -i /media/vijay/Data/Pictures/maybeDuplicates \
#        /media/vijay/Data/Pictures/duplicates \
#        /media/vijay/FACEAFABCEAF5E9F/maybeDuplicates \
#    -l /media/vijay/Data/Pictures/logs \
#    -k /media/vijay/Data/Pictures/logs/knownFiles_2018-04-27-19-48-45.json

################### First set of duplicates are at /media/vijay/FACEAFABCEAF5E9F/duplicates 
################### Second set of duplicates will be  at /media/vijay/Media1/duplicates 
python ./separateDuplicateFiles.py \
    -d /media/vijay/Media1/duplicates \
    -i /media/vijay/Media1/maybeduplicates \
    -l /media/vijay/Data/Pictures/logs \
    -k /media/vijay/Data/Pictures/logs/knownFiles_2018-04-27-21-21-33.json
