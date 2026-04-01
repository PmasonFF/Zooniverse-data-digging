
import os
import sys
import csv
from os.path import join
import ffmpy
from ffprobe import FFProbe
from datetime import datetime
import panoptes_client  # to interact with zooniverse
from panoptes_client import SubjectSet, Subject, Project, Panoptes

""" This script accepts a top directory and acquires all the .avi videos in that directory and any sub-directories
It splits out the directory name each file is in to be used as the Site_Date and added to the subject metadata.
It then accept a subject set name and if the subject aet exists it get a listing of the videos in the set by 
Site_date and filename (note different cameras may generate identical filenames so Site_Date and filename is required.

Once the listing and subject set is known, the script steps through the list of files, extracting date_time information
from the video file's exif and then the video is compressed to a known codec, format and frame rate that plays well on 
most browsers.  The subject is uploaded (subject.save()) and then added to the subject set.  If this step fails - 
usually due to stale object or connection issues with zooniverse, the script will try to reconnect with zooniverse, 
initiate a new subject set instance, and try the subject save and subject set add a second time.

If this script fails or is interrupted, it may be restarted with the same directory and subject set name,  it takes 
time (~ one minute/400 subjects) but it will resume where it left off without duplication any subjects.  This can 
become impractical for large subject sets with several thousand subjects.

Finally there is a summary file produced listing all the subjects a that were created. Again this is becomes a slow 
process for larger sets.

Version 0.0.0

0.0.0 - added retry to version 0.4.0 of subject_video_uploader_woodpeckers_sub_dir .py
"""


def get_files_in(folder):  # get list of files to upload
    file_types = ['avi']  # this script is expecting .avi files and would need slight modifications for other video.
    file_listing = []
    for root, dirs, files in os.walk(folder):  # opens the directory and gets a list of all .avi files in it.
        for name in files:
            if name.partition('.')[2].lower() in file_types:
                file_listing.append((root.split(os.sep)[-1], root, name))
    return file_listing


def compress(original_location):  # converts video container and reduces file size
    inp = {original_location: None}
    # outp = {'temp.mp4': '-loglevel 8 -t 10 -vf scale=640:480 -pix_fmt yuv420p -y'}
    outp = {'temp.mp4': '-loglevel 8 -t 10 -c:v libx264 -crf 33 -pix_fmt yuv420p -c:a aac -b:a 128k -y'}
    ff = ffmpy.FFmpeg(inputs=inp, outputs=outp)
    ff.run()
    return ff.run()


while True:  # interactive entry of the directory where the video subdirectories are located, and a subject set name
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

while True:
    set_name = input('Entry a name for the subject set to use or create.' + '\n')
    if type(set_name) is str and 5 <= len(set_name) <= 60:  # test for valid string
        break
    else:
        print('That entry is not a valid name for a subject set. ' + '\n'
              + r'(name must be a text string 5 to 60 characters long with no special characters eg \n)')
        retry = input('Enter "y" to try again, any other key to exit' + '\n')
        if retry.lower() != 'y':
            quit()

# connect to zooniverse using a user_name and password previusly stored as environmental variables in the user's OS
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='elwest/woodpecker-cavity-cam')
# project = Project.find(slug='pmason/fossiltrainer')  # project slug

file_list = get_files_in(location)  # go get the file list
number = len(file_list)
previous_subjects = []
try:
    # check if the subject set already exits:
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', number, ' videos to an existing subject set', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    print('Checking for previously uploaded subjects, this could take a while!')
    for subject in subject_set.subjects:  # if the subject set does exist get a listing of what is in it
        previous_subjects.append(subject.metadata['Site_Date'] + subject.metadata['Filename'])
except StopIteration:
    print('You have chosen to upload ', number, ' videos to an new subject set ', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # if not, create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Uploading subjects, this could take a while!')
videos_uploaded = 0

for site_date, path, original_file in file_list:  # loop through the file list
    # test if the file is already uploaded, if so skip it
    if site_date + original_file not in previous_subjects:
        # get data-time from original video file
        try:
            video_data = FFProbe(path + os.sep + original_file)
            date_time = video_data.metadata['creation_time']
        except (IOError, KeyError, TypeError):
            print('Acquiring exif data for ', original_file, ' failed')
            date_time = ''

        # finally we are ready for the actual upload of the modified file:
        try:
            compress(join(path, original_file))
            print('Compressed ', original_file, 'to', os.path.getsize('temp.mp4'), 'bytes, uploading....')
        except (OSError, ffmpy.FFRuntimeError):
            print(original_file, 'Failed on compression -', str(sys.exc_info()[1]))
            quit()
        subject = Subject()
        subject.links.project = project
        subject.add_location('temp.mp4')
        # update the subject metadata (add '#' to the beginning of the field name to hide that field)
        subject.metadata['Site_Date'] = site_date
        subject.metadata['Filename'] = original_file
        subject.metadata['Date_time'] = date_time

        try:
            subject.save()
            subject_set.add(subject.id)
            videos_uploaded += 1
        except panoptes_client.panoptes.PanoptesAPIException:
            print('Retry for', original_file, str(sys.exc_info()[1]))
            Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
            subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
            try:
                subject.save()
                subject_set.add(subject.id)
                print('Successful on retry')
                videos_uploaded += 1
            except panoptes_client.panoptes.PanoptesAPIException:
                print('An error occurred during the upload of ', original_file, str(sys.exc_info()[1]))

print(videos_uploaded, 'videos uploaded')
# cleanup the temporary file at the end
if os.path.isfile('temp.mp4'):
    os.remove('temp.mp4')

uploaded = 0
#  generate a report and save it to disk for the subjects actually uploaded
#  note metadata field names MUST match those used above, This section can be commented out if not required
print('Preparing summary file, please wait...')

with open(location + os.sep + 'Uploaded_' + set_name + '_' + str(datetime.now())[0:10]
          + '.csv', 'w', newline='') as file:
    fieldnames = ['zoo_subject', 'Site_Date', 'Filename', 'Date_time']
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
