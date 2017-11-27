""" This version of the uploader has been modified as best I am able to run in Python 2.7. 
 It has not been tested and likely contains errors but the basic structure and specifically the 
 Panoptes client related code should be solid.  At the very least it should be a good starting 
 point for a python 2.7 version of the subject uploader"""
import os
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='pmason/fossiltrainer')

while True:
    location = raw_input('Enter the full path for the image directory, or enter ".." '
                     'to use the current directory' + '\n')
    if location == '..':
        location = os.getcwd()
        break
    else:
        if os.path.exists(location):
            break
        else:
            print 'That entry is not a valid path for an existing directory'
            retry = raw_input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

# load the list of image files found in the directory:
file_types = ['jpg', 'jpeg', 'png', 'gif', 'svg']
subject_metadata = {}
with os.scandir(location) as directory:
    for entry in directory:
        if entry.name.partition('.')[2] in file_types:
            subject_metadata[location + os.sep + entry.name] = {'Filename': entry.name}

print 'Found ', len(subject_metadata), ' files to upload in this directory.'

set_name = raw_input('Entry a name for the subject set to use or create:' + '\n')

try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print 'You have chosen to upload ', len(subject_metadata), ' files to an existing subject set',  set_name
    retry = raw_input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
except panoptes_client.panoptes.PanoptesAPIException:
    print 'You have chosen to upload ', len(subject_metadata), ' files to an new subject set ',  set_name
    retry = raw_input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    #  subject_set.save()

print 'Uploading subjects, this could take a while!'
new_subjects = []
for file, metadata in subject_metadata.items():
    try:
        subject = Subject()
        subject.links.project = project
        subject.add_location(file)
        subject.metadata.update(metadata)
        #  subject.save()
        print(file)
        new_subjects.append(subject)
    except panoptes_client.panoptes.PanoptesAPIException:
        print 'An error occurred during the upload of ', file
print len(new_subjects), 'new subjects created and uploaded'
try:
    #  subject_set.add(new_subjects)
    pass
except panoptes_client.panoptes.PanoptesAPIException:
    print 'subjects did not link correctly'

uploaded = 0
with open(location + os.sep + 'Uploaded subjects.csv', 'wt') as file:
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        file.write(subject.id + ',' + (subject.metadata.values())[0] + '\n')
    print uploaded, ' subjects found in the subject set, see the full list in Uploaded subjects.csv.'
