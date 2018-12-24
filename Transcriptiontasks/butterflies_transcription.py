"""This script was written in Python 3.6.6 "out of the box" and should run without any added packages."""
import csv
import json
import sys
import operator
import os

csv.field_size_limit(sys.maxsize)

# File location section:
location = r'C:\py\Butterflies\danish-butterflies-and-moths-2020-challenge-classifications.csv'
out_location = r'C:\py\Butterflies\flatten_class_butterflies.csv'
sorted_location = 'flatten_class_butterflies_sorted.csv'


# Function definitions needed for any blocks.
def include(class_record):
    if int(class_record['workflow_id']) == 6750:
        pass
    else:
        return False
    if float(class_record['workflow_version']) >= 179.0:
        pass  # replace '001.01' with first version of the workflow to include.
    else:
        return False
    if 40000000 >= int(class_record['subject_ids']) >= 1000:
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
    clean = ['[unclear]', '[/unclear]', '[uklar]', '[/uklar]',
             '[непонятный]', '[/непонятный]', '[pas clair]', '[/pas clair]']
    for text in clean:
        string = string.replace(text, '')
    return string


# Set up the output file structure with desired fields:
# prepare the output file and write the header
with open(out_location, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ['classification_id',
                  'NHMD',
                  'Scientific_Name',
                  'subject_id',
                  'user_name',
                  'workflow_id',
                  'workflow_version',
                  'created_at',
                  'Fully_visible',
                  'Accession',
                  'Belonged',
                  'Type_label',
                  'Location',
                  'month',
                  'day',
                  'year',                  
                  'Collector',
                  'Taxon_label',
                  'Taxon',
                  'Determiner',
                  'Sex',
                  'Genital_prep',
                  'Prep_number',
                  'Prepared_by',
                  'ZMUC_number'
                  ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # this area for initializing counters, status lists and loading pick lists into memory:
    i = 0
    j = 0
    # In this area place lines that initialize variables or load dictionaries needed by the additional code blocks
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    #  open the zooniverse data file using dictreader,  and load the more complex json strings as python objects
    with open(location, encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            # for k in range (1, 100000):
            #     f= k**2
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
                    catalog_number = metadata['catalog_number']
                except KeyError:
                    catalog_number = ''
                try:
                    scientific_name = metadata['scientific_name']
                except KeyError:
                    scientific_name = ''

                # reset the field variables for each new row
                q1 = ''
                q2 = ''
                q3 = ''
                q4 = ''
                q5 = ''
                q6 = ''

                t1 = ''
                t2 = ''
                t3 = ''
                t4 = ''
                t5 = ''
                t6 = ''
                t7 = ''
                t8 = ''

                d1 = ''
                d2 = ''
                d3 = ''
                date = ''
            
                # loop over the tasks
                for task in annotations:
                    #  Question Fully visible?
                    try:
                        if task['task'] == 'T3':
                            q1 = task['value']
                    except KeyError:
                        continue

                    #  Question Accession?
                    try:
                        if task['task'] == 'T10':
                            q2 = task['value']
                    except KeyError:
                        pass

                    #  Question Type_label?
                    try:
                        if task['task'] == 'T19':
                            q3 = task['value']
                    except KeyError:
                        pass
                    #   Question Taxon_label?
                    try:
                        if task['task'] == 'T9':
                            q4 = task['value']
                    except KeyError:
                        pass

                    #  Question Sex?
                    try:
                        if task['task'] == 'T13':
                            q5 = task['value']
                    except KeyError:
                        pass

                    # Question Genital_prep?
                    try:
                        if task['task'] == 'T16':
                            q6 = task['value']
                    except KeyError:
                        pass

                    # Free Transcription Belonged?
                    try:
                        if task['task'] == 'T11':
                            if task['value'] is not None:
                                t1_raw = str(task['value'])
                                t1 = t1_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass

                    # Free Transcription Location?
                    try:
                        if task['task'] == 'T5':
                            if task['value'] is not None:
                                t2_raw = str(task['value'])
                                t2 = t2_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass

                    # Free Transcription Collector?
                    try:
                        if task['task'] == 'T8':
                            if task['value'] is not None:
                                t3_meta = str(task['value']).replace('\n', '').strip()
                                t3_raw = clear_unclear(t3_meta)
                                l3 = sorted(
                                    [t3_raw.partition(';')[0], t3_raw.partition(';')[1], t3_raw.partition(';')[2]])
                                t3 = l3[0] + l3[1] + ' ' + l3[2]
                    except KeyError:
                        pass

                    # Free Transcription Taxon?
                    try:
                        if task['task'] == 'T12':
                            if task['value'] is not None:
                                t4_raw = str(task['value']).replace('\n', ' ').strip()
                                l4 = sorted(
                                    [t4_raw.partition(';')[0], t4_raw.partition(';')[1], t4_raw.partition(';')[2]])
                                t4 = l4[0] + l4[1] + ' ' + l4[2]
                    except KeyError:
                        pass

                    # Free Transcription Determiner?
                    try:
                        if task['task'] == 'T14':
                            if task['value'] is not None:
                                t5_raw = str(task['value'])
                                t5 = t5_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass

                    # Free Transcription Prep_number?
                    try:
                        if task['task'] == 'T15':
                            if task['value'] is not None:
                                t6_raw = str(task['value'])
                                t6_digits = ''
                                for char in t6_raw:
                                    if char in digits:
                                        t6_digits += char
                                if len(t6_digits) > 0:
                                    t6 = int(t6_digits)
                                    if t6 > 40000:
                                        t6 = ''
                    except KeyError:
                        pass

                    # Free Transcription Prepared_by?
                    try:
                        if task['task'] == 'T18':
                            if task['value'] is not None:
                                t7_raw = str(task['value'])
                                t7 = t7_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass

                    # Free Transcription ZMUC_number?
                    try:
                        if task['task'] == 'T17':
                            if task['value'] is not None:
                                raw = str(task['value'])
                                t8_digits = ''
                                for char in raw:
                                    if char in digits:
                                        t8_digits += char
                                if len(t8_digits) > 0:
                                    t8 = int(t8_digits)
                                    if t8 > 200000:
                                        t8 = ''

                    except KeyError:
                        pass

                    # Dropdown Month/day?
                    try:
                        if task['task'] == 'T6':
                            if task['value'] is not None:
                                if task['value'][0]['value'] is not None:
                                    d2 = str(task['value'][0]['value'])
                                    if d2 == 'da0a39c5a481a8':
                                        d2 = ''
                                if task['value'][1]['value'] is not None:
                                    d1 = str(task['value'][1]['value'])
                                    if d1 == 'eaba355e214cf8':
                                        d1 = ''

                    except KeyError:
                        pass

                    # Dropdown Year?
                    try:
                        if task['task'] == 'T7':
                            if task['value'] is not None:
                                d3 = str(task['value'][0]['value'])
                                if d3 == 'a005a674b228e':
                                        d3 = ''
                    except KeyError:
                        pass
              

                # This set up the writer to match the field names above and the variable names of their values:
                writer.writerow({'classification_id': row['classification_id'],
                                 'NHMD': catalog_number,
                                 'Scientific_Name': scientific_name,
                                 'subject_id': row['subject_ids'],
                                 'user_name': row['user_name'],
                                 'workflow_id': row['workflow_id'],
                                 'workflow_version': row['workflow_version'],
                                 'created_at': row['created_at'],
                                 'Fully_visible': q1,
                                 'Accession': q2,
                                 'Belonged': t1,
                                 'Type_label': q3,
                                 'Location': t2,
                                 'month': d2,
                                 'day': d1,
                                 'year': d3,                                 
                                 'Collector': t3,
                                 'Taxon_label': q4,
                                 'Taxon': t4,
                                 'Determiner': t5,
                                 'Sex': q5,
                                 'Genital_prep': q6,
                                 'Prep_number': t6,
                                 'Prepared_by': t7,
                                 'ZMUC_number': t8
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
