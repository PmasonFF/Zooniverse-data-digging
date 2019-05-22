""" This version is written in Python 3.7"""

import os
import io
from PIL import Image
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes


def compress(original_location, original_file, resized_width):
    orig_image = Image.open(original_location + os.sep + original_file)
    width, height = orig_image.size
    #  calculate the scale factor required and resized height
    scale = float(resized_width) / width
    scaled_size = (resized_width, int(height * scale))
    #  resize the image
    resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)
    #  save it in a file-like object (in memory) and find the size
    file_bytes = io.BytesIO()
    resized_file.save(file_bytes, optimize=True, quality=100, format='jpeg')
    size = file_bytes.tell()
    print('Uploading ', original_file, scale, resized_width, size)
    #  ensure the file pointer is returned to the beginning of the file-like object
    file_bytes.seek(0, 0)
    return file_bytes


#  connect to zoniverse - requires the User_name and Password to be set up as environmental variables in your OS
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
#  modify the project slug if used for other than Snapshots at Sea
project = Project.find(slug='tedcheese/snapshots-at-sea')


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

#  load the list of image files found in the directory:
#  The local file name will be uploaded as metadata with the image
file_types = ['jpg', 'jpeg']
subject_metadata = {}
for entry in os.listdir(location):
    if entry.partition('.')[2].lower() in file_types:
        subject_metadata[entry] = {'Filename': entry}
print('Found ', len(subject_metadata), ' files to upload in this directory.')

# input the subject set name the images are to be uploaded to
set_name = input('Entry a name for the subject set to use or create:' + '\n')
previous_subjects = []

try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', len(subject_metadata), ' files to an existing subject set', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    print('\n', 'It may take a while to recover the names of files previously uploaded, to ensure no duplicates')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['Filename'])
except StopIteration:
    print('You have chosen to upload ', len(subject_metadata), ' files to an new subject set ', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Uploading subjects, this could take a while!')
new_subjects = 0
for filename, metadata in subject_metadata.items():
    try:
        if filename not in previous_subjects:
            subject = Subject()
            subject.links.project = project
            subject.add_location(compress(location, filename, 960))
            subject.metadata.update(metadata)
            subject.save()
            subject_set.add(subject.id)
            new_subjects += 1
    except panoptes_client.panoptes.PanoptesAPIException:
        print('An error occurred during the upload of ', filename)
print(new_subjects, 'new subjects created and uploaded')
print('Uploading complete, Please wait while the full subject listing is prepared and saved in')
print('"Uploaded subjects.csv" in the drive with the original images')

uploaded = 0
with open(location + os.sep + 'Uploaded subjects.csv', 'wt') as file_up:
    file_up.write('subject.id' + ',' + 'Filename' + '\n')
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        file_up.write(subject.id + ',' + list(subject.metadata.values())[0] + '\n')
    print(uploaded, ' subjects found in the subject set, see the full list in Uploaded subjects.csv.')
