import piexif
import os
import csv
from os.path import join
import io
from PIL import Image
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
                site_date = ''
                # This next section can be used to set site_date to the directory name of a subdirectory in the path
                # based on the directory names eg in this case containing "2021", and only accept images
                # from subdirectories meeting this condition.
                for folder_level in path.split(os.sep):
                    if folder_level.find('2021') >= 0:
                        site_date = folder_level
                if site_date:
                    try:
                        exif_dict = piexif.load(join(path, name))
                        exposure_date_time = exif_dict['Exif'][36867].decode("utf-8")
                        file_listing.append([name, site_date, path, exposure_date_time, name])
                    except (KeyError, TypeError):
                        print('date_time not found for image file', join(path, name))

    files_by_time = sorted(file_listing, key=operator.itemgetter(3))
    return sorted(files_by_time, key=operator.itemgetter(1))  # files sorted by site and time


def compress(original_file, resize_width, max_size):
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

        scaled_size = (int(resize_width), int(height * resize_width / width + .5))
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
    return file_bytes_


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
frames_count = 0
for file in file_list[start:]:
    current_site = file[1]
    current_time = datetime.strptime(file[3], '%Y:%m:%d %H:%M:%S')
    if current_time.year == 2000:
        continue  # ie skip files with no valid date_time
    tdelta = current_time - previous_time
    file_count += 1
    frames_count += 1
    # Set maximum number of frames_count
    if tdelta.seconds <= int(delay) and current_site == previous_site and frames_count <= 3:
        sequence.append(file)
    else:
        all_images.append([sequence[0][0], sequence])
        sequence = [file]
        sequence_count += 1
        frames_count = 0
    previous_site = current_site
    previous_time = current_time
all_images.append([sequence[0][0], sequence])

print('\n', 'Found ', file_count, ' files in', sequence_count, ' sequences to upload in this directory.')

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='pmason/fossiltrainer')
previous_subjects = []
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', sequence_count, ' subjects to an existing subject set', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    print('Please wait while a list of previous subjects uploaded to this set is prepared')
    print('This can take approximately one minute for every 400 subjects previously uploaded')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['Site_Date'] + '_' + str(subject.metadata['#event_id']))
except StopIteration:
    print('You have chosen to upload ', sequence_count, ' subjects to an new subject set ', set_name)
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
for [first_image, seq] in all_images:
    if seq[0][1] + '_' + first_image not in previous_subjects:  # subdirectory and event_id
        try:
            subject = Subject()
            subject.links.project = project
            metadata = {'#Subject_set': set_name,
                        '#event_id': first_image,
                        'Site_Date': seq[0][1],
                        }
            image_number = 0
            for [image, site, root, dtime, _] in seq:
                try:
                    file_bytes = compress(join(root, image), 1920, 500000)
                    subject.add_location(file_bytes)
                    image_number += 1
                    metadata['image_' + str(image_number)] = image
                    metadata['#datetime_' + str(image_number)] = dtime
                    images_uploaded += 1
                except FileNotFoundError:
                    print(join(root, image), 'not found')
                    continue
                except OSError:
                    print(join(root, image), 'image defective')
                    continue
            new_subjects += 1
            print('Uploading group', seq[0][0], 'with', image_number, 'files' + '\n')
            subject.metadata.update(metadata)
            subject.save()
            subject_set.add(subject.id)

        except panoptes_client.panoptes.PanoptesAPIException:
            print('An error occurred during the upload of File_group ', seq[0][1], first_image)
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
        fieldnames = ['zoo_subject', '#event_id', '#Subject_set', 'Site_Date', 'image_1', 'image_2',
                      'image_3', '#datetime_1', '#datetime_2', '#datetime_3']

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
