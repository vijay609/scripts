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


class File:
    def __init__(self, original):
        self._original = original
        self._duplicates = []

    def addDuplicate(self, duplicate):
        self._duplicates.append(duplicate)

## This method will get called for json deserialization for every json block
## from innermost level to outermost level.
def createFromJson(jsonObject):
    if '_original' in jsonObject and '_duplicates' in jsonObject :
        f = File(jsonObject['_original'])
        f._duplicates = jsonObject['_duplicates']
        return f
    elif type(list(jsonObject.values())[0]) is File:
        filesmap = {}
        for k,v in jsonObject.items():
            filesmap[k] = v
        return filesmap
    else:
        raise JSONDecodeError(msg='unexpected json', doc=json.dumps(jsonObject, default=lambda o : o.__dict__), pos=0)

## loads the file paths and hashes that are previously known
## also ensures that all those files are actually present on the disk
def loadUniqueFilesMap(uniqueFilesMapFile):
    filesMap = {}
    with open(uniqueFilesMapFile) as fh:
        #filesMap = json.load(fh, object_hook=createFromJson)
        filesMap = json.load(fh)
        filesMap = {k:File(v) for (k,v) in filesMap.items()}
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Start the load operations and mark each future with its URL
            future_to_file = {executor.submit(path.exists, inputFile._original): inputFile for inputFile in filesMap.values()}
            for future in concurrent.futures.as_completed(future_to_file):
                if (not future.result()):
                    raise OSError("File not found : {}".format(future_to_file[future]))

    return filesMap

## creates and returns a list of all the file paths from the inputPaths that are not
## known(not present in uniqueFilesMap)
def buildInputFilesList(inputPaths, uniqueFilesMap):
    inputFiles = []
    uniqueFilesMap = uniqueFilesMap or {}
    knownFiles = [file._original for file in uniqueFilesMap.values()]

    for inputPath in inputPaths:
        if not path.exists(inputPath):
            raise OSError("Invalid input folder path : {}".format(inputPath))
        for root, dirs, files in walk(inputPath):
            # Sort the files first by length and then by filename
            files.sort(key=lambda x : (len(path.split(x)[-1]), path.split(x)[-1]))
            inputFiles.extend(img for img in [path.join(root, f) for f in files] if img not in inputFiles if img not in knownFiles)
    return inputFiles

def calculateMD5Hash(file):
    with open(file, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()

## find all the inputFiles that are already present in uniqueFilesMap and add them to the duplicateFilesMap
## all the new files frim teh inputFiles get added to uniqueFilesMap
def checkForDuplicates(inputFiles, filesMap):
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        future_to_file = {executor.submit(calculateMD5Hash, inputFile): inputFile for inputFile in inputFiles}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            md5Hash = future.result()
            if md5Hash in filesMap:
                filesMap[md5Hash].addDuplicate(file)
            else:
                filesMap[md5Hash] = File(file)

## Moves the inputFile to the duplicatesFolder
def moveFile(inputFile, duplicatesFolder):
    try:
        ## To join two absolute paths, we need to split the second path into its components and path
        ## that as an expanded list
        destFolder = path.join(duplicatesFolder, *path.normpath(path.dirname(inputFile)).split(sep))

        if (not path.exists(destFolder)):
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

## moves all the duplicates from the filesMap to duplicatesDestRoot folder and preserves
## the original directory structure
def moveTheDuplicates(filesMap, duplicatesDestRoot):
    ## List comprehension to combine list of lists
    allDuplicateFiles = [f for dupFiles in filesMap.values() for f in dupFiles._duplicates]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(moveFile, duplicateFile, duplicatesDestRoot): duplicateFile for duplicateFile in allDuplicateFiles}
        done, notDone = concurrent.futures.wait(future_to_file, timeout=0)
        while notDone:
            done, notDone = concurrent.futures.wait(future_to_file, timeout=5)
            print('Moving Files..... done {} not done {}'.format(len(done), len(notDone)))

    for f in filesMap.values():
        ## Two absolute paths cannot be joined using os.path.join, the '/' in front of the second path needs to be omitted
        newDuplicatesList = [path.join(duplicatesDestRoot, df[1:]) for df in f._duplicates if f._duplicates]
        f._duplicates = newDuplicatesList

## Saves the duplicate and unique files list in a json file
def saveFileList(uniqueFilesMap, uniqueFilesMapPath, duplicateFilesMap, duplicateFilesMapPath):
    duplicateFilesMapJson = json.JSONEncoder(sort_keys=True, indent=0).encode(duplicateFilesMap)
    with open(duplicateFilesMapPath, 'w') as jsonFile:
        jsonFile.write(duplicateFilesMapJson)


    uniqueFilesMapJson = json.JSONEncoder(sort_keys=True, indent=0).encode(uniqueFilesMap)
    with open(uniqueFilesMapPath, 'w') as jsonFile:
        jsonFile.write(uniqueFilesMapJson)

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-d','--duplicateFilesDestination',help="Path where all the duplicate files will by moved to", required=True)
#     parser.add_argument('-i', '--inputPaths', help='List of input paths to search', required=True, nargs='+')
#     parser.add_argument('-u', '--uniqueFilesMapFile', help='path to unique file paths json file. All the new files get added to this list', required=True)
#     parser.add_argument('-df', '--duplicateFilesMapFile', help='path to duplicate file paths json file. The file will be overwritten if it already exists', required=True)
#     args = parser.parse_args()


#     print ('duplicateFilesDestination : {}'.format(args.duplicateFilesDestination))
#     print ('inputPaths : {}'.format(args.inputPaths))
#     print ('uniqueFilesMapFile : {}'.format(args.uniqueFilesMapFile))
#     print ('duplicateFilesMapFile : {}'.format(args.duplicateFilesMapFile))

#     uniqueFilesMap=loadUniqueFilesMap(args.uniqueFilesMapFile)
#     print ('loadUniqueFilesMap : {} files found'.format(len(uniqueFilesMap)))
#     inputFiles = buildInputFilesList(args.inputPaths, uniqueFilesMap)
#     print ('buildInputFilesList : {} files found'.format(len(inputFiles)))
#     duplicateFilesMap = checkForDuplicates(inputFiles, uniqueFilesMap)
#     moveTheDuplicates(duplicateFilesMap, args.duplicateFilesDestination)
#     saveFileList(uniqueFilesMap, args.uniqueFilesMapFile, duplicateFilesMap, args.duplicateFilesMapFile)

# profileOutputFile = '/data/profile_{}'.format(time.strftime("%Y-%m-%d-%H-%M-%S"))
# cProfile.run('main()', profileOutputFile)
# import pstats
# p = pstats.Stats(profileOutputFile)
# p.sort_stats('cumulative').print_stats(10)
# # main()