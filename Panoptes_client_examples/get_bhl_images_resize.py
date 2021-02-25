"""

Download a group of jpeg files from Biodiversity Heritage Library (BHL). Download the highest resolution
versions available. The user is prompted for the name of an input file with two columns with headers 'page_id'
and 'output_filename' containing BHL pageids and an optional output filename.
The quality is the depth or jpeg quality to use for the reduced file, and the max_size is a parameter that
determines if the file is reduce in pixels as well as depth to meet this limit. The actual final file size
will normally be less than the limit but that is not certain, It may end up slightly larger.
If output filenames are not supplied, output files are named <BHL page id>_<quality>_<maxsize(kb)>.jpg
Code is written in Python 3.
"""
import os
import csv
from urllib.request import urlopen
import io
from PIL import Image


def compress(url, quality, max_size):
    orig_image = Image.open(urlopen(url))
    width, height = orig_image.size
    scales = [scale / 16 for scale in range(1, 17)]
    resized_file = []
    lo = 0
    hi = len(scales)
    while lo < hi:
        mid = (lo + hi) // 2
        scaled_size = (int(width * scales[mid]), int(height * scales[mid]))
        resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)
        file_bytes = io.BytesIO()
        resized_file.save(file_bytes, optimize=True, quality=quality, format='jpeg')
        size = file_bytes.tell()
        if size < max_size:
            lo = mid + 1
        else:
            hi = mid
    return resized_file


def get_input_file():
    """
    Prompt the user for the name of an input file with two columns with headers 'page_id' and 'output_filename'
    containing BHL pageids and an optional output filename.
    The quality is the depth or jpeg quality to use for the reduced file, and the max_size is a parameter
    that determines if the file is reduce in pixels as well as depth to meet this limit. The actual final
    file size will normally be less than the limit but that is not certain, It may end up slightly larger.
    If output filenames are not supplied, output files are named <BHL page id>_<quality>_<maxsize(kb)>.jpg
    """

    while True:  # Loop until a valid filename is entered or the user types 'exit'
        infile = input('Enter filename of input file or exit: ' + '\n')
        if infile == 'exit':
            exit()
        try:
            if os.path.isfile(infile):
                break
        except FileNotFoundError:
            print('The file could not be opened. Please try again.')

    while True:  # Loop until a valid quality is entered or the user types 'exit'
        qual = input('Enter the quality setting:' + '\n')
        if qual == 'exit':
            exit()
        try:
            if 30 <= int(qual) <= 100:
                break
        except TypeError:
            print('Quality must be an integer between 30 and 100, please try again or type exit')

    while True:  # Loop until a valid max_size is entered or the user types 'exit'
        max_s = input('Enter the maximum file size or exit:' + '\n')
        if max_s == 'exit':
            exit()
        try:
            if 200000 <= int(max_s) <= 1000000:
                break
        except TypeError:
            print('Max_size must be an integer between 200000 and 1000000, please try again or type exit')

    return infile, int(qual), int(max_s)


def getimage(pageid, quality, max_size, outfn):
    """
    Use the pageid to build the URL for a high-resolution image within 
    Biodiversity Heritage Library (BHL).
    The quality and max_size are use to compress the file. Some experimentation is
    required to find the optimum parameters. For black on beige illustration captions
    lower depth (eg quality = 60) and full pixel counts ( max_size near the max limit
    are often the best. Uses the last parameter outfn, as the filename for a file on
    the local system.
    """
    base_url = 'https://biodiversitylibrary.org/pageimage/'
    current_url = base_url + pageid
    print(current_url)  # Keep user informed of progress by printing the image URL
    reduced_img_file = compress(current_url, quality, max_size)  # Call the compression routine
    print(outfn)
    reduced_img_file.save(outfn, optimize=True, quality=quality, format='jpeg')  # save the reduced file
    return


def main():
    infile, quality, max_size = get_input_file()  # Get filename of file containing page ids, quality and max_size.
    with open(infile, 'r') as file:
        print(file)
        quit()
        input_hand = csv.DictReader(file)
        for row in input_hand:  # Process every row in the input file. Each row identifies an image to download.
            if row['output_filename']:
                ofn = row['output_filename']
            else:
                ofn = row['page_id'] + '_' + str(quality) + '_' + str(max_size)[
                                                                  :3] + '.jpg'
            getimage(row['page_id'], quality, max_size, ofn)  # Call code that pulls compresses and saves images


if __name__ == "__main__":
    main()
