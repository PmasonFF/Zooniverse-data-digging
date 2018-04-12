""" This version is written in Python 3.62"""

import os
from panoptes_client import SubjectSet, Project, Panoptes

# edit this line for your directory path:
directory_path = r'C:\py\Data_digging\Panoptes_client'

# set up your zooniverse sign-in credentials as environment variables:
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
# edit the project slug for your project:
project = Project.find(slug='rainforestexpeditions/amazon-aerobotany')

while True:
    set_name = input('Entry a name for the subject set to use' + '\n')
    try:
        # check if the subject set already exits
        subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
        retry = input('Subject set found, Enter "n" to cancel this quiry, any other key to continue' + '\n')
        if retry.lower() == 'n':
            quit()
        break
    except StopIteration:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to try again' + '\n')
        if retry.lower() == 'n':
            quit()

listed = 0
location = directory_path + os.sep + 'Subjects_' + set_name + '.csv'
with open(location, 'wt') as file:
    for subject in subject_set.subjects:
        listed += 1
        print(subject.id, list(subject.metadata.values())[0])
        file.write(subject.id + ',' + list(subject.metadata.values())[0] + '\n')
    print(listed, ' subjects found in the subject set, see the full list in', location)
