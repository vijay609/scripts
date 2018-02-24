from PIL import Image, ImageDraw
import os
import glob
import concurrent.futures


# %matplotlib inline
# import matplotlib.pyplot as plt

def drawLines(image, destFolder):
    colors =[(255, 0, 0), (0, 255,0), (0, 0, 255), (255, 255,0), (255, 0, 255), (0, 255, 255)]
    im = Image.open(image)
    path, fileName = os.path.split(image)
    print (path)
    print (fileName)
    draw = ImageDraw.Draw(im) 
    col = 0
    for i in range(0,im.height,50):
        draw.line((0,i,im.width,i), fill=colors[col%len(colors)])
        col = col+1
    im.save(os.path.join(destFolder, fileName ))



images = glob.glob('/src/notebooks/images/*.png')

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Start the load operations and mark each future with its URL
    future_to_img = {executor.submit(drawLines, image, '/src/notebools/images'): image for image in images}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
        else:
            print('%r page is %d bytes' % (url, len(data)))
#res = [drawLines(img, '/src/notebooks/imagesWithLines/') for img in images]