# -*- coding: utf-8 -*-

import argparse
import textwrap
import csv
import os
import io
import panoptes_client
from panoptes_client import Panoptes, Project, Subject, SubjectSet


# where the optional summary is output:
def output(location, build):
    with io.open(location, 'w', encoding='utf-8', newline='') as out_file:
        out_file.write(build)
    return


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""
            This script is an uploader customized for the project skink-spotter-nz.
            It requires a manifest in a specific format. It builds multiframe image 
            subjects with the metadata a subject number and the image filenames.
            Subjects are uploaded to a specified subject set that exists or is created 
            in the project. The script reports errors that occurred and is restartable
            without subject duplication. Optionally a summary file of all subjects 
            successfully uploaded can be produced and saved.
            To connect to panoptes the zooniverse user_name and password must be stored
            in the users operating system environmental variables USERNAME and PASSWORD.
            If this is not the case line 103 must be modified to the form 
            Panoptes.connect(username='jovirens', password='actual-password'), and 
            steps must be taken to protect this script.
            NOTE: You may use a file to hold the command-line arguments like:
            @/path/to/args.txt."""))

parser.add_argument('--manifest', '-m', required=True,
                    help="""The manifest is required. It must list the image files to 
                    be uploaded in columns headed image1 through image10, and may have 
                    an additional column 'subject' Give the full path (from the 
                    directory where this script is run, or from the root directory) and 
                    the file name. The manifest must be a csv file using commas as the
                    delimiter.
                    example -m C:\py\Skinks\manifest.csv""")
parser.add_argument('--image_directory', '-d', required=True,
                    help="""The directory where the images files are to be found. Give the
                    full path (from the directory where this script is run, or from the
                    root directory)
                    example -d C:\py\Skinks\images  """)
parser.add_argument('--subject_set', '-s', required=False, default='New subject set',
                    help="""The name of the subject set to create for or to add the uploaded
                    subjects to. This argument is optional and defaults to "New subject set".
                    This name can be edited via the project builder. If the script is being
                    restarted with the intention of adding more subjects to an existing set,
                    the subject_set name must be exactly the same. 
                    example -s "A different set" (note quotes)  """)
parser.add_argument('--save_to', '-f', required=False, default='None',
                    help="""An optional file name (including extension ".csv"
                    where the summary of the subjects uploaded will be saved in csv format.
                    Give the full path (from the directory where this script is run, or from the
                    root directory) and the file name. 
                    example -s some_path\summary_file.csv """)
args = parser.parse_args()

manifest = args.manifest
set_name = args.subject_set
save_to = args.save_to
directory = args.image_directory

save = False
if '.csv' in save_to:
    save = True

# parts of the optional summary file are built and either printed or added to the summary file
build_file = ''
build_part = "Subject uploader for project 'jovirens/skink-spotter-nz'" + '\n'
build_part += "Manifest = {}   Image Directory = {}    Subject_Set Name = {}   Save location = {}" \
                  .format(manifest, directory, set_name, save_to) + '\n' + '\n'

manifest_header = ['subject', 'image1', 'image2', 'image3', 'image4',
                   'image5', 'image6', 'image7', 'image8', 'image9', 'image10']

build_part += 'Loading manifest and checking files exist:' + '\n'
with open(manifest, 'r') as m_file:
    r = csv.DictReader(m_file)
    manifest_list = []
    total_rows = 0
    for row in r:
        manifest_line = {'subject': int(row['subject'])}
        for i in range(1, len(row)):
            if row[manifest_header[i]]:
                if os.path.isfile(directory + os.sep + row[manifest_header[i]]):
                    manifest_line[manifest_header[i]] = row[manifest_header[i]]
                else:
                    build_part += 'File {} in subject {} not found'. \
                                      format(row[manifest_header[i]], row['subject']) + '\n'
        manifest_list.append(manifest_line)
        total_rows += 1
    build_part += '\n'

# connection and login for the project:
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
# project = Project.find(slug='jovirens/skink-spotter-nz')
project = Project.find(slug='pmason/fossiltrainer')

#  This section sets up a subject set
previous_subjects = []
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    build_part += 'You have chosen to upload {} subjects to an existing subject set {}'.format(total_rows, set_name)\
                  + '\n'
    print(build_part)
    retry = input('Enter "n" to cancel this upload, any other key to continue;' + '\n')
    if retry.lower() == 'n':
        quit()
    if save:
        build_file += build_part
    # get listing of previously uploaded subjects
    print('Please wait while the existing subjects are determined, this can take up to several minutes')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['image1'])
    build_part = '{} subjects found in this set'.format(len(previous_subjects)) + '\n'
    print(build_part)
    if save:
        build_file += build_part
except StopIteration:
    # create a new subject set link it to the project above
    build_part += 'You have chosen to upload {} subjects to an new subject set {}'.format(total_rows, set_name) + '\n'
    print(build_part)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    if save:
        build_file += build_part
    # nothing happens until the subject_set.save() for testing comment out that line
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Uploading subjects, This could take a while!')
new_subjects = 0
old_subjects = 0
failed_subjects = 0
working_on = []
#  loop over the preloaded manifest file
for metadata in manifest_list:
    working_on = [metadata['subject'], metadata['image1']]
    #  test for previously uploaded
    if metadata['image1'] not in previous_subjects:
        try:
            subject = Subject()
            subject.links.project = project
            #  find the files in the metadata listing and add their locations
            for file in list(metadata.values())[1:]:
                if file.find('.jpg') > 0:
                    subject.add_location(directory + os.sep + file)
            # update subject metadata
            subject.metadata.update(metadata)
            # again nothing happens until these wo line below, comment them out for testing
            subject.save()
            subject_set.add(subject.id)
            new_subjects += 1
            build_part = '{} successfully uploaded'.format(working_on) + '\n'
        except panoptes_client.panoptes.PanoptesAPIException:
            failed_subjects += 1
            build_part = 'An error occurred during the upload of {}'.format(working_on) + '\n'
    else:
        old_subjects += 1
        build_part = '{} previously uploaded'.format(working_on) + '\n'
    print(build_part, end='')
    if save:
        build_file += build_part

build_part = 'Of {} subjects listed in the manifest -'.format(total_rows) + '\n'
build_part += '{} new subjects were created and uploaded'.format(new_subjects) + '\n'
build_part += '{} subjects were already uploaded and {} subjects failed to upload'\
                  .format(old_subjects, failed_subjects) + '\n'

print(build_part)
if save:
    build_file += build_part
#  test for the optional summary output
if save:
    output(save_to, build_file)
#  ____________________________________________________________________________________________________________________
