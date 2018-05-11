import os
import json
import separateDuplicateFiles
import shutil

# allFiles = '/media/vijay/Data/Pictures/logs/allFiles_2018-04-27-23-14-49.json_'
allFiles = '/media/vijay/Data/Pictures/logs/allFiles_2018-04-27-21-21-33.json'
safeOriginals = '/media/vijay/Data/Pictures/organize/'
removedFilesFile = '/media/vijay/Data/Pictures/logs/removedFiles_allFiles_2018-04-27-21-21-33.json'


def main():
    filesMap = {}
    with open(allFiles) as fh:
        filesMap = json.load(fh, object_hook=separateDuplicateFiles.createFromJson)

    removedFilesList = []
    print(len(filesMap))
    for f in filesMap.values():
        if f._original.startswith(safeOriginals):
            for d in f._duplicates:
                if safeOriginals not in d:
                    removedFilesList.append(d)
                    if os.path.exists(d): 
                        os.remove(d) 

    with open(removedFilesFile,'w') as fh:
        filesMap = json.dump(removedFilesList, fh, indent=1)

    # mistakeDeletion = []
    # count = 0
    # for f in filesMap.values():
    #     for d in f._duplicates:
    #         if safeOriginals in d:
    #             mistakeDeletion.append((f._original, d))
    #             if not os.path.exists(os.path.dirname(d)) :
    #                 os.makedirs(os.path.dirname(d))
    #             shutil.copyfile(f._original, d)
                    
    #             count += 1
    # print(count)

    # with open('/media/vijay/Data/Pictures/logs/mistakeDeletion.json','w') as fh:
    #     json.dump(mistakeDeletion, fh, indent=1)
if __name__ == '__main__':
    main()