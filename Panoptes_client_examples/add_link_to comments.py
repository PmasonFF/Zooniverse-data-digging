""" This version is written in Python 3.66
This script adds a link to the comments in a subject's metadata which oopens in a new
tab. This allows one to comment while classifying. It requires the project owner credentials
to be set up as OS environmental variables, and an appropriate project slug modified
on line 12. """
import os
from PIL import Image, ExifTags
import panoptes_client
from panoptes_client import SubjectSet, Project, Panoptes
import requests
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project_slug = 'insert project slug here'
project = Project.find(slug=project_slug)

while True:
    set_id = input('Entry subject set id to modify:' + '\n')
    try:
        subject_set = SubjectSet.find(set_id)
        count_subjects = 0
        subject_list = []
        for subject in subject_set.subjects:
            count_subjects += 1
            link = r'[Comments](+tab+https://www.zooniverse.org/projects/' \
                   + project_slug + r'/talk/subjects/' + str(subject.id) + ')'
            subject.metadata['Talk Pages'] = link
            print(subject.id, subject.metadata['Talk Pages'], ' added')
            subject.save()

        break
    except panoptes_client.panoptes.PanoptesAPIException:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
        if retry.lower() == 'n':
            quit()
