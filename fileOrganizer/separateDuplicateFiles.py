'''
Start by loading the knownFiles list
Prepare the list of known file paths
Find duplicates using the hash
move duplicates to duplicates folder
the run should output [hash, originalFilePath, [duplciate 1 path, /duplicate 2 path, duplicate 3,....]]
save this knownFiles list along with the hash [hash, original file path]
'''

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
import multiprocessing
import pstats
makeDirLock = threading.Lock()

class File:
    def __init__(self, original, duplicates=None):
        self._original = original
        self._duplicates = [] if duplicates is None else duplicates

    def addDuplicate(self, duplicate):
        self._duplicates.append(duplicate)

'''
This method will get called for json deserialization for every json block
from innermost level to outermost level.
'''
def createFromJson(jsonObject):
    if '_original' in jsonObject and '_duplicates' in jsonObject :
        f = File(jsonObject['_original'], jsonObject['_duplicates'])
        return f
    elif type(list(jsonObject.values())[0]) is File:
        filesmap = {}
        for k,v in jsonObject.items():
            filesmap[k] = v
        return filesmap
    else:
        raise JSONDecodeError(msg='unexpected json', doc=json.dumps(jsonObject, default=lambda o : o.__dict__), pos=0)

'''
loads the file paths and hashes that are previously known
also ensures that all those files are actually present on the disk
'''
def loadKnownFilesMap(knownFilesMapFile):
    filesMap = {}
    with open(knownFilesMapFile) as fh:
        #filesMap = json.load(fh, object_hook=createFromJson)
        filesMap = json.load(fh)

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for filePath, present in zip(filesMap.values(), executor.map(path.exists, filesMap.values())):
            if not present:
                print('Not found : {}'.format(filePath))
            #     raise OSError("Invalid file path : {}".format(filePath))

    filesMap = {k:File(v) for (k,v) in filesMap.items()}

    return filesMap

'''
creates and returns a list of all the file paths from the inputPaths that are not
known(not present in knownFilesMap)
'''
def buildInputFilesList(inputPaths, knownFilesMap):
    if type(inputPaths) is not list:
        raise TypeError("buildInputFilesList expects a list of input paths")

    inputFiles = []
    knownFilesMap = knownFilesMap or {}
    knownFiles = [file._original for file in knownFilesMap.values()]

    for inputPath in inputPaths:
        if not path.exists(inputPath):
            raise OSError("Invalid input folder path : {}".format(inputPath))
        for root, dirs, files in walk(inputPath):
            '''Within a directory, sort the files first by filename length and then by full filename
            This helps us put 'img2025.png' before 'copy of img2025.png'
            '''
            files.sort(key=lambda x : (len(path.split(x)[-1]), path.split(x)[-1]))
            inputFiles.extend(img for img in [path.join(root, f) for f in files] if img not in inputFiles if img not in knownFiles)
            '''
            Although dirs is not used directly, sorting the list of dirs here will make
            os.walk to parse the directories in that order
            '''
            dirs.sort(reverse=True)

    return inputFiles

'''
Calculates the MD5 hash of a file
'''
def calculateMD5Hash(file):
    with open(file, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()

'''
Given an input fileTupleList [(id3, file3), (1d1, file1), (id2, file2), (id0, file0)] for example,
return file0, [file1, file2, file3]
'''
def getOriginalAndDuplicates(fileTupleList):
    fileTupleList.sort()
    return fileTupleList[0][1], [x[1] for x in fileTupleList[1:]]

'''
find all the inputFiles that are already present in knownFilesMap and add them to the duplicateFilesMap
all the new files frim teh inputFiles get added to knownFilesMap
'''
def checkForDuplicates(inputFiles, filesMap):
    hashToFiles = {}
    numDuplicates = 0
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ProcessPoolExecutor() as executor:
        '''In order to preserve the order of the inputFiles we use enumerate(inputFiles) which returns tuples
        of the form (index, inputFile) and combine that with the hash of the input file into a single tuple
        '''
        # optimal number of chunks should be same as the number of processors/cores 
        for (index, inputFile), md5Hash in zip(enumerate(inputFiles), executor.map(calculateMD5Hash, inputFiles, chunksize=len(inputFiles)//multiprocessing.cpu_count())):
            if md5Hash in filesMap:
                filesMap[md5Hash].addDuplicate(inputFile)
                numDuplicates += 1

            elif md5Hash in hashToFiles:
                hashToFiles[md5Hash].append((index, inputFile))
                numDuplicates += 1

            else:
                hashToFiles[md5Hash] = [(index, inputFile)]

    '''
    At this point we have files separated by hashes. The hashToFiles dictionary has md5Hash as the key
    and a list of tuples (index, file) as value. Since which thread in the threadpool returns first is
    not deterministic, we can use the index of the file for sorting each list in hashToFiles and pick
    the top one (after sorting) as the original'''
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for md5Hash, (original, duplicates) \
            in zip (hashToFiles.keys(), executor.map(getOriginalAndDuplicates, hashToFiles.values())):
            assert (md5Hash not in filesMap.keys())
            filesMap[md5Hash] = File (original, duplicates)

    return numDuplicates
    # print(json.dumps(filesMap, default=lambda o : o.__dict__, indent=2))

def moveFile(srcFile, destFile):
    try:
        destFolder = path.split(destFile)[0]

        # Delay acquiring a lock until necessary
        if (not path.exists(destFolder)):
            makeDirLock.acquire()
            ## Create the dest folder if necessary
            if (not path.exists(destFolder)):
                makedirs(destFolder)
            makeDirLock.release()

        shutil.move(srcFile, destFile)
    except:
        logging.exception("")
        raise

'''
moves all the duplicates from the filesMap to duplicatesDestRoot folder and preserves
the original directory structure
'''
def moveTheDuplicates(filesMap, duplicatesDestRoot):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        moveFileFutures = []
        for v in filesMap.values():
            for i in range(len(v._duplicates)):
                srcFile = v._duplicates[i]
                destFile = path.join(duplicatesDestRoot, srcFile[1:])
                v._duplicates[i] = destFile
                moveFileFutures.append(executor.submit(moveFile, srcFile, destFile))

        done, notDone = concurrent.futures.wait(moveFileFutures, timeout=0)
        while notDone:
            done, notDone = concurrent.futures.wait(moveFileFutures, timeout=5)
            print('Moving Files..... done {} not done {}'.format(len(done), len(notDone)))


## Saves the duplicate and known files list in a json file
def saveFileList(filesMap, knownFilesMapPath, allFilesMapPath):
    with open(knownFilesMapPath, 'w') as fw:
        json.dump(filesMap, fw, default=lambda o : o._original, indent=1)
    with open(allFilesMapPath, 'w') as fw:
        json.dump(filesMap, fw, default=lambda o : o.__dict__, indent=1)

def main():
    timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--duplicateFilesDestination',help="Path where all the duplicate files will by moved to", required=True)
    parser.add_argument('-i', '--inputPaths', help='List of input paths to search', required=True, nargs='+')
    parser.add_argument('-k', '--knownFilesMapFile', help='path to known file paths json file.')
    parser.add_argument('-l', '--logDirectory', help='path to the logs directory where the new filesMap will be written to', required=True)
    args = parser.parse_args()


    print ('duplicateFilesDestination : {}'.format(args.duplicateFilesDestination))
    print ('inputPaths : {}'.format(args.inputPaths))
    print ('knownFilesMapFile : {}'.format(args.knownFilesMapFile))
    print ('logDirectory : {}'.format(args.logDirectory))

    pr = cProfile.Profile()

    profileOutputFile = path.join(args.logDirectory, 'profile_{}'.format(timestr))
    # Start Profiling
    pr.enable()
    filesMap = loadKnownFilesMap(args.knownFilesMapFile) if args.knownFilesMapFile is not None else {}
    print ('loadKnownFilesMap : {} files found'.format(len(filesMap)))
    inputFiles = buildInputFilesList(args.inputPaths, filesMap)
    print ('buildInputFilesList : {} files found'.format(len(inputFiles)))
    numDuplicates = checkForDuplicates(inputFiles, filesMap)
    print ('{} duplicates found'.format(numDuplicates))

    moveTheDuplicates(filesMap, args.duplicateFilesDestination)
    print ('done moving duplicates')
    if path.isabs(args.logDirectory) and not path.exists(args.logDirectory):
        makedirs(args.logDirectory)
    print ('writing logs')
    knownFilesMapFile = path.join(args.logDirectory, 'knownFiles_{}.json'.format(timestr))
    allFilesMapFile = path.join(args.logDirectory, 'allFiles_{}.json'.format(timestr))
    saveFileList(filesMap, knownFilesMapFile, allFilesMapFile)
    pr.disable()
    # Stop Profiling
    pr.dump_stats(profileOutputFile)
    p = pstats.Stats(profileOutputFile)
    p.sort_stats('cumulative').print_stats(10)

if __name__ == '__main__':
    main()
