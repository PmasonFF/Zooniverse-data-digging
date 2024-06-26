import csv
import os

from panoptes_client import SubjectSet, Subject, Project, Panoptes

#  modify path and file name as needed:
manifest_file = r'C:\py\Project_postcard\tinder-add-manifest - original.csv'

# set up zooniverse User_name and password as environmental variables
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
#  modify project slug as needed:
project = Project.find(slug='pmason/fossiltrainer')

#  modify subject set name as needed:
set_name = 'Test_panoptes_upload'

# This section sets up a subject set
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
except StopIteration:
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

# Add a subjects from a manifest to the above subject set
with open(manifest_file, 'r') as mani_file:
    r = csv.DictReader(mani_file)
    for line in r:
        subject = Subject()
        subject.links.project = project
        subject.locations = [{'image/jpeg': line['#image1']}, {'image/jpeg': line['#image2']}]
        subject.metadata['subject_id'] = line['id']
        subject.metadata['#image1'] = line['#image1']
        subject.metadata['#image2'] = line['#image2']
        subject.metadata['County/State'] = line['County/State']
        subject.metadata['Location'] = line['Location']
        print('Uploading subject', line['id'])
        subject.save()
        subject_set.add(subject.id)
