from PIL import Image
import csv
import json
import os
import io

from panoptes_client import SubjectSet, Subject, Project, Panoptes

avg_compressed_file_size = 500000


def compress(original_file, max_size):
    orig_image = Image.open(original_file)
    width, height = orig_image.size
    quality = [scale for scale in range(0, 101)]
    lo = 0
    hi = len(quality)
    file_bytes_ = ''
    while lo < hi:
        mid = (lo + hi) // 2

        scaled_size = (int(width * .75), int(height * .75))
        resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)

        file_bytes_ = io.BytesIO()
        resized_file.save(file_bytes_, optimize=True, quality=quality[mid], format='jpeg')
        size_ = file_bytes_.tell()

        if size_ < max_size:
            lo = mid + 1
        else:
            hi = mid
    file_bytes_.seek(0, 0)
    return file_bytes_


# set up zooniverse User_name and password as environmental variables
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])  # os.environ['Password'])

#  modify project slug as needed:
project = Project.find(slug='pmason/fossiltrainer')
#  project = Project.find(slug='embeller/offal-wildlife-watching')

#  input path for manifest file as needed:
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

manifest_file = location + os.sep + 'manifest.csv'

#  input subject set name as needed:
set_name = input('Entry a name for the subject set to use or create:' + '\n')
previous_subjects = []

# This section sets up a subject set
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('Please wait while a list of previous subjects uploaded to this set is prepared')
    print('This can take approximately one minute for every 400 subjects previously uploaded')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['File_group'])
except StopIteration:
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Previous subjects acquired, beginning resize and uploading: \n')
# This section adds subjects from a manifest to the above subject set
with open(manifest_file, 'r') as mani_file:
    r = csv.DictReader(mani_file)
    images_uploaded = 0
    new_subjects = 0
    previously_uploaded = 0
    for line in r:
        file_list = json.loads(line['file_list'])
        if line['File_group'] not in previous_subjects:
            new_subjects += 1
            subject = Subject()
            subject.links.project = project
            subject.metadata['File_group'] = line['File_group']
            subject.metadata['Set_Name'] = set_name
            subject.metadata['Date_times'] = line['Date_times']
            subject.metadata['Number of files'] = line['Number of files']

            for index, image, in enumerate(file_list):
                subject.add_location(compress(location + os.sep + image, avg_compressed_file_size))
                images_uploaded += 1
            print('Uploading group', line['File_group'], 'with', len(file_list),
                  'files, this could take a while!')
            subject.save()
            subject_set.add(subject.id)
        else:
            previously_uploaded += 1
print(images_uploaded, 'images uploaded into', new_subjects, 'subjects, ',
      previously_uploaded, 'subjects previously uploaded')

uploaded = 0
with open(location + os.sep + 'Uploaded_' + set_name + '.csv', 'wt') as upfile:
    upfile.write('subject.id' + ',' + 'Metadata' + '\n')
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        upfile.write(subject.id + ',' + json.dumps(subject.metadata) + '\n')
    print(uploaded, ' subjects found in the subject set, see the full list in Uploaded_' + set_name + '.csv')

#  ___________________________________________________________________________________________________________________
