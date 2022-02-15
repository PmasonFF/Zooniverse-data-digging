from PIL import Image
import exiftool
import os
from os.path import join
import csv
import io
import operator
from datetime import datetime
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes


def get_files_in(folder):
    file_types = ['jpg', 'jpeg']
    file_listing = []
    counter = 0
    for path, _, files in os.walk(folder):  # opens the directory and gets a list of all .jpg files in it.
        for name in files:
            if counter % 10 == 0:
                print('.', end='')
            counter += 1
            if name.partition('.')[2].lower() in file_types:
                image_tags = get_image_tags(join(path, name))
                file_listing.append([name, path.split(os.sep)[-1], path, get_date_time(image_tags, name),
                                     get_camera_number(image_tags, name)])
    files_by_time = sorted(file_listing, key=operator.itemgetter(3))
    return sorted(files_by_time, key=operator.itemgetter(1))  # files sorted by site and time


def get_image_tags(image_file):
    try:
        with exiftool.ExifTool() as et:
            return et.get_tags(['DateTimeOriginal', 'UserLabel', 'Software'], image_file)
    except (IOError, KeyError, TypeError):
        print('Acquiring tags for ', image_file, ' failed')
        return {}


def get_date_time(tag_dict, image_file):
    try:
        date_time = tag_dict['EXIF:DateTimeOriginal']
        if date_time:
            return date_time
    except (IOError, KeyError, TypeError):
        pass
    print('Acquiring date_time for ', image_file, ' failed')
    return '2000:01:01 00:00:00'


def get_camera_number(tag_dict, image_file):
    try:
        camera = tag_dict['MakerNotes:UserLabel']
        if camera:
            return camera
    except (IOError, KeyError, TypeError):
        try:  # this try...except is primarily for testing with image files without valid UserLabel info
            software = tag_dict['EXIF:Software']
            if software:
                return software
        except (IOError, KeyError, TypeError):
            print('Acquiring camera name for ', image_file, ' failed')
            return 'no camera number'


def compress(original_file, resize_ratio, max_size):
    orig_image = Image.open(original_file)
    width, height = orig_image.size
    quality = [scale for scale in range(0, 101)]
    lo = 0
    mid = 50
    hi = len(quality)
    file_bytes_ = ''
    size_ = 0
    while lo < hi:
        mid = (lo + hi) // 2

        scaled_size = (int(width * resize_ratio), int(height * resize_ratio))
        resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)

        file_bytes_ = io.BytesIO()
        resized_file.save(file_bytes_, optimize=True, quality=quality[mid], format='jpeg')
        size_ = file_bytes_.tell()

        if size_ < max_size:
            lo = mid + 1
        else:
            hi = mid
    print('resized', original_file, ' to', size_, ' Bytes, quality', quality[mid])
    file_bytes_.seek(0, 0)
    return file_bytes_, size_


while True:
    top_folder = input('Enter the full path for the top directory to begin image search, or enter "." '
                       'to use the current directory' + '\n')
    if top_folder == '.':
        top_folder = os.getcwd()
        break
    else:
        if os.path.exists(top_folder):
            break
        else:
            print('That entry is not a valid path for an existing directory')
            retry = input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

set_name = input('Entry a name for the subject set to use or create:' + '\n')
while True:
    delay = input('Entry maximum time interval in seconds for images within an event:' + '\n')
    try:
        if 0 < int(delay) < 600:
            break
    except TypeError:
        pass
    print('That entry is not a valid delay in seconds, must be an integer >0, <600')
    retry = input('Enter "y" to try again, any other key to exit' + '\n')
    if retry.lower() != 'y':
        quit()

print('Acquiring image info and building sequences - this take approximately one minutes for every 150 images')

file_list = get_files_in(top_folder)
number = len(file_list)
start = 1
previous_site = file_list[0][1]
previous_time = datetime.strptime(file_list[0][3], '%Y:%m:%d %H:%M:%S')
sequence = [file_list[0]]
if previous_time.year == 2000:  # this loop is required if the first file encountered has no valid date_time
    for index, file in enumerate(file_list):
        previous_time = datetime.strptime(file[3], '%Y:%m:%d %H:%M:%S')
        if previous_time.year != 2000:
            previous_site = file[1]
            sequence = file
            start = index + 1
            break
    print('No Valid Date time found to start sequencing')
    quit()

all_images = []
file_count = 1
sequence_count = 1
for file in file_list[start:]:
    current_site = file[1]
    current_time = datetime.strptime(file[3], '%Y:%m:%d %H:%M:%S')
    if current_time.year == 2000:
        continue  # ie skip files with no valid date_time
    tdelta = current_time - previous_time
    file_count += 1
    if tdelta.seconds <= int(delay) and current_site == previous_site:
        sequence.append(file)
    else:
        all_images.append(sequence)
        sequence = [file]
        sequence_count += 1
    previous_site = current_site
    previous_time = current_time
all_images.append(sequence)

print('Found ', file_count, ' files in', sequence_count, ' sequences to upload in this directory.')

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
# project = Project.find(slug='lawildlife/wildlife-of-los-angeles')
project = Project.find(slug='pmason/fossiltrainer')
previous_subjects = []
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', file_count, ' files to an existing subject set', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    print('Please wait while a list of previous subjects uploaded to this set is prepared')
    print('This can take approximately one minute for every 400 subjects previously uploaded')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['#Site'] + os.sep + subject.metadata['image_1'])
except StopIteration:
    print('You have chosen to upload ', file_count, ' files to an new subject set ', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Previous subjects acquired, beginning resize and uploading: \n')
images_uploaded = 0
new_subjects = 0
previously_uploaded = 0
for seq_num, seq in enumerate(all_images):
    avg_size = 0
    if seq[0][1] + os.sep + seq[0][0] not in previous_subjects:  # subdirectory and filename
        image_count = len(seq)
        step = int((image_count - 1) / 8) + 1
        try:
            subject = Subject()
            subject.links.project = project
            metadata = {'id': seq_num + 1,
                        '#Set_name': set_name,
                        '#Site': seq[0][1],
                        '#camera': seq[0][4]
                        }
            image_number = 0
            for index, [image, site, root, dtime, _] in enumerate(seq):
                if index % step == 0:
                    image_number += 1
                    try:
                        file_bytes, size = compress(join(root, image), .75, 300000)
                        avg_size += size
                        subject.add_location(file_bytes)

                        metadata['image_' + str(image_number)] = image
                        metadata['#datetime_' + str(image_number)] = dtime
                        images_uploaded += 1
                    except FileNotFoundError:
                        print(join(root, image), 'not found')
                        continue
            new_subjects += 1
            print('Uploading group', seq[0][0], 'with', len(seq), 'files' + '\n')
            subject.metadata.update(metadata)
            subject.save()
            subject_set.add(subject.id)

        except panoptes_client.panoptes.PanoptesAPIException:
            print('An error occurred during the upload of File_group ', seq[0][0])
    else:
        previously_uploaded += 1
print(images_uploaded, 'images uploaded into', new_subjects, 'subjects, ',
      previously_uploaded, 'subjects previously uploaded')

#  test for the optional summary output
if input('Enter "y" to save a summary file, any other key to exit' + '\n').lower() == 'y':
    print('Preparing summary file, please wait...')
    uploaded = 0
    with open(top_folder + os.sep + 'Uploaded_' + set_name + '_' + str(datetime.now())[0:10]
              + '.csv', 'w', newline='') as file:
        fieldnames = ['zoo_subject', 'id', '#Set_name', '#Site', '#camera', 'image_1', 'image_2',
                      'image_3', 'image_4', 'image_5', 'image_6', 'image_7', 'image_8',
                      '#datetime_1', '#datetime_2', '#datetime_3', '#datetime_4',
                      '#datetime_5', '#datetime_6', '#datetime_7', '#datetime_8']

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
        for subject in subject_set.subjects:
            uploaded += 1
            if (uploaded - 1) % 100 == 0:
                print('.', end='')
            new_line = subject.metadata
            new_line['zoo_subject'] = subject.id
            writer.writerow(subject.metadata)

        print('\n', uploaded, ' subjects found in the subject set, see the full list in  '
              'Uploaded_' + set_name + '_' + str(datetime.now())[0:10] + '.csv')
