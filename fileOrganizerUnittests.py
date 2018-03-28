import os
import numpy as np
import shutil
import unittest
import random
import string
import pprint
import cv2
import json
import copy
import separateDuplicateFiles as dff

## Helper method that creates random test images and returns a list with the paths
def createRandomTestImages(basepath, width, height, start, count):
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    imagePaths = []
    for i in range(count):
        imgArr = (np.random.rand(width,height,3)*255).astype(np.uint8)
        imagePaths.append(os.path.join(basepath, 'img_{}.png'.format(start + i)))
        cv2.imwrite(imagePaths[len(imagePaths) - 1], imgArr)
    return imagePaths

## Unittest
class TestLoadUniqueFilesMap(unittest.TestCase):
    _testBasePath = os.path.join('/tmp', 'unittestdata')

    @classmethod
    def setUpClass(cls):
        np.random.seed(0)
        imagePaths = createRandomTestImages(cls._testBasePath, 10, 10, 0, 5)
        cls._simpleFilesMap1 = {dff.calculateMD5Hash(img): img for img in imagePaths}
        cls._simpleFilesMap1File = os.path.join(cls._testBasePath, 'filesmap1.json')
        with open(cls._simpleFilesMap1File, 'w') as fp:
            json.dump(cls._simpleFilesMap1, fp)

        imagePaths.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder1'), 10, 10, 0, 5))
        imagePaths.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder2'), 10, 10, 0, 5))
        imagePaths.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder1', 'folder3'), 10, 10, 0, 5))
        imagePaths.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder2', 'folder4'), 10, 10, 0, 5))
        cls._complexFilesMap1 = {dff.calculateMD5Hash(img): img for img in imagePaths}
        cls._complexFilesMap1File = os.path.join(cls._testBasePath, 'complexFilesMap.json')
        with open(cls._complexFilesMap1File, 'w') as fp:
            json.dump(cls._complexFilesMap1, fp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._testBasePath)

    def test_loadingSimpleUniqueFilesMapPasses(self):
        filesMap = dff.loadUniqueFilesMap(self._simpleFilesMap1File)
        filesMap = {k:v._original for (k,v) in filesMap.items()}
        sharedItems = set(filesMap.items()) \
                        & set (self._simpleFilesMap1.items())
        self.assertEqual(len(sharedItems), 5)

    def test_loadingSimpleUniqueFilesMapWithBadFileNameFails(self):
        key, value = self._simpleFilesMap1.popitem()
        self._simpleFilesMap1[key] = value+'1'
        filesMap = dff.loadUniqueFilesMap(self._simpleFilesMap1File)
        filesMap = {k:v._original for (k,v) in filesMap.items()}

        sharedItems = set(filesMap.items()) \
                        & set (self._simpleFilesMap1.items())
        self.assertNotEqual(len(sharedItems), 5)
        self.assertEqual(len(sharedItems), 4)

    def test_loadingComplexUniqueFilesMapPasses(self):
        filesMap = dff.loadUniqueFilesMap(self._complexFilesMap1File)
        filesMap = {k:v._original for (k,v) in filesMap.items()}
        sharedItems = set(filesMap.items()) \
                        & set (self._complexFilesMap1.items())
        self.assertEqual(len(sharedItems), 25)

class TestBuildInputFilesList(unittest.TestCase):
    _testBasePath = os.path.join('/tmp', 'unittestdata')

    @classmethod
    def setUpClass(cls):
        np.random.seed(0)
        cls._imagePaths = createRandomTestImages(cls._testBasePath, 10, 10, 0, 5)
        cls._imagePaths1 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder1'), 10, 10, 5, 5)
        cls._imagePaths2 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder2'), 10, 10, 10, 5)
        cls._imagePaths3 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder1', 'folder3'), 10, 10, 15, 5)
        cls._imagePaths4 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder2', 'folder4'), 10, 10, 20, 10)

        cls._knownFilesMap = {dff.calculateMD5Hash(f):dff.File(f) for f in cls._imagePaths}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._testBasePath)

    def test_buildInputFilesListReturnsEmptyListWhenNoPathsAreGivenAsInput(self):
        self.assertFalse(dff.buildInputFilesList([], {}))

    def test_buildInputFilesListWorksWhenSingleInputPathIsGiven(self):
        basepath = os.path.join(self._testBasePath, 'folder1', 'folder3')
        inputFilesList = dff.buildInputFilesList([basepath], None)
        self.assertEqual(len(inputFilesList), 5)
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(15 + i)), inputFilesList)

    def test_buildInputFilesListWorksWhenMultipleInputPathsAteGiven(self):
        inputFilesList = dff.buildInputFilesList([os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder2', 'folder4')], None)
        self.assertEqual(len(inputFilesList), 15)

        basepath = os.path.join(self._testBasePath, 'folder1', 'folder3')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(15 + i)), inputFilesList)

        basepath = os.path.join(self._testBasePath, 'folder2', 'folder4')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(20 + i)), inputFilesList)

    def test_buildInputFilesListWorksWhenSamePathIsRepeated(self):
        inputFilesList = dff.buildInputFilesList([
                os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder2', 'folder4'),
                os.path.join(self._testBasePath, 'folder2', 'folder4'),
                os.path.join(self._testBasePath, 'folder2', 'folder4'),
                ], None)
        self.assertEqual(len(inputFilesList), 15)

        basepath = os.path.join(self._testBasePath, 'folder1', 'folder3')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(15 + i)), inputFilesList)

        basepath = os.path.join(self._testBasePath, 'folder2', 'folder4')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(20 + i)), inputFilesList)

    def test_buildInputFilesListWorksWithNestedPath(self):
        inputFilesList = dff.buildInputFilesList([
                os.path.join(self._testBasePath, 'folder1', 'folder3'),
                os.path.join(self._testBasePath, 'folder1'),
                ], None)
        self.assertEqual(len(inputFilesList), 10)

        basepath = os.path.join(self._testBasePath, 'folder1', 'folder3')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(15 + i)), inputFilesList)

        basepath = os.path.join(self._testBasePath, 'folder1')
        for i in range(5):
            self.assertIn(os.path.join(basepath, 'img_{}.png'.format(5 + i)), inputFilesList)

    def test_buildInputFilesListFailsWithInvalidPath(self):
        with self.assertRaisesRegex(OSError, "Invalid input folder"):
            inputFilesList = dff.buildInputFilesList([
                    os.path.join(self._testBasePath, 'folder1', 'folder3'),
                    os.path.join(self._testBasePath, 'folder5'),
                    ], None)

    def test_buildInputFilesListDoesntReturnKnownFilePaths(self):
        inputFilesList = dff.buildInputFilesList([
            self._testBasePath,
            os.path.join(self._testBasePath, 'folder1'),
            os.path.join(self._testBasePath, 'folder2'),
            os.path.join(self._testBasePath, 'folder1', 'folder3'),
            os.path.join(self._testBasePath, 'folder2', 'folder4'),
        ], self._knownFilesMap)

        self.assertFalse(set(inputFilesList) & set(self._knownFilesMap.values()))

class TestCalculateMD5Hash(unittest.TestCase):
    _testBasePath = os.path.join('/tmp', 'unittestdata')

    @classmethod
    def setUpClass(cls):
        np.random.seed(0)
        cls._testImgs = createRandomTestImages(cls._testBasePath, 10, 10, 0, 1)
        # cls._testImgs.extend(createRandomTestImages(cls._testBasePath, 8000, 8000, 1, 1))
        cls._emptyTestImg = os.path.join(cls._testBasePath, 'emptytestimg.png')
        with open(cls._emptyTestImg, 'w'):
            pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._testBasePath)

    def test_calculateMD5HashWorks(self):
        ## small image
        self.assertEqual(dff.calculateMD5Hash(self._testImgs[0]), "5b4f89add29ae4ad253ce90b24ca132c")
        ## big image
        # self.assertEqual(dff.calculateMD5Hash(self._testImgs[1]), "7c4143dee5870f2dc5aebc7be1a42e32")

    def test_calculateMD5HashWorksOnEmptyFiles(self):
        ## md5 hash for empty '' is d41d8cd98f00b204e9800998ecf8427e
        self.assertEqual(dff.calculateMD5Hash(self._emptyTestImg), "d41d8cd98f00b204e9800998ecf8427e")

class TestCheckForDuplicates(unittest.TestCase):
    _testBasePath = os.path.join('/tmp', 'unittestdata')

    @classmethod
    def setUpClass(cls):
        np.random.seed(0)
        cls._imagePaths = createRandomTestImages(cls._testBasePath, 10, 10, 0, 5)
        cls._imagePaths3 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder1', 'folder3'), 10, 10, 5, 5)
        cls._imagePaths4 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder2', 'folder4'), 10, 10, 10, 20)

        np.random.seed(0)
        cls._imagePaths5 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder5'), 10, 10, 5, 5)
        cls._imagePaths6 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder1', 'folder6'), 10, 10, 10, 10)
        np.random.seed(10)
        cls._imagePaths6 = cls._imagePaths6.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder1', 'folder6'), 10, 10, 20, 10))
        cls._knownFilesMap = {dff.calculateMD5Hash(f):dff.File(f) for f in cls._imagePaths}
        np.random.seed(0)
        cls._imagePaths7 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder7'), 10, 10, 0, 10)
        np.random.seed(0)
        cls._imagePaths7.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder7'), 10, 10, 10, 10))
        np.random.seed(0)
        cls._imagePaths7.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder7'), 10, 10, 20, 10))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._testBasePath)

    def test_checkForDuplicatesWorksWithNoDuplicateFiles(self):
        inputFilesList = dff.buildInputFilesList([
            os.path.join(self._testBasePath, 'folder1', 'folder3'),
            os.path.join(self._testBasePath, 'folder2', 'folder4'),
        ], self._knownFilesMap)

        filesMap = copy.deepcopy(self._knownFilesMap)
        dff.checkForDuplicates(inputFilesList, self._knownFilesMap)
        self.assertEqual(len(self._imagePaths3) + len(self._imagePaths4) + len(filesMap), len(self._knownFilesMap))

        previouslyKnownFiles = [v._original for (k,v) in self._knownFilesMap.items()]
        allKnownFiles = [v._original for (k,v) in filesMap.items()]
        for f in allKnownFiles:
            self.assertTrue(f in previouslyKnownFiles or f in self._imagePaths3 or f in self._imagePaths4)
        for v in filesMap.values():
            self.assertFalse(v._duplicates)

    def test_checkForDuplicatesWorksWithDuplicateFilesInDifferentFolders(self):
        inputFilesList = dff.buildInputFilesList([self._testBasePath], {})
        filesMap = {}
        dff.checkForDuplicates(inputFilesList, filesMap)
        self.assertEqual(len(filesMap), 40)
        originalFileHashes = [dff.calculateMD5Hash(f._original) for f in filesMap.values() ]
        self.assertEqual(len(set(originalFileHashes)), len(originalFileHashes))
        self.assertEqual(originalFileHashes.sort(), list(filesMap.keys()).sort())
        ##assert duplicate file count matches
        duplicateFiles = [f for dupFiles in filesMap.values() for f in dupFiles._duplicates]
        self.assertEqual(len(duplicateFiles), 45)

    def test_checkForDuplicatesWorksWithDuplicateFilesInSameFolder(self):
        inputFilesList = dff.buildInputFilesList([os.path.join(self._testBasePath, 'folder7')], {})
        filesMap = {}
        dff.checkForDuplicates(inputFilesList, filesMap)
        self.assertEqual(len(filesMap), 10)

        duplicateFiles = [f for dupFiles in filesMap.values() for f in dupFiles._duplicates]

        self.assertEqual(len(duplicateFiles), 20)

class TestMoveTheDuplicates(unittest.TestCase):
    _testBasePath = os.path.join('/tmp', 'unittestdata')

    @classmethod
    def setUpClass(cls):
        np.random.seed(0)
        cls._imagePaths1 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder1'), 10, 10, 0, 10)
        np.random.seed(0)
        cls._imagePaths2 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder2'), 10, 10, 0, 5)

        np.random.seed(10)
        cls._imagePaths3 = createRandomTestImages(os.path.join(cls._testBasePath, 'folder3'), 10, 10, 0, 10)
        np.random.seed(10)
        cls._imagePaths3.extend(createRandomTestImages(os.path.join(cls._testBasePath, 'folder4'), 10, 10, 10, 5))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._testBasePath)
        shutil.rmtree('/tmp/duplicates')

    def test_moveTheDuplicatesWithDuplicatesInDifferentFoldersWorks(self):
        inputFilesList = dff.buildInputFilesList([os.path.join(self._testBasePath, 'folder1'),
            os.path.join(self._testBasePath, 'folder2')], {})
        filesMap = {}
        dff.checkForDuplicates(inputFilesList, filesMap)
        self.assertEqual(len(filesMap), 10)

        filesMapBeforeMove = copy.deepcopy(filesMap)
        dff.moveTheDuplicates(filesMap, '/tmp/duplicates')

        self.assertTrue(all([os.path.exists(f._original) for f in filesMap.values()]))
        
        self.assertTrue(all([os.path.exists(f) for dupFiles in filesMap.values() for f in dupFiles._duplicates]))
        self.assertTrue(not any([os.path.exists(f) for dupFiles in filesMapBeforeMove.values() for f in dupFiles._duplicates]))
        # print(json.dumps(filesMap, default=lambda o : o.__dict__, indent=2))

    def test_moveTheDuplicatesWithDuplicatesInSameFoldersWorks(self):
        inputFilesList = dff.buildInputFilesList([os.path.join(self._testBasePath, 'folder3'),
            os.path.join(self._testBasePath, 'folder4')], {})
        filesMap = {}
        dff.checkForDuplicates(inputFilesList, filesMap)
        self.assertEqual(len(filesMap), 10)

        filesMapBeforeMove = copy.deepcopy(filesMap)
        dff.moveTheDuplicates(filesMap, '/tmp/duplicates')

        self.assertTrue(all([os.path.exists(f._original) for f in filesMap.values()]))
        
        self.assertTrue(all([os.path.exists(f) for dupFiles in filesMap.values() for f in dupFiles._duplicates]))
        self.assertTrue(not any([os.path.exists(f) for dupFiles in filesMapBeforeMove.values() for f in dupFiles._duplicates]))
        # print(json.dumps(filesMap, default=lambda o : o.__dict__, indent=2))

if __name__ == '__main__':
    unittest.main()