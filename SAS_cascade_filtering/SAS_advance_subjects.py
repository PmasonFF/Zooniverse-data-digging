# this script was written in Python 3.6.2 . It requires the panoptes_client to be installed as well.
import csv
import json
import os
import sys
import operator
import time
from panoptes_client import SubjectSet, Project, Panoptes
csv.field_size_limit(sys.maxsize)
# set up a UI to collect or verify information on what to analyse
try:
    mod_date = os.path.getmtime('snapshots-at-sea-classifications.csv')
    print('Classification download found, dated:')
    print(time.ctime(mod_date))
except OSError:
    print('Classification download not found in project directory!')
    quit()
try:
    mod_date = os.path.getmtime('snapshots-at-sea-subjects.csv')
    print('Subject download found, dated:')
    print(time.ctime(mod_date))
    choice = input('Do you want to use these files? "y" or "n"' + '\n')
    if choice.lower() != 'y':
        print('Download or move files as appropriate, and try again.')
        quit()
except OSError:
    print('Subject download not found in project directory!')
    quit()
class_location = 'snapshots-at-sea-classifications.csv'
subject_location = 'snapshots-at-sea-subjects.csv'

while True:
    choice = input('What stage do you want to analyse? "q1, q2, q3, or q4"' + '\n')
    if choice.lower() in ['q1', 'q2', 'q3', 'q4']:
        break
    else:
        choice = 'Q1'
        print('Input did not match expect options')
        get_out = input('Do you want to exit? "y" or "n"' + '\n')
        if get_out.lower() == 'y':
            quit()
step_to_analyse = choice.upper()

base_subject_set_id = '15195'
print('The default base data set is ', base_subject_set_id)
choice = input('Press "enter" to accept default, or enter another subject_set_id' + '\n')
if choice != '':
    base_subject_set_id = str(choice)

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
proj = Project.find(slug='tedcheese/snapshots-at-sea')
try:
    # check if the subject set already exits
    subj_set = SubjectSet.where(project_id=proj.id, subject_set_id=base_subject_set_id).next()
    print("Found base data set: {}.".format(subj_set.display_name))
    base_data_set = subj_set.display_name
except:
    base_data_set = ''
    print('base data subject set not found')
    quit()

advance_steps = {'Q1': [427, base_data_set.partition(' ')[0] + '_Q2_' + base_data_set.partition(' ')[2],
                        'least one', 5, .75],
                 'Q2': [433, base_data_set.partition(' ')[0] + '_Q3_' + base_data_set.partition(' ')[2],
                        'any whales', 5, .75],
                 'Q3': [505, base_data_set.partition(' ')[0] + '_Q4_' + base_data_set.partition(' ')[2],
                        'a fluke', 5, .45],
                 'Q4': [506, 'SAS_' + base_data_set, 'Humpback', 5, .5],
                 }
workflow = advance_steps[step_to_analyse][0]
set_name = advance_steps[step_to_analyse][1]
snippet = advance_steps[step_to_analyse][2]
retirement = int(advance_steps[step_to_analyse][3])
test_criteria = float(advance_steps[step_to_analyse][4])

print('Determining the range of subject_ids to include from the subjects download')
lower = 50000000
upper = 0
with open(subject_location) as sub_file:
    r = csv.DictReader(sub_file)
    for sub_row in r:
        if sub_row['subject_set_id'] == base_subject_set_id:
            subject_id = sub_row['subject_id']
            lower = min(int(subject_id), lower)
            upper = max(int(subject_id), upper)
location = 'sas_' + step_to_analyse + '_' + base_subject_set_id + '_' + time.strftime('%Y-%m-%d')
out_location = location + '_slice.csv'


def include(class_record):
    if int(class_record['workflow_id']) == workflow:
        pass  # where xxxx is the workflow to include.
    else:
        return False

    if upper >= int(class_record['subject_ids']) >= lower:
        pass
    else:
        return False
    return True


def sort_file(input_file, output_file_sorted, field):
    with open(input_file, 'r') as in_file:
        in_put = csv.reader(in_file, dialect='excel')
        headers = in_put.__next__()
        sort = sorted(in_put, key=operator.itemgetter(field))

        with open(output_file_sorted, 'w', newline='') as out_file:
            write_sorted = csv.writer(out_file, delimiter=',')
            write_sorted.writerow(headers)
            sort_counter = 0
            for line in sort:
                write_sorted.writerow(line)
                sort_counter += 1
    # clean up temporary file
    try:
        os.remove(input_file)
    except:
        print('temp file not found and deleted')
    return sort_counter


print('Select the desired classifications and extract question responses')
# Set up the output file structure with desired fields:
# prepare the output file and write the header
with open(out_location, 'w', newline='') as o_file:
    fieldnames = ['classification_id',
                  'user_name',
                  'workflow_id',
                  'workflow_version',
                  'task_answer',
                  'subject_ids']
    writer = csv.DictWriter(o_file, fieldnames=fieldnames)
    writer.writeheader()

    # this area for initializing counters, status lists and loading pick lists into memory:
    i = 0
    j = 0
    #  open the zooniverse data file using dictreader,  and load the more complex json strings as python objects
    with open(class_location) as f:
        r = csv.DictReader(f)
        for row in r:
            i += 1
            if i < 1250000:  # use this to loop through the older classifications quickly
                continue
            if include(row) is True:
                j += 1
                annotations = json.loads(row['annotations'])
                answer_1 = ''
                for task in annotations:
                    try:
                        if snippet in task['task_label']:
                            if task['value'] is not None:
                                answer_1 = str(task['value'])
                                if answer_1 == 'Yes':
                                    answer_1 = 1
                                else:
                                    answer_1 = 0
                    except KeyError:
                        continue

                # This set up the writer to match the field names above and the variable names of their values:
                writer.writerow({'classification_id': row['classification_id'],
                                 'user_name': row['user_name'],
                                 'workflow_id': row['workflow_id'],
                                 'workflow_version': row['workflow_version'],
                                 'task_answer': answer_1,
                                 'subject_ids': row['subject_ids']})

# This area prints some basic process info and status
print(i, 'lines read and inspected', j, 'records processed')

print(sort_file(out_location,
                location + '_sorted.csv', 5), 'lines sorted and written to file')


def process_aggregation(subj, cl_counter, workflo_id, workflo_version, ag_answer, subjs_to_add):
    if ag_answer/cl_counter >= test_criteria:
        out_put_1 = 'advance'
        out_put_2 = 1
        subjs_to_add |= {subject}
    else:
        out_put_1 = 'retire'
        out_put_2 = 0
    new_row = {'subject_ids': subj, 'classifications': cl_counter,
               'workflow_id': workflo_id,
               'workflow_version': workflo_version,
               'advance': out_put_1,
               'flag': out_put_2
               }
    writer_ag_out.writerow(new_row)
    return subjs_to_add


print('Aggregate, and test subjects for advancement, prepare list.')
with open(location + '_aggregated.csv', 'w', newline='') as ag_file:
    fieldnames = ['subject_ids',
                  'classifications',
                  'workflow_id',
                  'workflow_version',
                  'file-name',
                  'advance',
                  'flag']
    writer_ag_out = csv.DictWriter(ag_file, fieldnames=fieldnames)
    writer_ag_out.writeheader()
    # set up to read the flattened file
    with open(location + '_sorted.csv') as ag_f:
        r = csv.DictReader(ag_f)
        # initialize a starting point subject and empty bins for aggregation
        subject = ''
        workflow_id = ''
        workflow_version = ''
        subjects_to_add = set()  # Build subjects to add as a set
        m = 1
        bin_1 = 0

        # Loop over the flattened classification records
        for row in r:
            # read a row and pullout the flattened data fields we need to aggregate, or pass through.
            new_subject = row['subject_ids']
            new_workflow_id = row['workflow_id']
            new_workflow_version = row['workflow_version']
            task_answer = int(row['task_answer'])

            # test for a change in the selector - in this case the selector is the subject
            if new_subject != subject:
                if m != 1:  # if not the first line, we have aggregated all the classifications for
                    # this subject and we can analyse the aggregated fields and output the results.
                    subjects_to_add = process_aggregation(subject, m, workflow_id, workflow_version,
                                                          bin_1, subjects_to_add)
                # To start the next group, reset the selector, those things we need to pass through,
                # and the bins for the next aggregation.
                m = 1
                subject = new_subject
                workflow_id = new_workflow_id
                workflow_version = new_workflow_version
                bin_1 = task_answer
            else:
                # the selector has not yet changed so we continue the aggregation:
                bin_1 += task_answer
                m += 1
        # catch and process the last aggregated group
        subjects_to_add = process_aggregation(subject, m, workflow_id, workflow_version,
                                              bin_1, subjects_to_add)

if step_to_analyse == 'Q4':
    proj = Project.find(slug='tedcheese/whales-as-individuals')  # this will become WAI 'tedcheese/whales-as-individuals'
try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=proj.id, display_name=set_name).next()
    print("Add subjects to subject set: {}.".format(subject_set.display_name))
except:
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = proj
    subject_set.display_name = set_name
    subject_set.save()
    print("Created a new subject set with id: {}.".format(subject_set.id))

linked_subjects = set()  # use sets to automatically do inclusion test
with open(subject_location) as sub_file:
    r = csv.DictReader(sub_file)
    for sub_row in r:
        if sub_row['subject_set_id'] == subject_set.id:
            linked_subjects |= {sub_row['subject_id']}

add_subjects = (subjects_to_add - linked_subjects)

print("Adding {} subjects to the subject set".format(len(add_subjects)))
k = 0
# iterate through the subjects to advance verifying they load (for now) may use a list later.
for sub in add_subjects:
    try:
        subject_set.add(sub)
        k += 1
        print(sub, 'linked')
    except:
        print(sub, 'link failed')

print(k, 'subjects successfully linked')
