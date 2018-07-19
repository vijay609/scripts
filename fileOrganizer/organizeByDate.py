'''
.MP4 : 7
.MOV : 540
.png : 24
.PNG : 17
.CR2 : 464
.tif : 7
.JPG : 25540
.AVI : 30
.THM : 49
.3gp : 11
.mts : 7
.mov : 214
.tiff : 1
.psd : 8
.mp4 : 138
.txt : 1
.MTS : 233
.jpeg : 741
.NEF : 8760
.MPG : 42
.nef : 1278
.jpg : 13660
.dng : 112
.avi : 20
'''
import os
import exiftool
import glob
ext = '.MP4'
source_dir = '/media/vijay/Data/Pictures/allPictures/**/'
dest_dir = '/media/vijay/Data/Pictures/allPicturesSorted/'

def main():
    all_files = glob.glob('{}*{}'.format(source_dir, ext), recursive=True)
    with exiftool.ExifTool('/src/Image-ExifTool-10.97/exiftool') as et:
        tags = et.get_tags_batch(['File:FileModifyDate'], all_files)
        for tag in tags:
            print(tag)



if __name__ == '__main__':
    main()