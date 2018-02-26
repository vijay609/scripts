## Start by loading the uniqueFiles list
## Prepare the list of unique file paths
## Find duplicates using the hash
## move duplicates to duplicates folder
## the run should output [hash, originalFilePath, [duplciate 1 path, /duplicate 2 path, duplicate 3,....]]
## save this uniqueFiles list along with the hash [hash, original file path]
import json
from os import walk, path, sep, makedirs

import concurrent.futures
import hashlib
import time
import shutil
import logging
import threading
import argparse
import cProfile
makeDirLock = threading.Lock()

## loads the file paths and hashes that are previously known
## also ensures that all those files are actually present on the disk
def loadUniqueFilesMap(uniqueFilesMapFile):
    uniqueFilesMap = json.load(open(uniqueFilesMapFile)) if path.exists(uniqueFilesMapFile) else {}
     # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        future_to_file = {executor.submit(path.exists, inputFile): inputFile for inputFile in uniqueFilesMap.values()}
        for future in concurrent.futures.as_completed(future_to_file):
            if (not future.result()):
                raise OSError("File not found : {}".format(future_to_file[future]))

    return uniqueFilesMap

## creates and returns a list of all the file paths from the inputPaths that are not
## known(not present in uniqueFilesMap)
def buildInputFilesList(inputPaths, uniqueFilesMap):
    inputFiles = []
    for inputPath in inputPaths:
        for root, dirs, files in walk(inputPath):
            inputFiles.extend(img for img in [path.join(root, f) for f in files] if img not in inputFiles if img not in uniqueFilesMap.values())
    return inputFiles

def calculateMD5Hash(file):
    fh = open(file, "rb")
    return hashlib.md5(fh.read()).hexdigest()

## find all the inputFiles that are already present in uniqueFilesMap and add them to the duplicateFilesMap
## all the new files frim teh inputFiles get added to uniqueFilesMap
def checkForDuplicates(inputFiles, uniqueFilesMap):
    duplicateFilesMap = {}
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        future_to_file = {executor.submit(calculateMD5Hash, inputFile): inputFile for inputFile in inputFiles}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            md5Hash = future.result()
            if md5Hash in uniqueFilesMap:
                if md5Hash in duplicateFilesMap:
                    duplicateFilesMap[md5Hash].append(file)
                else:
                    duplicateFilesMap[md5Hash] = [uniqueFilesMap[md5Hash], file]
            else:
                uniqueFilesMap[md5Hash] = file
    return duplicateFilesMap


## Moves the inputFile to the duplicatesFolder
def moveFile(inputFile, duplicatesFolder):
    try:
        ## To join two absolute paths, we need to split the second path into its components and path
        ## that as an expanded list
        destFolder = path.join(duplicatesFolder, *path.normpath(path.dirname(inputFile)).split(sep))

        makeDirLock.acquire()
        ## Create the dest folder if necessary
        if (not path.exists(destFolder)):
            makedirs(destFolder)
        makeDirLock.release()

        shutil.move(inputFile, path.join(destFolder, path.basename(inputFile)))
        #print (inputFile)
    except:
        logging.exception("")
        raise
        
## moves all the duplicates from the duplicateFilesMap to duplicatesDestRoot folder and preserves
## the original directory structure
def moveTheDuplicates(duplicateFilesMap, duplicatesDestRoot):
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        for duplicateFiles in duplicateFilesMap.values():
            if (len(duplicateFiles) > 1):
                future_to_file = {executor.submit(moveFile, duplicateFile, duplicatesDestRoot): duplicateFile for duplicateFile in duplicateFiles[1:]}
            else:
                raise Exception("how did you get a single file entry in duplicate files list?")
             
            
## Saves the duplicate and unique files list in a json file
def saveFileList(uniqueFilesMap, uniqueFilesMapPath, duplicateFilesMap, duplicateFilesMapPath):
    duplicateFilesMapJson = json.JSONEncoder(sort_keys=True, indent=0).encode(duplicateFilesMap)
    with open(duplicateFilesMapPath, 'w') as jsonFile:
        jsonFile.write(duplicateFilesMapJson)

   
    uniqueFilesMapJson = json.JSONEncoder(sort_keys=True, indent=0).encode(uniqueFilesMap)
    with open(uniqueFilesMapPath, 'w') as jsonFile:
        jsonFile.write(uniqueFilesMapJson)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--duplicateFilesDestination',help="Path where all the duplicate files will by moved to", required=True)
    parser.add_argument('-i', '--inputPaths', help='List of input paths to search', required=True, nargs='+')
    parser.add_argument('-u', '--uniqueFilesMapFile', help='path to unique file paths json file. All the new files get added to this list', required=True)
    parser.add_argument('-df', '--duplicateFilesMapFile', help='path to duplicate file paths json file. The file will be overwritten if it already exists', required=True)
    args = parser.parse_args()


    print (args.duplicateFilesDestination)
    print (args.inputPaths)
    print (args.uniqueFilesMapFile)
    print (args.duplicateFilesMapFile)
    
    uniqueFilesMap=loadUniqueFilesMap(args.uniqueFilesMapFile)
    inputFiles = buildInputFilesList(args.inputPaths, uniqueFilesMap)
    duplicateFilesMap = checkForDuplicates(inputFiles, uniqueFilesMap)
    moveTheDuplicates(duplicateFilesMap, args.duplicateFilesDestination)
    saveFileList(uniqueFilesMap, args.uniqueFilesMapFile, duplicateFilesMap, args.duplicateFilesMapFile)


# cProfile.run('main()')
main()