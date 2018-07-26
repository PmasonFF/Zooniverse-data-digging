import csv
import os

from panoptes_client import SubjectSet, Subject, Project, Panoptes

#  modify path and file name as needed:
manifest_file = r'C:\py\Data_digging\Panoptes_client\manifest.csv'

# set up zooniverse User_name and password as environmental variables
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

#  modify project slug as needed:
project = Project.find(slug='pmason/fossiltrainer')

#  modify subject set name as needed:
set_name = 'test_url'


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

# This section adds subjects from a manifest to the above subject set
with open(manifest_file, 'r') as mani_file:
    r = csv.DictReader(mani_file)
    for line in r:
        subject = Subject()
        subject.links.project = project

        #  modify the next three lines with the appropriate column headers from the manifest file
        subject.add_location({'image/jpeg': line['link']})
        subject.metadata['subject_id'] = line['subject_id']
        subject.metadata['image_name'] = line['image_name']
        subject.save()
        subject_set.add(subject.id)
