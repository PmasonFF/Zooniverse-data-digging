""" This version is written in Python 3.8  """

import os
import panoptes_client
from panoptes_client import SubjectSet, Panoptes
import shutil
import requests

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

while True:
    set_id = input('Enter subject set id to download:' + '\n')
    try:
        print('Please wait while I check this subject set exists and how many subjects are in it')
        subject_set = SubjectSet.find(set_id)
        count_subjects = subject_set.set_member_subjects_count
        print('You have chosen to download ', count_subjects, ' subjects from subject set ', set_id)
        retry = input('Enter "n" to cancel this download, any other key to continue' + '\n')
        if retry.lower() == 'n':
            quit()
        break
    except panoptes_client.panoptes.PanoptesAPIException:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
        if retry.lower() == 'n':
            quit()

while True:
    location = input('Enter the full path for the image directory to download to, or enter "." '
                     'to use the current directory' + '\n')
    if location == '.':
        location = os.getcwd()
        break
    else:
        if os.path.exists(location):
            break
        else:
            try:
                os.mkdir(location)
                break
            except FileNotFoundError:
                print('That entry is not a valid path for an existing directory')
                print(r'Example (Windows) "C:\Some_directory_name\Some_sub_directory"')
                print('Note, no closing slash')
                retry = input('Enter "n" to cancel, any other key to try again' + '\n')
                if retry.lower() == 'n':
                    quit()

print('Please wait while a list of subject to download is prepared')
subject_list = []
count = 0

for subject in subject_set.subjects:
    count += 1
    # if count == 10:
    #    break
    print('\r', 'Found subject:', count, '   ', subject.id, end='')
    subject_list.append(subject)
print("\r", '')
print('Downloading...')
count = 0
saved_single = 0
saved_multiple = 0
for item in subject_list:
    count += 1
    try:
        if item.metadata['id'].find('jpeg_') > 0:
            file_names = item.metadata['id'].partition('jpeg_')
            file_name_1 = location + os.sep + file_names[0] + 'jpeg'
            file_name_2 = location + os.sep + file_names[2]
            flag = 'multiple'
        elif item.metadata['id'].find('jpg_') > 0:
            file_names = item.metadata['id'].partition('jpg_')
            file_name_1 = location + os.sep + file_names[0] + 'jpg'
            file_name_2 = location + os.sep + file_names[2]
            flag = 'multiple'
        else:
            file_name_1 = location + os.sep + item.metadata['id']
            file_name_2 = ''
            flag = 'single'
    except KeyError:  # default to zooniverse subject id as file name if metadata does not contain a field "id"
        file_name_1 = location + os.sep + item.id + '_1.' + (list(item.locations[0].keys())[0]).partition('/')[
            2].lower()
        try:
            file_name_2 = location + os.sep + item.id + '_2.' + (list(item.locations[1].keys())[0]).partition('/')[
                2].lower()
            flag = 'multiple'
        except IndexError:  # ie if locations[1] does not exist it is a single frame image
            file_name_2 = ''
            flag = 'single'

    # acquire the images
    try:
        if flag == 'multiple':
            if not os.path.isfile(file_name_1):
                with requests.get(list(item.locations[0].values())[0], stream=True) as r_1:
                    with open(file_name_1, 'wb') as f_1:
                        shutil.copyfileobj(r_1.raw, f_1, length=16 * 1024 * 1024)
            if not os.path.isfile(file_name_2):
                with requests.get(list(item.locations[1].values())[0], stream=True) as r_2:
                    with open(file_name_2, 'wb') as f_2:
                        shutil.copyfileobj(r_2.raw, f_2, length=16 * 1024 * 1024)
            print('\r', 'Subject ', item.id, '   ', 'Acquired files', file_name_1, '   ', file_name_2, end='')
            saved_multiple += 1
        else:
            if not os.path.isfile(file_name_1):
                with requests.get(list(item.locations[0].values())[0], stream=True) as r_1:
                    with open(file_name_1, 'wb') as f_1:
                        shutil.copyfileobj(r_1.raw, f_1, length=16 * 1024 * 1024)
            print('\r', 'Subject ', item.id, '   ', 'Acquired file', file_name_1, end='')
            saved_single += 1
    except IOError:
        print('\r', 'Subject download for ', item.id, ' failed')
        continue
print('\r', '')
print('Downloaded', saved_single, 'single frame subjects and', saved_multiple, 'double frame subjects of ',
      len(subject_list), 'total subjects')
