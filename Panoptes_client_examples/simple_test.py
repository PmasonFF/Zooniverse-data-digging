import os
from panoptes_client import SubjectSet, Panoptes
print(os.environ['User_name'])
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

subject_set_id = input('Enter subject set id' + '\n')
print(subject_set_id)
subject_set = SubjectSet.find(subject_set_id)
print(subject_set)
