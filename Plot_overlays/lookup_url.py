""" This script uses the subject download and pulls out subjects and their
corresponding url based on a workflow and subject set.  This creates a look-up
list to be used to retrieve the subject images from zooinverse using the url"""
import csv
import sys
import json

csv.field_size_limit(sys.maxsize)

#  These file names and locations must be customized for your particular use.
location = r'C:\py\AASubject\amazon-aerobotany-subjects.csv'
locationout = r'C:\py\AASubject\lookup_list_subject_url.csv'

with open(locationout, 'w', newline='') as file:
    fieldnames = ['subject_id', 'url']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    with open(location, 'r') as subject_file:
        reader = csv.DictReader(subject_file)
        for line in reader:
            if line['subject_set_id'] == '7369' and line['workflow_id'] == '3130':
                line['locations'] = json.loads(line['locations'])
                url = line['locations']["0"]
                new_row = {'subject_id': line['subject_id'], 'url': url}
                print(new_row)
                writer.writerow(new_row)
                subject = line['subject_id']
