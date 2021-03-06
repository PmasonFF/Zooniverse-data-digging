"""This script was written in Python 3.6.6 "out of the box" and should run without any added packages."""
import csv
import json
import operator
import os

# csv.field_size_limit(sys.maxsize)
csv.field_size_limit(10000000)

# File location section:
location = r'C:\Users\Mark\OneDrive - University of Dundee\Test\reading-natures-library-classifications.csv'
out_location = r'C:\Users\Mark\OneDrive - University of Dundee\Test\flatten_class_rnl.csv'
sorted_location = 'flatten_class_rnl_sorted.csv'


# Function definitions needed for any blocks.
def include(class_record):
    if int(class_record['workflow_id']) == 2861:
        pass
    else:
        return False
    if float(class_record['workflow_version']) >= 227.608:
        pass  # replace '001.01' with first version of the workflow to include.
    else:
        return False
    if 40000000 >= int(class_record['subject_ids']) >= 5000:
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
    clean = ['[#unknown]', '[UNKNOWN]', '[unkow]', '[uknown]', '[unkow]', '[unnown]',
             '[#no_collector]', '[no data]', '[not known]', '[not recorded]']
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
                  'Scientific_name',
                  'Country',
                  'Location',
                  'Collector',                  
                  'Era',
                  'Age',
                  'image',
                  ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # this area for initializing counters, status lists and loading pick lists into memory:
    i = 0
    j = 0    
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
                    image_name = metadata['Filename']
                except KeyError:
                    image_name = ''                

                # reset the field variables for each new row
                t1 = ''
                t2 = ''
                t3 = ''               
              
                d1 = ''
                q1 = ''
                q2 = ''               
            
                # loop over the tasks
                for task in annotations:

                    # loop over the combo task
                    try:
                        if task['task'] == 'TX':
                            for combo_task in task['value']:                            
                                # Free Transcription Scientific name?
                                try:
                                    if combo_task['task'] == 'TY':
                                        if combo_task['value'] is not None:
                                            t1_raw = str(combo_task['value']).replace('\n', ' ').strip()
                                            l1 = sorted(
                                                [t1_raw.partition(';')[0], t1_raw.partition(';')[1],
                                                 t1_raw.partition(';')[2]])
                                            t1 = l1[0] + l1[1] + ' ' + l1[2]
                                except KeyError:
                                    pass 

                                # Free Transcription Location?
                                try:
                                    if combo_task['task'] == 'TZ':
                                        if combo_task['value'] is not None:
                                            t2_raw = str(combo_task['value'])
                                            t2 = t2_raw.replace('\n', ' ').strip()
                                except KeyError:
                                    pass

                                # Free Transcription Collector?
                                try:
                                    if combo_task['task'] == 'TW':
                                        if combo_task['value'] is not None:
                                            t3_meta = str(combo_task['value']).replace('\n', '').strip()
                                            t3_raw = clear_unclear(t3_meta)
                                            l3 = sorted(
                                                [t3_raw.partition(';')[0], t3_raw.partition(';')[1],
                                                 t3_raw.partition(';')[2]])
                                            t3 = l3[0] + l3[1] + ' ' + l3[2]
                                except KeyError:
                                    pass

                                # Dropdown Country?
                                try:
                                    if combo_task['task'] == 'TV':
                                        if combo_task['value'] is not None:
                                            d1 = str(combo_task['value'][0]['value']) 
                                except KeyError:
                                    pass

                    except KeyError:
                        pass

                    # Question Era?
                    try:
                        if task['task'] == 'TU':
                            if task['value'] is not None:
                                q1 = str(task['value'])                           
                    except KeyError:
                        pass
    
                    # Question Age?
                    try:
                        if task['task'] == 'TT':
                            if task['value'] is not None:
                                q2 = str(task['value'])                              
                    except KeyError:
                        pass          

                # This set up the writer to match the field names above and the variable names of their values:
                writer.writerow({'classification_id': row['classification_id'],                               
                                 'subject_id': row['subject_ids'],
                                 'user_name': row['user_name'],
                                 'workflow_id': row['workflow_id'],
                                 'workflow_version': row['workflow_version'],
                                 'Scientific_name': t1,
                                 'Country': d1,
                                 'Location': t2,
                                 'Collector': t3,                                 
                                 'Era': q1,
                                 'Age': q2,
                                 'image': image_name,
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
