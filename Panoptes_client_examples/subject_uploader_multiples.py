import numpy as np
import cv2 as cv
from PIL import Image
import os
import io
from datetime import datetime, timedelta
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes


def get_files_in(folder):
    file_types = ['jpg', 'jpeg']
    file_listing = []
    for entry in os.listdir(folder):
        if entry.partition('.')[2].lower() in file_types:
            file_listing.append(entry)
    return file_listing


def light_curves(image_file):
    img = cv.imread(image_file, 1)[50: 350, 50: 350]
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    light_sum = np.sum(gray)
    return light_sum


def get_date_time(image_file):
    try:
        img = Image.open(image_file)
        exif_dict = img._getexif()
        date_time = exif_dict[306]
    except (IOError, KeyError):
        print('Acquiring exif data for ', image_file, ' failed')
        date_time = '2018:07:26 00:00:00'
    return date_time


def compress(original_file, max_size, reduced_file):
    orig_image = Image.open(original_file)
    width, height = orig_image.size
    quality = [scale for scale in range(80, 101)]

    lo = 0
    hi = len(quality)
    file_bytes = ''
    size = 0
    while lo < hi:
        mid = (lo + hi) // 2

        scaled_size = (int(width * .75), int(height * .75))
        resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)

        file_bytes = io.BytesIO()
        resized_file.save(file_bytes, optimize=True, quality=quality[mid], format='jpeg')
        size = file_bytes.tell()

        if size < max_size:
            lo = mid + 1
        else:
            hi = mid
    print('resized', original_file, ' to', size, ' Bytes')
    file_bytes.seek(0, 0)
    with open(reduced_file, 'wb') as f_output:
        f_output.write(file_bytes.read())
    return reduced_file


while True:
    location = input('Enter the full path for the image directory, or enter "." '
                     'to use the current directory' + '\n')
    if location == '.':
        location = os.getcwd()
        break
    else:
        if os.path.exists(location):
            break
        else:
            print('That entry is not a valid path for an existing directory')
            retry = input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

set_name = input('Entry a name for the subject set to use or create:' + '\n')

file_list = get_files_in(location)
number = len(file_list)
previous_time = get_date_time(location + os.sep + file_list[0])
day_images = []
sequence = []
count = 0
for file in file_list:
    print('Testing image', file)
    current_time = get_date_time(location + os.sep + file)
    tdelta = datetime.strptime(current_time,
                               '%Y:%m:%d %H:%M:%S') - datetime.strptime(previous_time, '%Y:%m:%d %H:%M:%S')
    if light_curves(location + os.sep + file) >= 2000000:
        count += 1
        if tdelta <= timedelta(minutes=5, seconds=2):
            sequence.append([file, current_time])
        else:
            if len(sequence) > 0:
                day_images.append(sequence)
            sequence = [[file, current_time]]
    else:
        if len(sequence) > 0:
            day_images.append(sequence)
            sequence = []
    previous_time = current_time
if len(sequence) > 0:
    day_images.append(sequence)

print('Found ', count, ' day time files to upload in this directory.')

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='pmason/fossiltrainer')

# previous_subjects = []

try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', count, ' files to an existing subject set',  set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # for subject in subject_set.subjects:
    #     previous_subjects.append(subject.metadata['Filegroup'])
except StopIteration:
    print('You have chosen to upload ', count, ' files to an new subject set ',  set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

images_uploaded = 0
new_subjects = 0
table = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8],
         9: [4, 5], 10: [5, 5], 11: [5, 6], 12: [6, 6], 13: [6, 7], 14: [7, 7],
         15: [7, 8], 16: [8, 8], 17: [5, 6, 6]}
for seq in day_images:
    groups = int((len(seq) + 3) / 7)
    group_list = []
    eights = len(seq) % 7
    if len(seq) < 18:
        group_list = table[len(seq)]
    else:
        if len(seq) % 7 > 3:
            sixes = 7 - len(seq) % 7
            for i in range(1, sixes + 1):
                group_list.append(6)
            for i in range(sixes, groups):
                group_list.append(7)
        if len(seq) % 7 < 4:
            eights = len(seq) % 7
            for i in range(0, eights):
                group_list.append(8)
            for i in range(eights, groups):
                group_list.append(7)

    k = 0
    for index in range(0, len(group_list)):
        date_times = ''
        files = ''
        try:
            subject = Subject()
            new_subjects += 1
            subject.links.project = project
            for j in range(0, group_list[index]):
                compressed_file = compress(location + os.sep + seq[k][0], 900000,
                                           r'C:\py\image_manipulation\temp_file.jpg')
                subject.add_location(compressed_file)
                files += seq[k][0] + ', '
                date_times += seq[k][1] + ', '
                images_uploaded += 1
                k += 1
            subject.metadata['File_group'] = files[:-2]
            subject.metadata['Site_Date'] = set_name
            subject.metadata['Date_times'] = date_times[:-2]
            print('Uploading group, this could take a while!')
            subject.save()
            subject_set.add(subject.id)
            print(new_subjects, subject.metadata['File_group'], subject.metadata['Date_times'])
        except panoptes_client.panoptes.PanoptesAPIException:
            print('An error occurred during the upload of ', files)
print(images_uploaded, 'images uploaded into', new_subjects, 'subjects')

uploaded = 0
with open(location + os.sep + 'Uploaded subjects.csv', 'wt') as upfile:
    upfile.write('subject.id' + ',' + 'File_group' + ',' + 'Site_Date' + ',' + 'Date_times' + '\n')
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        upfile.write(subject.id + ',' + subject.metadata['File_group']
                     + ',' + subject.metadata['Site_Date'] + ',' + subject.metadata['Date_times'] + '\n')
    print(uploaded, ' subjects found in the subject set, see the full list in Uploaded subjects.csv.')
