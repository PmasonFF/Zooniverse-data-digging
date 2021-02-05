""" Requires packages ffmpy, ffprobe-python, and panoptes_client. ffmpy requires a functioning FFmpeg installation
with the location of ffmpeg/bin included in the Path environmental variables

Sets up subjects with metadata as follows:
subject.metadata['Site_Date'] = set_name
subject.metadata['Filename'] = original_file name
subject.metadata['Date_time'] = datetime as found from the video created at time

Original video files are truncated at 10 seconds and reduced to one of two optional commonly used formats """

import os
import json
import ffmpy
from ffprobe import FFProbe
import panoptes_client  # to interact with zooniverse
from panoptes_client import SubjectSet, Subject, Project, Panoptes


def get_files_in(folder):  # get list of files to upload
    file_types = ['avi']  # this script is expecting .avi files and would need slight modifications for other video.
    file_listing = []
    for entry in os.listdir(folder):  # opens the directory and gets a list of all .avi files in it.
        if entry.partition('.')[2].lower() in file_types:
            file_listing.append(entry)
    return file_listing


def compress(original_location):  # converts video container and reduces file size
    inp = {original_location: None}
    # outp = {'temp.mp4': '-loglevel 8 -t 10 -vf scale=640:480 -pix_fmt yuv420p -y'}  #  optional format
    outp = {'temp.mp4': '-loglevel 8 -t 10 -c:v libx264 -crf 33 -pix_fmt yuv420p -c:a aac -b:a 128k -y'}
    ff = ffmpy.FFmpeg(inputs=inp, outputs=outp)
    ff.run()
    return ff.run()


while True:  # interactive entry of the directory where the files are and the subject set name to use
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

print('Entry a name for the subject set to use or create.')
set_name = input('This will also be used as the Site-Date in the subject metadata:' + '\n')

# connect to zooniverse using a user_name and password previously stored as environmental variables in the user's OS
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])  # OR
# Panoptes.connect(username='actual_zooniverse_user_name', password='actual_zooniverse_password')  # NOT secure!!!!
project = Project.find(slug='pmason/fossiltrainer')  # project slug
#  needs to be changed for different projects

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
        previous_subjects.append(subject.metadata['Filename'])
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

for original_file in file_list:  # loop throught the file list
    # test if the file is already uploaded, if so skip it
    if original_file not in previous_subjects:
        # get data-time from original video file
        try:
            video_data = FFProbe(location + os.sep + original_file)
            datetime = video_data.metadata['creation_time']
        except (IOError, KeyError, TypeError):
            print('Acquiring exif data for ', original_file, ' failed')
            datetime = ''

        # finally we are ready for the actual upload of the modified file:
        try:
            subject = Subject()
            subject.links.project = project
            compress(location + os.sep + original_file)
            print('Compressed ', original_file, 'to', os.path.getsize('temp.mp4'), 'bytes, uploading....')
            subject.add_location('temp.mp4')
            videos_uploaded += 1
            # update the subject metadata (add '#' to the beginning of the field name to hide that field)
            subject.metadata['Site_Date'] = set_name
            subject.metadata['Filename'] = original_file
            subject.metadata['Date_time'] = datetime
            # nothing is actually uploaded to panoptes until the save is executed.
            # for testing without actually uploading anything comment out the following two lines
            subject.save()
            subject_set.add(subject.id)
        except panoptes_client.panoptes.PanoptesAPIException:
            print('An error occurred during the upload of ', original_file)
print(videos_uploaded, 'videos uploaded')
# cleanup the temporary file at the end
if os.path.isfile('temp.mp4'):
    os.remove('temp.mp4')

uploaded = 0
#  generate a report and save it to disk for the subjects actually uploaded
#  note metadata field names MUST match those used above, This section can be commented out if not required
with open(location + os.sep + 'Uploaded_' + set_name + '.csv', 'wt') as upfile:
    upfile.write('subject.id' + ',' + 'Metadata' + '\n')
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        upfile.write(subject.id + ',' + json.dumps(subject.metadata) + '\n')
    print(uploaded, ' subjects found in the subject set, see the full list in Uploaded_' + set_name + '.csv')
