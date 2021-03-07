"""This script was written in Python 3.6.6 "out of the box" and should run without any added packages."""
import csv
import json
import sys
import operator
import os

csv.field_size_limit(sys.maxsize)

# File location section:
location = r'path\project-title-classifications.csv'
out_location = 'flatten_class_project.csv'
sorted_location = 'flatten_class_project_sorted.csv'


# Function definitions needed for any blocks.
def include(class_record):
    if int(class_record['workflow_id']) == 12345:
        pass
    else:
        return False
    if float(class_record['workflow_version']) >= 0.0:
        pass  # replace '001.01' with first version of the workflow to include.
    else:
        return False
    if 60000000 >= int(class_record['subject_ids']) >= 1000:
        pass  # replace upper and lower subject_ids to include only a specified range of subjects - this is
        # a very useful slice since subjects are selected together and can still be aggregated.
    else:
        return False
    if not class_record['gold_standard'] and not class_record['expert']:
        pass  # this excludes gold standard and expert classifications - remove the "not" to select only
        # the gold standard or expert classifications
    else:
        return False
    if '2100-00-10 00:00:00 UTC' >= class_record['created_at'] >= '2000-00-10 00:00:00 UTC':
        pass  # replace earliest and latest created_at date and times to select records commenced in a
        #  specific time period
    else:
        return False
    # otherwise :
    return True


def clear_unclear(string):
    clean = ['[unclear]', '[/unclear]']
    for text in clean:
        string = string.replace(text, '')
    return string


# Set up the output file structure with desired fields:
# prepare the output file and write the header
with open(out_location, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ['classification_id',
                  'subject_id',
                  'user_name',
                  'workflow_id',
                  'workflow_version',
                  'created_at',
                  'metadata_1',
                  'metadata_2',
                  'question_task_1',
                  'question_task_2',
                  'q2_vector',
                  'transcription_1',
                  'transcription_2',
                  'Date',
                  'Numerical',
                  'Description'
                  ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # this area for initializing counters, status lists and loading pick lists into memory:
    i = 0
    j = 0
    q2_template = ['answer_1', 'answer_2', 'answer_3']  # where answer_x is a unique snippet from that answer option
    # In this area place lines that initialize variables or load dictionaries needed by the additional code blocks
    #  open the zooniverse data file using dictreader,  and load the more complex json strings as python objects
    with open(location, encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            # useful for debugging - set the number of record to process at a low number ~1000
            # if i == 100:
            #     break
            i += 1
            if include(row) is True:
                j += 1
                annotations = json.loads(row['annotations'])
                subject_data = json.loads(row['subject_data'])

                # this is the area the various blocks of code will be inserted to preform additional general
                # tasks, to flatten the annotations field, or test the data for various conditions.

                # pull metadata from the subject data field

                metadata = subject_data[(row['subject_ids'])]
                try:
                    metadata_1 = metadata['metadata_1']
                except KeyError:
                    metadata_1 = ''
                try:
                    metadata_2 = metadata['metadata_1']
                except KeyError:
                    metadata_1 = ''

                # reset the field variables for each new row
                q1 = ''
                q2 = []
                q2_vector = [0, 0, 0]  # vector format for multiple responses
                t1 = ''
                t2 = ''
                d1 = ''
                d2 = ''
                d3 = ''
                date = ''

                # loop over the tasks
                for task in annotations:
                    #  Question 1? # single response
                    try:
                        if task['task'] == 'T0':
                            q1 = task['value']
                    except KeyError:
                        pass

                    #  Question 2? # multiple response where shortened response choices are listed, and also reported
                    # in a vector format for easy aggregation
                    try:
                        if task['task'] == 'T1':
                            if task['value'] is not None:
                                for counter in range(0, len(q2_template)):
                                    for item in task['value']:
                                        if item.find(q2_template[counter]) >= 0:
                                            q2.append(q2_template[counter])
                                            q2_vector[counter] = 1
                    except KeyError:
                        pass

                    # Free Transcription_1
                    try:
                        if task['task'] == 'T2':
                            if task['value'] is not None:
                                t1_raw = str(task['value'])
                                t1 = t1_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass

                    # Free Transcription_2  - clean for unclear tags
                    try:
                        if task['task'] == 'T3':
                            if task['value'] is not None:
                                t2_raw = str(task['value'])
                                t2 = clear_unclear(t2_raw.replace('\n', ' ').strip())
                    except KeyError:
                        pass

                    # Dropdown Month/day?
                    try:
                        if task['task'] == 'T4':
                            if task['value'] is not None:
                                if task['value'][0]['value'] is not None:
                                    d2 = str(task['value'][0]['value'])
                                if task['value'][1]['value'] is not None:
                                    d1 = str(task['value'][1]['value'])
                                    # It may be necessary to deal with certain cases where the d1 or d2 value
                                    # appears as an odd string like 'da0a39c5a481a8' rather than the correct number:
                                    #  if d1 == 'da0a39c5a481a8':
                                    #      d1 = '12'
                    except KeyError:
                        pass

                    # Dropdown Year?
                    try:
                        if task['task'] == 'T5':
                            if task['value'] is not None:
                                d3 = str(task['value'][0]['value'])
                                # same issue as in month/day dropdowns can occur here
                    except KeyError:
                        pass

                # massage date
                if len(d1) == 1:
                    day = '0' + d1
                else:
                    day = d1

                if len(d2) == 1:
                    mon = '0' + d2
                else:
                    mon = d2

                if len(d3) > 4:
                    year = 'xxxx'
                elif len(d3) == 0:
                    year = '0000'
                else:
                    year = d3
                date = mon + '/' + day + '/' + year

                # This set up the writer to match the field names above and the variable names of their values:
                writer.writerow({'classification_id': row['classification_id'],
                                 'subject_id': row['subject_ids'],
                                 'user_name': row['user_name'],
                                 'workflow_id': row['workflow_id'],
                                 'workflow_version': row['workflow_version'],
                                 'created_at': row['created_at'],
                                 'metadata_1': metadata_1,
                                 'metadata_2': metadata_2,
                                 'question_task_1': q1,
                                 'question_task_2': q2,
                                 'q2_vector': json.dumps(q2_vector, ensure_ascii=False),
                                 'transcription_1': t1,
                                 'transcription_2': t2,
                                 'month': d2,
                                 'day': d1,
                                 'year': d3,
                                 'Date': date
                                 })

                print(j)  # just so we know progress is being made
        # This area prints some basic process info and status
        print(i, 'lines read and inspected', j, 'records processed and copied')


# This section defines a sort function. Note the last parameter is the field to sort by where fields
# are numbered starting from '0'
def sort_file(input_file, output_file_sorted, field, reverse, clean):
    #  This allows a sort of the output file on a specific field.
    with open(input_file, 'r', encoding='utf-8') as in_file:
        in_put = csv.reader(in_file, dialect='excel')
        headers = in_put.__next__()
        sort = sorted(in_put, key=operator.itemgetter(field), reverse=reverse)
        with open(output_file_sorted, 'w', newline='', encoding='utf-8') as out_file:
            write_sorted = csv.writer(out_file, delimiter=',')
            write_sorted.writerow(headers)
            sort_counter = 0
            for line in sort:
                write_sorted.writerow(line)
                sort_counter += 1
    if clean:  # clean up temporary file
        try:
            os.remove(input_file)
        except OSError:
            print('temp file not found and deleted')
    return sort_counter


print(sort_file(out_location, sorted_location, 1, False, False), 'lines sorted and written')
