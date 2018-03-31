## Start by loading the knownFiles list
## Prepare the list of unique file paths
## Find duplicates using the hash
## move duplicates to duplicates folder
## the run should output [hash, originalFilePath, [duplciate 1 path, /duplicate 2 path, duplicate 3,....]]
## save this knownFiles list along with the hash [hash, original file path]
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
import pprint
makeDirLock = threading.Lock()


class File:
    def __init__(self, original, duplicates = []):
        self._original = original
        self._duplicates = duplicates

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
def loadKnownFilesMap(uniqueFilesMapFile):
    filesMap = {}
    with open(uniqueFilesMapFile) as fh:
        #filesMap = json.load(fh, object_hook=createFromJson)
        filesMap = json.load(fh)
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for filePath, present in zip(filesMap.values(), executor.map(path.exists, filesMap.values())):
                if not present:
                    print(filePath+" doesn't exist")

        filesMap = {k:File(v) for (k,v) in filesMap.items()}

    return filesMap

## creates and returns a list of all the file paths from the inputPaths that are not
## known(not present in knownFilesMap)
def buildInputFilesList(inputPaths, knownFilesMap):
    inputFiles = []
    knownFilesMap = knownFilesMap or {}
    knownFiles = [file._original for file in knownFilesMap.values()]

    for inputPath in inputPaths:
        if not path.exists(inputPath):
            raise OSError("Invalid input folder path : {}".format(inputPath))
        for root, dirs, files in walk(inputPath):
            # Within a directory, sort the files first by filename length and then by full filename
            # This helps us put 'img2025.png' before 'copy of img2025.png'
            files.sort(key=lambda x : (len(path.split(x)[-1]), path.split(x)[-1]))
            inputFiles.extend(img for img in [path.join(root, f) for f in files] if img not in inputFiles if img not in knownFiles)
            # Although dirs is not used directly, sorting the list of dirs here will make
            # os.walk to parse the directories in that order
            dirs.sort()

    return inputFiles

## Calculates the MD5 hash of a file
def calculateMD5Hash(file):
    with open(file, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()

## Given an input fileTupleList [(id3, file3), (1d1, file1), (id2, file2), (id0, file0)] for example,
## return file0, [file1, file2, file3]
def getOriginalAndDuplicates(fileTupleList):
    fileTupleList.sort()
    return fileTupleList[0][1], [x[1] for x in fileTupleList[1:]]

## find all the inputFiles that are already present in uniqueFilesMap and add them to the duplicateFilesMap
## all the new files frim teh inputFiles get added to uniqueFilesMap
def checkForDuplicates(inputFiles, filesMap):
    hashToFiles = {}
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # In order to preserve the order of the inputFiles we use enumerate(inputFiles) which returns tuples
        # of the form (index, inputFile) and combine that with the hash of the input file into a single tuple
        for (index, inputFile), md5Hash in zip(enumerate(inputFiles), executor.map(calculateMD5Hash, inputFiles)):
            if md5Hash in filesMap:
                filesMap[md5Hash].addDuplicate(inputFile)

            elif md5Hash in hashToFiles:
                hashToFiles[md5Hash].append((index, inputFile))

            else:
                hashToFiles[md5Hash] = [(index, inputFile)]

    # At this point we have files separated by hashes. The hashToFiles dictionary has md5Hash as the key
    # and a list of tuples (index, file) as value. Since which thread in the threadpool returns first is
    # not deterministic, we can use the index of the file for sorting each list in hashToFiles and pick
    # the top one (after sorting) as the original
    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        for md5Hash, (original, duplicates) in zip (hashToFiles.keys(), executor.map(getOriginalAndDuplicates, hashToFiles.values())):
            assert (md5Hash not in filesMap.keys())
            filesMap[md5Hash] = File (original, duplicates)

    # print(json.dumps(filesMap, default=lambda o : o.__dict__, indent=2))

## Moves the inputFile to the duplicatesFolder
def moveFile(inputFile, duplicatesFolder):
    try:
        ## To join two absolute paths, we need to remove the '/' from the beginning of the second path
        destFile = path.join(duplicatesFolder, inputFile[1:])
        destFolder = path.split(destFile)[0]

        # Delay acquiring a lock until necessary
        if (not path.exists(destFolder)):
            makeDirLock.acquire()
            ## Create the dest folder if necessary
            if (not path.exists(destFolder)):
                makedirs(destFolder)
            makeDirLock.release()

        shutil.move(inputFile, destFile)
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

#     uniqueFilesMap=loadKnownFilesMap(args.uniqueFilesMapFile)
#     print ('loadKnownFilesMap : {} files found'.format(len(uniqueFilesMap)))
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