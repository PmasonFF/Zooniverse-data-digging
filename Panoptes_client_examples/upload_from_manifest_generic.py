# -*- coding: utf-8 -*-

import argparse
import textwrap
import csv
import os
import io
from datetime import datetime
import validators
from run_config import Runconfig  # a copy is included in this repository
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
            This script is an generic uploader using a manifest.  It requires a 
            manifest in a specific format. It builds single or multiframe subjects 
            subjects with the metadata consisting of a unique identifier from the first 
            column, additional metadata fields and the path and file names of the media 
            or the remote https locations hosting the media in a variable number of 
            additional columns.  Local media can be of any mime supported by zooniverse,
            but hosted media must all be of one mime type - image/jpeg.  Unlike the CLI,
            it can handle variation in the number of frames in the subjects being uploaded.
            
            Subjects are uploaded to a specified subject set that exists or is created 
            in the project. The script reports errors that occurred and is restartable
            without subject duplication. Optionally a summary file of all subjects 
            successfully uploaded can be produced and saved.
            
            This script requires a copy of the script run_config.py to be in the same 
            directory as this script.
            The first time this script is run, run_config.py will be called up to to build
            a file called run_config.csv. This will ask four questions:
            - for the directory of where the project data files reside (generally where you
            will keep this script and other files associated with the project including the 
            summary file if requested,
            - your zooniverse username,
            - your zooniverse password, and,
            - the project slug for your project.  
            The run_config.csv file will store your password in an encrypted format.  To 
            retrieve the password in plain text to send it to zooniverse the exact copy of
            run_config.py file used to encrypt it is required  - anyone with BOTH the 
            run_config.csv and the exact run_config.py used to create it can retrieve the 
            password, but both the matching pair are needed.  Deleting the run_config.csv 
            file will result in a new file being built the next time this script is run, 
            and run_config.py will be updated with with the new encryption key.
            
            NOTE: You may use a file to hold the command-line arguments like:
            @/path/to/args.txt."""))

parser.add_argument('--manifest', '-m', required=True,
                    help="""The manifest is required. The manifest must be a csv file using 
                    commas as the delimiter. It must have a unique identifier (ie different for
                    every subject in the subject set) in the very first column column and 
                    additional metadata fields including the full path and file names of the local 
                    media or the remote https locations hosting the media in a variable number 
                    of additional columns.
                    The manifest file must be placed in the directory specified in the 
                    run_config.csv file. 
                    example -m FISHc_Pages_Standard_Manifest.csv""")
parser.add_argument('--subject_set', '-s', required=False, default='New subject set',
                    help="""The name of the subject set to create for or to add the uploaded
                    subjects to. This argument is optional and defaults to "New subject set".
                    This name can be edited via the project builder. If the script is being
                    restarted with the intention of adding more subjects to an existing set,
                    the subject_set name must be exactly the same. 
                    example -s "A different set" (note quotes)  """)
parser.add_argument('--save_to', '-f', required=False, default='None',
                    help="""An optional file name (including extension ".csv" where the
                    summary of the subjects uploaded will be saved in csv format. This
                    file will be placed in the directory specified in the run_config.csv file
                    example -f summary_file.csv """)
args = parser.parse_args()

manifest = args.manifest
set_name = args.subject_set
save_to = args.save_to

directory = Runconfig().working_directory

save = False
if '.csv' in save_to:
    save = True

# parts of the optional summary file are built and either printed or added to the summary file
build_file = ''
build_part = "Subject uploader for project" + Runconfig().project_slug + '\n'
build_part += "Manifest = {}   Subject_Set Name = {}".format(manifest, set_name) + '\n' + '\n'

build_part += 'Loading manifest:' + '\n'
with open(directory + os.sep + manifest, 'r') as m_file:
    r = csv.DictReader(m_file)
    manifest_header = r.fieldnames
    manifest_list = []
    total_rows = 0
    for row in r:
        manifest_line = {manifest_header[0]: row[manifest_header[0]]}
        for i in range(1, len(row)):
            if row[manifest_header[i]]:
                manifest_line[manifest_header[i]] = row[manifest_header[i]]

        manifest_list.append(manifest_line)
        total_rows += 1
    build_part += '\n'

# connection and login for the project:
Panoptes.connect(username=Runconfig().username, password=Runconfig().password)
project = Project.find(slug=Runconfig().project_slug)

#  This section sets up a subject set
previous_subjects = []
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    build_part += 'You have chosen to upload {} subjects to an existing subject set {}'.format(total_rows, set_name) \
                  + '\n'
    print(build_part)
    retry = input('Enter "n" to cancel this upload, any other key to continue;' + '\n')
    if retry.lower() == 'n':
        quit()
    if save:
        build_file += build_part
    # get listing of previously uploaded subjects
    print('Please wait while the existing subjects are determined, this can take approximately one minute per '
          '400 previous subjects depending on the connection speed and zooinverse workload')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata[manifest_header[0]])
    build_part = '{} subjects found in this set'.format(len(previous_subjects)) + '\n'
    print(build_part)
    if save:
        build_file += build_part
except StopIteration:
    # create a new subject set link it to the project above
    build_part += 'You have chosen to upload {} subjects to a new subject set {}'.format(total_rows, set_name) + '\n'
    print(build_part)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    if save:
        build_file += build_part
    # nothing happens until the subject_set.save(). For testing comment out that line
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
    working_on = metadata[manifest_header[0]]
    build_part = 'working on {}'.format(working_on) + '\n'
    #  test for previously uploaded
    if metadata[manifest_header[0]] not in previous_subjects:
        try:
            subject = Subject()
            subject.links.project = project
            #  find the files in the metadata and add their locations
            for field in manifest_header:
                try:
                    if validators.url(metadata[field]):
                        subject.add_location({'image/jpeg': metadata[field]})
                    elif metadata[field].split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif',
                                                                    'svg', 'mp3', 'm4a', 'mpeg',
                                                                    'mp4', 'txt', 'json']:
                        subject.add_location(metadata[field])
                except KeyError:
                    continue
            # update subject metadata
            subject.metadata.update(metadata)
            build_part += str(metadata) + '\n'
            # again nothing happens until these two lines below, comment them out for testing
            subject.save()
            subject_set.add(subject.id)
            new_subjects += 1
            build_part += '{} successfully uploaded at {}'.format(working_on, str(datetime.now())[0:19]) + '\n'
        except panoptes_client.panoptes.PanoptesAPIException:
            failed_subjects += 1
            build_part += 'An error occurred during the upload of {}'.format(working_on) + '\n'
    else:
        old_subjects += 1
        build_part += '{} previously uploaded'.format(working_on) + '\n'
    print(build_part, end='')
    if save:
        build_file += build_part

build_part = '\n' + '\n' + '\n' + 'Of {} subjects listed in the manifest -'.format(total_rows) + '\n'
build_part += '{} new subjects were created and uploaded'.format(new_subjects) + '\n'
build_part += '{} subjects were already uploaded and {} subjects failed to upload' \
                  .format(old_subjects, failed_subjects) + '\n'

print(build_part)
if save:
    build_file += build_part
#  test for the optional summary output
if save:
    output(directory + os.sep + save_to, build_file)
#  ____________________________________________________________________________________________________________________
