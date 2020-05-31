import csv
import os

from panoptes_client import SubjectSet, Subject, Project, Panoptes

#  modify path and file name as needed:
manifest_file = r'C:\py\list_of_subject_ids_to_add.csv'
# must have a column headed "subject_id" which is the list of subject to add/remove

# set up zooniverse User_name and password as environmental variables
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

#  modify subject set name as needed:
set_id = '12345'

# This section verifies and finds the subject set
try:
    # check if the subject set already exits
    subject_set = SubjectSet.find(set_id)
except StopIteration:
    print('Subject set', set_id, 'not found')
    quit()

# This section adds/removes subjects from a manifest to the above subject set
with open(manifest_file, 'r') as mani_file:
    r = csv.DictReader(mani_file)
    for line in r:
        subject_set.add(line['subject_id'])  #  note subjects can also be unlinked by changing "add" to "remove" in this line
        print(line['subject_id'])
