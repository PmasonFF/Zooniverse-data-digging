""" This version is written in Python 3.62.  It accepts a subject set id then locates the subjects
in the set sequentially.  It uses a specified subject set metadata field to determine if the
subject is a duplicate. If so it attempts to delink it from the subject set. There is a report produced
including the number of unique subjects found, the number of subjects with no metadata as specified,
the number of duplicates found, the number of duplicates removed and the number of duplicates not removed
successfully.  The script then asks for a directory to place a listing of the remaining subjects in the
subject set. This action can be terminated by entering an invalid directory name."""
import os
import panoptes_client
from panoptes_client import SubjectSet, Panoptes

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

while True:
    subject_set_id = input('Enter subject set id to test and remove duplicates :' + '\n')
    metadata_field = input('Enter the name of the metadata field use to test for duplicates' + '\n')
    try:
        print('Please wait while I check this subject set exists and how many subjects are in it')
        subject_set = SubjectSet.find(subject_set_id)
        dup_count = 0
        no_metadata = 0
        count_subjects = 0
        duplicate_subjects = []
        not_removed = []
        dup_removed = 0
        subject_list = set()
        for subject in subject_set.subjects:
            count_subjects += 1
            print(subject.id)
            try:
                if subject.metadata[metadata_field] in subject_list:
                    dup_count += 1
                    duplicate_subjects.append(subject.id)
                    try:
                        subject_set.remove(subject.id)
                        dup_removed += 1
                    except panoptes_client.panoptes.PanoptesAPIException:
                        not_removed.append(subject.id)
                subject_list = subject_list | {subject.metadata[metadata_field]}
            except KeyError:
                no_metadata += 1

        print('Found ', len(subject_list), ' unique subjects in subject set ', subject_set_id)
        print('Found ', no_metadata, 'subjects with no metadata field as specified')
        print('Found ', dup_count, ' duplicate subjects in subject set ', subject_set_id)
        print('Removed ', dup_removed, ' duplicate subjects')
        print('Failed to remove ', len(not_removed), 'subjects')
        break
    except panoptes_client.panoptes.PanoptesAPIException:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
        if retry.lower() == 'n':
            quit()

while True:
    print('Preparing to create file listing remaining subjects')
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
remaining = 0
with open(location + os.sep + subject_set.display_name + '_subjects.csv', 'wt') as file:
    print('locating subjects to include, this can take a few minutes!')
    for subject in subject_set.subjects:
        remaining += 1
        print(subject.id)
        file.write(subject.id + ',' + list(subject.metadata.values())[0] + '\n')
    print(remaining, 'subjects found in the subject set, see the full list in '
                     '{0}_subjects.csv.' .format(subject_set.display_name))
