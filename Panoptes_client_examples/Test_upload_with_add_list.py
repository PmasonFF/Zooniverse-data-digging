import csv
import sys
import os
import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes

#  modify path and file name as needed:
manifest_file = r'C:\py\Project_postcard\tinder-add-manifest - original.csv'

# set up zooniverse User_name and password as environmental variables
Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
#  modify project slug as needed:
project = Project.find(slug='pmason/fossiltrainer')

#  modify subject set name as needed:
set_name = 'Test_panoptes_upload_3'

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
with open('Uploaded_' + set_name + '.csv', 'w', newline='') as file:
    fieldnames = ['zoo_subject', 'subject_id', '#image1', '#image2', 'County/State', 'Location']

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    with open(manifest_file, 'r') as mani_file:
        r = csv.DictReader(mani_file)
        for line in r:
            metadata = {'subject_id': line['id'],
                        '#image1': line['#image1'],
                        '#image2': line['#image2'],
                        'County/State': line['County/State'],
                        'Location': line['Location']}
            subject = Subject()
            subject.links.project = project
            subject.locations = [{'image/jpeg': line['#image1']}, {'image/jpeg': line['#image2']}]
            subject.metadata.update(metadata)
            print('Uploading subject', line['id'])
            subject.save()
            metadata['zoo_subject'] = subject.id
            writer.writerow(metadata)

print('Adding uploaded subjects to the subject set in batches of 100.  '
      'This can take a while, please allow the script to complete')
with open('Uploaded_' + set_name + '.csv') as file:
    subject_list = []
    subject_data = csv.DictReader(file)
    for line in subject_data:
        subject_list.append(int(line['zoo_subject']))
    flag = True
    j = 0
    while flag:
        if j + 100 > len(subject_list):
            end = len(subject_list)
        else:
            end = j + 100
            print('Adding batch', int(j/100) + 1)
        subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
        for redo in range(0, 3):
            try:
                subject_set.add(subject_list[j:end])
                flag = True
                break
            except panoptes_client.panoptes.PanoptesAPIException:
                print(str(sys.exc_info()[1]))
                print('retry', redo + 1, 'for batch', int(j / 100))
                subject_set.reload()
                flag = False
                continue
        if not flag:
            print('Maximum retries attempted, Not all subjects in the uploaded file were added to the subject set. '
                  'Please forward any error messages and the file Uploaded_' + set_name + '.csv')
        j += 100
        if j > len(subject_list):
            flag = False
print('Subjects uploaded and successfully added to the subject set')
