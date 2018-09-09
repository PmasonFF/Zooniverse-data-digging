""" This version is written in Python 3.62
The following script inputs a subject set by subjectset.id, then acquires the subject using requests,
opens it as a numpy array and passes that into OpenCV. there it is cropped, changed to gray scale, and
filtered with a threshold to clean up the image.  The cleaned clropped image is saved as a file like
object and passed to Tesseract using the python "wrapper" (actually just a subprocess controller)
pytesseract.  That returns the text interpretation of the Date and time from the camera image. This
is cleaned up and converted to a fixed format, and also tested for a true date time structure.
It the reformatted text passes the test it is added to the subject metadata for the original subject
and the subject updated. As well a file of the subject.id, read text and the reformatted result is created.
"""
import os
import io
import csv
from PIL import Image
import numpy as np
import cv2 as cv
import pytesseract
from datetime import datetime


import panoptes_client
from panoptes_client import SubjectSet, Project, Panoptes
import requests
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='watchablewildlife/nebraska-spotted-skunk-project')


def text_to_date(in_text):
    # this function reformats and tests text that has been read by tesseract
    try:
        split_text = in_text.split(' ')
        month = {
            'JAN': '01',
            'FEB': '02',
            'MAR': '03',
            'APR': '04',
            'MAY': '05',
            'JUN': '06',
            'JUL': '07',
            'AUG': '08',
            'SEP': '09',
            'OCT': '10',
            'NOV': '11',
            'DEC': '12'
        }
        # desired format: 2018:04:04 14:57:26
        date = split_text[2] + ':' + month[split_text[1]] + ':' + split_text[0].zfill(2)
        split_time = split_text[3].split(':')
        if len(split_time[1]) > 2 and len(split_text) == 4:
            split_text.append(split_time[1].zfill(4)[2:])
        if split_text[4] == 'pm' and int(split_time[0]) < 12:
            time_hr = str(int(split_time[0]) + 12)
        else:
            time_hr = split_time[0]
        time = time_hr + ':' + split_time[1].zfill(2)[:2] + ':00'
        datetime.strptime(date + ' ' + time, '%Y:%m:%d %H:%M:%S')
        return date + ' ' + time
    except(KeyError, TypeError, IndexError):
        return ''


def write_results(sub, txt, dattim):
    # this simply write the results to the previously opened file
    new_line = {'subject_ids': sub,
                'Text_as_read': str(txt),
                'Text_formatted': dattim}
    writer.writerow(new_line)
    return

# open the output file and write the header with DictWriter
with open('OCR_results.csv', 'wt', newline='') as file:
    fieldnames = ['subject_ids', 'Text_as_read', 'Text_formatted']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    while True:
        # input the subject set to update (note credentials are needed to save to the
        # subject set but not to read from it.
        set_id = input('Entry subject set id to update:' + '\n')
        save_opts = {'optimize': True, 'quality': 95, 'format': 'png'}
        try:
            subject_set = SubjectSet.find(set_id)
            count_subjects = 0
            subject_list = []
            for subject in subject_set.subjects:
                count_subjects += 1
                print(count_subjects)
                try:
                    # open the subject image file (first frame) and create a numpy array for the image
                    im = requests.get(subject.locations[0]['image/jpeg'], stream=True).raw
                    arr = np.asarray(bytearray(im.read()), dtype=np.uint8)
                    # decode the array as an OpenCV image and crop it
                    img = cv.imdecode(arr, -1)[538:, 650:]
                    # convert to gray scale and threshold to clean up image
                    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                    gray = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[1]

                    # save the cleaned and cropped image in memory as a file-like object
                    file_bytes = io.BytesIO()
                    filename = "file_bytes.png"
                    cv.imwrite(filename, gray)

                    # process the file with tesseract via py tesseract (this could include many
                    # options for tesseract, including templates or details of specific fonts, but it
                    # did the job in its simplest form.
                    text = pytesseract.image_to_string(Image.open(filename))

                    # apply the formatting function and write the results
                    date_time = text_to_date(text)
                    write_results(subject.id, text, date_time)

                except (IOError, KeyError, TypeError, IndexError):
                    text = 'process failed'
                    date_time = ''
                    write_results(subject.id, text, date_time)

                if len(date_time) >= 10:
                    # if a date_time has been recovered and passed the testing update the subject metadata
                    subject.metadata['DateTime'] = date_time
                    #  currently this save works with version 1.02 of the panoptes _client but doe not work
                    #  with the current version 1.03 - an issue has been raised 09-09-2018
                    subject.save()
                    print(subject.id, subject.metadata['DateTime'], ' updated')

            break
        except panoptes_client.panoptes.PanoptesAPIException:
            retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
            if retry.lower() == 'n':
                quit()
