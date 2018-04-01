import os
import numpy as np
import shutil
import random
import string
import pprint
import cv2
import json
import copy
import cProfile
import separateDuplicateFiles as dff
import glob

## Helper method that creates random test images and returns a list with the paths
def createRandomTestImages(basepath, width, height, start, count):
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    imagePaths = []
    for i in range(count):
        imgArr = (np.random.rand(width,height,3)*255).astype(np.uint8)
        # imgArr = np.empty([width, height, 3], dtype=np.uint8)
        # imgArr[:,:,:] = np.uint8(np.random.rand()*np.random.rand()*255)
        imagePaths.append(os.path.join(basepath, 'img_{}.png'.format(start + i)))
        cv2.imwrite(imagePaths[len(imagePaths) - 1], imgArr)
    return imagePaths

def main():
    base_path = '/tmp/profiler'
    # np.random.seed(0)
    # createRandomTestImages(base_path, 100, 100, 0, 10000 )
    # np.random.seed(0)
    # createRandomTestImages(base_path, 100, 100, 10000, 10000 )
    # images = glob.glob('/tmp/profiler/*.png')
    # filesMap = {dff.calculateMD5Hash(f) : f for f in images}
    # with open('/tmp/filesMap.json','w') as fw:
    #     json.dump({dff.calculateMD5Hash(f) : f for f in images}, fw, indent=1)
    filesMap = {}
    inputFiles = dff.buildInputFilesList([base_path], {})
    dff.checkForDuplicates(inputFiles, filesMap)
    dff.moveTheDuplicates(filesMap, '/tmp/duplicates')

if __name__ == '__main__':
    main()