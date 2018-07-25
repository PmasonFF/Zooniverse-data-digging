""" This version is written in Python 3.66
This script attempts to retrieve the exif data from existing subject image files
and add the datetime to the subject metadata. It requires the project owner credentials
to be set up as OS environmental variables, and an appropriate project slug modified
on line 11.  depending on the camera used to take the original subject image the exif
code may be different than that in the code and may need to be modified"""
import os
from PIL import Image, ExifTags
import panoptes_client
from panoptes_client import SubjectSet, Project, Panoptes
import requests
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='pmason\fossiltrainer')

while True:
    set_id = input('Entry subject set id to update:' + '\n')
    try:
        subject_set = SubjectSet.find(set_id)
        count_subjects = 0
        subject_list = []
        for subject in subject_set.subjects:
            count_subjects += 1
            if subject.metadata['DateTime'] == '':
                try:
                    img = Image.open(requests.get(subject.locations[0]['image/jpeg'], stream=True).raw)
                    exif_dict = img._getexif()
                    date_time = exif_dict[306]
                except (IOError, KeyError):
                    print('Acquiring exif data for ', subject.id, ' failed')
                    continue
                subject.metadata['DateTime'] = date_time
                print(subject.id, subject.metadata['DateTime'], ' fixed')
                subject.save()
            else:
                print(subject.id, subject.metadata['DateTime'])
        break
    except panoptes_client.panoptes.PanoptesAPIException:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
        if retry.lower() == 'n':
            quit()
