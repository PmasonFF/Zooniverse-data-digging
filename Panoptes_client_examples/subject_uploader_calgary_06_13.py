""" This version is written in Python 3.62,  This version checks the images in the
 manifest are actually in the directory, and produces the summary file of what is uploaded
 or not image by image as they are uploaded, with a status for each image in the manifest"""
import os
import csv
from PIL import Image
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes

file_info = ''
while True:
    directory = input('Enter the full path for the directory where the file information resides, or enter "." '
                      'to use the current directory' + '\n')
    if directory == '.':
        directory = os.getcwd()
        break
    else:
        if os.path.exists(directory):
            break
        else:
            print('That entry is not a valid path for an existing directory')
            retry = input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

while True:
    file_info = input('Enter the file name for the file with the information on the images to upload' + '\n')
    if os.path.isfile(directory + os.sep + file_info):
        print(directory + os.sep + file_info)
        break
    else:
        print('That entry is not a valid path and file name for an existing file')
        retry = input('Enter "y" to try again, any other key to exit' + '\n')
        if retry.lower() != 'y':
            quit()

while True:
    set_name = input('Entry a name for the subject set to use or create:' + '\n')
    if set_name != '':
        break
    else:
        print('You have not entered a  valid set name (can not be blank)')
        retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
        if retry.lower() == 'n':
            quit()

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
#  project = Project.find(slug='calgary-captured/calgary-captured')
project = Project.find(slug='pmason/fossiltrainer')

with open(directory + os.sep + file_info) as in_file:
    countrdr = csv.DictReader(in_file)
    totalrows = 0
    for row in countrdr:
        totalrows += 1
    in_file.seek(0)
    previous_subjects = {}
    try:
        # check if the subject set already exits
        subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
        print('You have chosen to upload ', totalrows, ' files to an existing subject set', set_name)
        retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
        if retry.lower() == 'n':
            quit()
        print('Please wait while the existing subjects are determined, this can take up to several minutes')
        for subject in subject_set.subjects:
            previous_subjects[subject.metadata['img']] = subject.id
        print(len(previous_subjects), ' subjects found in this set')
    except StopIteration:
        print('You have chosen to upload ', totalrows, ' files to an new subject set ', set_name)
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
    old_subjects = 0
    failed_subjects = 0
    with open(directory + os.sep + 'Subjects summary_' + file_info, 'w', newline='') as file:
        fieldnames = ['img_id',
                      'subject_id',
                      'img',
                      'cam_id',
                      'date',
                      'status',
                      ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        working_image = ''
        try:
            infile = csv.DictReader(in_file)
            for row in infile:
                working_image = row['NewName']
                if os.path.isfile(directory + os.sep + row['NewName']):
                    subject_metadata = {'img': row['NewName'], 'date': row['Date'],
                                        'cam_id': row['CameraID'], 'img_id': row['ImageID']}
                    try:
                        if row['NewName'] not in list(previous_subjects.keys()):
                            subject = Subject()
                            subject.links.project = project
                            subject.add_location(directory + os.sep + row['NewName'])
                            subject.metadata.update(subject_metadata)
                            subject.save()
                            subject_set.add(subject.id)
                            new_subjects += 1
                            print(row['NewName'], ' successfully uploaded')
                            writer.writerow({'subject_id': subject.id,
                                             'img_id': subject.metadata['img_id'],
                                             'cam_id': subject.metadata['cam_id'],
                                             'img': subject.metadata['img'],
                                             'date': subject.metadata['date'],
                                             'status': 'uploaded'
                                             })
                        else:
                            old_subjects += 1
                            print(row['NewName'], ' previously uploaded')
                            writer.writerow({'subject_id': previous_subjects[row['NewName']],
                                             'img_id': '',
                                             'cam_id': '',
                                             'img': row['NewName'],
                                             'date': '',
                                             'status': 'previously uploaded'
                                             })
                    except panoptes_client.panoptes.PanoptesAPIException:
                        failed_subjects += 1
                        print('An error occurred during the upload of ', row['NewName'])
                        writer.writerow({'subject_id': '',
                                         'img_id': '',
                                         'cam_id': '',
                                         'img': row['NewName'],
                                         'date': '',
                                         'status': 'failed to upload'
                                         })
                else:
                    failed_subjects += 1
                    print('Image file not found', row['NewName'])
                    writer.writerow({'subject_id': '',
                                     'img_id': '',
                                     'cam_id': '',
                                     'img': row['NewName'],
                                     'date': '',
                                     'status': 'image file not found'
                                     })
        except:
            print('script crashed for unknown reason during processing of ', working_image)
        print('Of', totalrows, 'images listed in the manifest,')
        print(new_subjects, 'new subjects created and uploaded')
        print(old_subjects, 'were already uploaded and', failed_subjects, 'failed to upload')
