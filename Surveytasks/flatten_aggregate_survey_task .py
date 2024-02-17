""" This script takes a local copy of the Zooniverse Classification download file from a survey task
as input and  flattens the annotations field into a more user friendly format. Specifically it takes
the questions.csv file used to build the project and a few details known by the project builder to
flatten the data export file, extract the metadata, and aggregate the responses in a vector format
showing vote fraction for every possible response, ready for filtering

This script was written in Python 3.7 "out of the box" and can be run without any added packages
up to the end of the filtered stage.

The last section which links indeterminate subjects to a subject set for further classification
requires the panoptes_client packages.  To log on to zooniverse username and password must be supplied.
The script run_config.py, if installed in the same directory as this script, may be used to securely store
your password, and also provide the Path and filename of the data export to use in line 35.  If this is
not used, the Path and filename of the data export can be hardcoded in line 35.

"""

import csv
import json
import sys
import operator
import os
from run_config import Runconfig  # this is optional - the required info can be hardcoded in lines 35, 654 and 655
# if the run_config optionis to be used the script run_config.py must be in the working directory.
from panoptes_client import SubjectSet, Project, Panoptes

csv.field_size_limit(sys.maxsize)

""" This section records details of the user's directory structure where the data export file is located, 
the name of the questions and confusedwith file which must be with the data export, the survey task number,
and the names of the metadata fields to be included in the output"""

# The directory where the classification data, a copy of the questions.csv, and output files will reside
# This Path and file name can be hardcoded here or pulled from a config file built with a copy of the script
# run_config.py that is also used to securely store credentials for logging on to zooniverse.
directory = Runconfig().working_directory

#  The name of the questions file used to set up the survey task for the data to be analyzed
question_file = 'questions.csv'
#  The name of the confusedwith file used to set up the survey task for the data to be analyzed
confused_with_file = 'confusedwith.csv'
# The name of the classification data export (it is best if these are the workflow classification exports):
location = 'survey-classifications.csv'

# workflow and earliest version to include in the analysis - Note other filtering conditions can be set
# below in the function "def include()"
workflow_id = 4994
workflow_version = 106.0

# The task number of the survey task ( normally T0 but can be project specific)
survey_task = 'T0'

# list of metadata fields to include in the output files - these must match the subject metadata field names
metadata_fields = ['Filename']
# List of Headers for flattened output file for the "questions" columns - one per question in the questions file
# This list is optional - if it is left blank (ie []) the zooniverse questions labels will be used, for example
# "HOWMANYINDIVIDUALSDOYOUSEE". These are unnecessarily long and messy, and noramlly can be shortened.
question_headers = ['how_many', 'behaviours', 'young', 'horns', 'care?']

# list of questions which are to be filtered to a single value and vote fraction, (or shown as indeterminate)
# by question number starting at 0.
show_vote_fraction = [0]

# Headers for the filtered output file for the "questions" columns  This dictionary is optional. If the columns
# for a question are not defined, the question labels (or if given above the question headers) and the response options
# will  be used to create the column headings for that question eg "young_present - Yes". "young_present - No".
# If the columns for a question are included here there must be a header for every possible response option.
# questions are numbered from 0 in the order they arein the questions file.
custom_headers = {1: ['Resting', 'Standing', 'Moving', 'Eating', 'Interacting'],
                  2: ['young-Yes', 'young-No'],
                  3: ['horns-Yes', 'horns-No']
                  }

# define the limits described in the filter -  See lines 435-501 for what these values mean
min_class = 10
min_species_vf = 66
ignore_vf = 26
at_least_v_f = 51

# ___________________________________________________________________________________________________________________

try:
    out_file_name = location[:location.find('class') - 1] + '_' + str(workflow_id)
except IndexError:
    out_file_name = 'survey_task_' + str(workflow_id)

# Output file names (generated from the data export file name - these can be modified if required)
out_location = directory + os.sep + out_file_name + '_flatten.csv'  # a sort deletes this file after use
sorted_location = directory + os.sep + out_file_name + '_sorted.csv'
aggregate_location = directory + os.sep + out_file_name + '_aggregate.csv'
columns_location = directory + os.sep + out_file_name + '_filtered.csv'
# add path info to question file confused_with file and data locations
question_file = directory + os.sep + question_file
confused_with_file = directory + os.sep + confused_with_file
location = directory + os.sep + location


# Function definitions needed for any blocks in this area.
def include(class_record):
    #  defines a function that returns True or False based on whether the argument record is to be
    #  included or not in the output file based on the conditional clauses.
    #  many other conditions could be set up to determine if a record is to be processed and the
    #  flattened data written to the output file.

    if int(class_record['workflow_id']) == workflow_id:
        pass  # this one selects the workflow to include.
    else:
        return False
    if float(class_record['workflow_version']) >= workflow_version:
        pass  # this one selects the first version of the workflow to include. Note the workflows
        #  must be compatible with the structure (task numbers) choices, and questions (they could
        #  differ in confusions, characteristics or other wording differences.)
    else:
        return False
    # if xxxxxxxxx >= int(class_record['subject_ids']) >= xxxxxxxxx \
    #         and int(class_record['subject_ids']) not in [xxxxxxxxx] \
    #         or int(class_record['subject_ids']) in [xxxxxxxxx]:
    #     pass  # replace upper and lower subject_ids to include only a specified range of subjects - this is
    #     # a very useful slice since subjects are selected together and can still be aggregated.
    # else:
    #     return False
    # if '2100-00-10 00:00:00 UTC' >= class_record['created_at'] >= '2020-04-13 00:00:00 UTC':
    #     pass  # replace earliest and latest created_at date and times to select records commenced in a
    #     #  specific time period
    # else:
    #     return False
    # otherwise :
    return True


def load_questions():
    #  This function loads the question.csv and creates a dictionary in memory with the possible responses
    with open(question_file) as qu_file:
        questdict = csv.DictReader(qu_file)
        questions_answers = {}
        translate_table = dict((ord(char), '') for char in r'!"#%\'()*,-./: <=>?@[\]^_`{|}~')
        for quest in questdict:
            questions_answers[quest['Question'].upper().translate(translate_table).replace(' ', '')] \
                = quest['Answers'].upper().translate(translate_table).split(';')
        return questions_answers


def load_confused_with():
    #  This function loads the confusedwith.csv and creates a list of confused pairs in memory
    with open(confused_with_file) as confus_file:
        confusdict = csv.DictReader(confus_file)
        confused_ = []
        translate_table = dict((ord(char), '') for char in r'!"#%\'()*+,-./: <=>?@[\]^_`{|}~')
        for confus in confusdict:
            confused_.append([confus['Name'].upper().translate(translate_table),
                              confus['Twin'].upper().translate(translate_table)])
        return confused_


def empty(ques, resp):
    # this is used to set up an empty response vector for each row
    blank = []
    for q1 in range(0, len(ques)):
        blank.append([0 for _ in resp[q1]])
    return blank


#  this loads the question.csv as a dictionary we can split to get the question labels
#  and possible responses we need to breakout the survey data.  It should produce the same
#  question and response labels as the project builder but strange characters in the questions
#  may need to be individually dealt with by adding them to the translation table in the function.
q_a = load_questions()
questions = list(q_a.keys())
responses = list(q_a.values())
confused = load_confused_with()
#  If the question headers were not fully defined, use the questions themselves
if len(question_headers) != len(questions):
    question_headers = questions

# Set up the output file structure with desired fields:
# The list of field names must include each field required in the output.
with open(out_location, 'w', newline='', encoding='utf-8') as ou_file:
    fieldnames = ['classification_id', 'subject_ids', 'created_at', 'user_name', 'subject_choices']
    fieldnames.extend(metadata_fields)
    fieldnames.append('choice')
    fieldnames.extend(question_headers)
    fieldnames.append('answer_vector')

    writer_out = csv.DictWriter(ou_file, fieldnames=fieldnames)
    writer_out.writeheader()

    # this area for initializing counters:
    rc2 = 0
    rc1 = 0
    wc1 = 0

    #  open the zooniverse data file using dictreader, and load the more complex json strings
    #  as python objects using json.loads()
    with open(location) as class_file:
        classifications = csv.DictReader(class_file)
        for row in classifications:
            rc2 += 1
            # useful for debugging - set the number of record to process at a low number ~1000
            # if rc2 == 150000:
            #     break
            if rc2 % 200 == 0:
                print('.', end='')
            if include(row) is True:
                rc1 += 1
                annotations = json.loads(row['annotations'])
                subject_data = json.loads(row['subject_data'])

                # pull subject metadata from the subject_data field of the classification export
                subjectdata = subject_data[(row['subject_ids'])]
                # initialize the metadata variables for this subject
                metadata_variables = ['' for _ in metadata_fields]
                # test for selected field names and acquire the values if they exist
                for index, metadata_field in enumerate(metadata_fields):
                    if metadata_field in subjectdata:
                        metadata_variables[index] = subjectdata[metadata_field]
                    else:
                        metadata_variables[index] = ''

                # reset field variables for the transcription task and the survey task for each new row
                choice = ''
                answer = ['' for q4 in questions]

                for task in annotations:
                    # The survey task block:
                    try:
                        #  main survey task recognized by project specific task number set above
                        if task['task'] == survey_task:
                            try:
                                for species in task['value']:
                                    choice = species['choice']
                                    answer_vector = empty(questions, responses)
                                    answer = ['' for q4 in questions]
                                    for q in range(0, len(questions)):
                                        try:
                                            answer[q] = species['answers'][questions[q]]
                                            # prepare answer_vectors that will make aggregation easier
                                            for r in range(0, len(responses[q])):
                                                if isinstance(answer[q], list):
                                                    if responses[q][r] in answer[q]:
                                                        answer_vector[q][r] = 1
                                                else:
                                                    if responses[q][r] == answer[q]:
                                                        answer_vector[q][r] = 1
                                        except KeyError:
                                            continue

                                    # This sets up the writer to match the field names above and the
                                    # variable names of their values. Note we write one line per
                                    # subject_choice
                                    wc1 += 1
                                    new_row = {'classification_id': row['classification_id'],
                                               'subject_ids': row['subject_ids'],
                                               'created_at': row['created_at'],
                                               'user_name': row['user_name'],
                                               'subject_choices': row['subject_ids'] + choice}
                                    for index, metadata_field in enumerate(metadata_fields):
                                        new_row[metadata_field] = metadata_variables[index]
                                    for index, question_field in enumerate(question_headers):
                                        new_row[question_field] = answer[index]
                                    new_row['choice'] = choice
                                    new_row['answer_vector'] = json.dumps(answer_vector)
                                    writer_out.writerow(new_row)
                            except KeyError:
                                continue
                    except KeyError:
                        continue

# This area prints some basic process info and status
print('\n')
print(rc2, 'lines read and inspected', rc1, 'records processed and', wc1, 'lines written')


#  ____________________________________________________________________________________________________________

# This section defines a sort function. Note the last parameter is the field to sort by where fields
# are numbered starting from '0'  This prepares the file to be aggregated by subject-species.

def sort_file(input_file, output_file_sorted, field, reverse, clean):
    #  This allows a sort of the output file on a specific field.
    with open(input_file, 'r') as in_file:
        in_put = csv.reader(in_file, dialect='excel')
        headers = in_put.__next__()
        sort = sorted(in_put, key=operator.itemgetter(field), reverse=reverse)
        with open(output_file_sorted, 'w', newline='') as sorted_out:
            write_sorted = csv.writer(sorted_out, delimiter=',')
            write_sorted.writerow(headers)
            sort_counter = 0
            for line in sort:
                write_sorted.writerow(line)
                sort_counter += 1
    if clean:  # clean up temporary file
        try:
            os.remove(input_file)
        except OSError:
            print('temp file not found and not deleted')
    return sort_counter


print(sort_file(out_location, sorted_location, 4, False, True), 'lines sorted and written')


#  ____________________________________________________________________________________________________________

# This next section aggregates the responses for each subject-species and out puts the result
# with one line per subject-species. Vote fractions are calculated for each question-response
# and are displayed in a answer_vector format suitable for further analysis.

def cal_fraction(ques1, resp1, aggr1, tot):
    for q2 in range(0, len(ques1)):
        for r2 in range(0, len(resp1[q2])):
            aggr1[q2][r2] = int(aggr1[q2][r2] / tot * 100 + .45)
    return aggr1


with open(aggregate_location, 'w', newline='') as ag_file:
    fieldnames = ['subject_ids']
    fieldnames.extend(metadata_fields)
    fieldnames.extend(['total_class', 'species_class', 'choice', 'aggregated_vector'])
    writer = csv.DictWriter(ag_file, fieldnames=fieldnames)
    writer.writeheader()
    #  build a look-up table of classification totals by subject - this is needed for the calculation of
    #  vote_fraction. We also aggregate the anything_else responses from each unique classification, also
    #  as a look-up table by subject.
    with open(sorted_location) as so_file:
        sorted_file = csv.DictReader(so_file)
        subject = ''
        class_totals = {}
        class_tot = 0
        for row1 in sorted_file:
            new_subject = row1['subject_ids']
            new_class = row1['classification_id']
            # new_user = row1['user_name']
            if new_subject != subject:
                if subject != '':
                    class_totals[subject] = class_tot
                # users = {new_user}
                unique_class = {new_class}
                subject = new_subject
                class_tot = 1
            else:
                # only count unique classifications EITHER by user or classification_id
                # only count by unique users
                # if users != users | {new_user}:
                #     users |= {new_user}
                # only count unique classifications
                if unique_class != unique_class | {new_class}:
                    unique_class |= {new_class}
                    subject = new_subject
                    class_tot += 1

        class_totals[subject] = class_tot
    # The old fashion aggregation routine with the vote count and file write
    # Here we aggregate over each subject-species, and output the results one line each subject-species
    # in vector format only since the filter will output the results in a more human readable format.
    with open(sorted_location) as so_file:
        sorted_file = csv.DictReader(so_file)
        subject = ''
        subject_choices = ''
        metadata_variables = ['' for _ in metadata_fields]
        row_counter = 0
        count_subj_choice = 0
        aggregate = []
        class_count = 0
        choice_now = ''
        for row2 in sorted_file:
            row_counter += 1
            new_subject = row2['subject_ids']
            # new_user = row2['user_name']
            new_subject_choices = row2['subject_choices']
            answer_vector = json.loads(row2['answer_vector'])

            if new_subject_choices != subject_choices:
                if row_counter != 1:  # don't want to output the empty initial values
                    count_subj_choice += 1
                    aggregate_vf = cal_fraction(questions, responses, aggregate, class_totals[subject])
                    new_row = {'subject_ids': subject,
                               'total_class': class_totals[subject],
                               'species_class': class_count,
                               'choice': choice_now,
                               'aggregated_vector': json.dumps(aggregate_vf)}
                    for index, metadata_field in enumerate(metadata_fields):
                        new_row[metadata_field] = metadata_variables[index]

                    writer.writerow(new_row)
                # users = {new_user}
                subject = new_subject
                subject_choices = new_subject_choices
                choice_now = row2['choice']
                metadata_variables = [row2[metadata_field] for metadata_field in metadata_fields]
                class_count = 1
                aggregate = answer_vector[:]
            else:
                # if users != users | {new_user}:
                #     users |= {new_user}
                for que in range(0, len(questions)):
                    for res in range(0, len(responses[que])):
                        aggregate[que][res] += answer_vector[que][res]
                class_count += 1
                subject = new_subject
                subject_choices = new_subject_choices

        # catch the last aggregate after the end of the file is reached
        count_subj_choice += 1
        aggregate_vf = cal_fraction(questions, responses, aggregate, class_totals[subject])
        new_row = {'subject_ids': subject,
                   'total_class': class_totals[subject],
                   'species_class': class_count,
                   'choice': choice_now,
                   'aggregated_vector': json.dumps(aggregate_vf)}

        for index, metadata_field in enumerate(metadata_fields):
            new_row[metadata_field] = metadata_variables[index]
        writer.writerow(new_row)
    print(row_counter, 'lines aggregated into', count_subj_choice, 'subject-choice categories')
# ___________________________________________________________________________________________________________

"""The next section applies a optional filter to accept a consensus by plurality or to determine if the
result is too ambiguous to accept.  Multiple species, if they survive the filter, are output
on separate lines.

The details of the filter are as follows:

1)  The minimum number of classifications required retain a subject as classified is min_class. Subjects with
    less than this number of classifications are marked "A0 - insufficient classifications in the species column.    

2)  Determine species to include:
    Calculate the total v_f for each species using all votes for that species in any classification for the
    subject, including those with multiple species identified.

    The minimum total v_f to count any species as present is the min_species_vf (value set below). Any species
    with at least this vote fraction is recorded on a separate line with the responses to the rest of the 
    questions as recorded  against that species. These are the species "known" to be present and are marked 
    "C0 - consensus". There can be multiple "known" species.

    Species with a total vote fraction less than some value ignore_vf are ignored, and their "how many" count
    may be spread over the remaining species as described below. 
    If no species has a vote fraction over this limit then mark the subject as 'A1 - no species agreement '. This  
    only occurs if volunteers voted for many different species and all votes are spread over many species.    

3)  Indeterminate species - some species has a total vote fraction less than the min_species_vf but more
    than the ignore_vf. A subject may have both known and indeterminate species, and it may have multiple 
    indeterminate species. Indeterminate species will show on a separate line as 'I0 - indeterminate species' or 
    'I1 - multiple indeterminate species' if there is more than one. Vote fractions will show for all responses
    entered for the species but 'how many' values are shown only if the vote fraction meets some limit 
    at_least_v_f where it is assumed they have some significance.      

4)  If there is a "How many" type question. (These will generally be counts and a vote fraction for that count)        
        Calculate the "How many" and vote fraction as follows:
            1. Use the vote fractions for all possible responses to the 'how many' question(s), from all 
            classifications including in some cases described below, those from an "ignored" species that did 
            not make it through the species filter above.            
            2. list the vote fraction of each possible response option ie the number of classifications that had
            that response divided by the number of classifications for the subject, in order by count. Place 
            "unknown" as the lowest option if it was an allowed choice.            
            3. Beginning at the highest count, take the vote fraction of classifications that had that count 
            and add the vote fraction of the next highest count, and continue until some total at_least_v_f 
            saw AT LEAST that number of animals. Report the count as the 'how many' and the summed vote
            fraction as the vote fraction. For a reasonable choice of at_least_v_f such as 51 this ensures any 
            consensus, if one exists, is selected as the 'how many', otherwise the value can be interpreted as 
            an "at least" count.
            
        If there is one or more "ignore" species which did not get enough votes to be counted as a known or an 
        indeterminate species, it is very likely that the animals are misidentified, but it is also likely 
        the 'how many' responses are still accurate, and these may be applied to one of the species that did 
        make the cut.  
        
        The "ignored" votes for a species will be applied to any known or indeterminate species that was a 
        'confused with' pair with the ignored species as listed in the confusedwith.csv file. If there is a
        match, the vote fraction for each possible response for the ignored species is added to the vote fraction
        for the corresponding response for the matching species. Note the vote fraction for the species choices
        themselves are NOT modified, only the question responses are added up.       
        In general, "known" species already have enough votes this makes little or no difference, but it is 
        the best we can do to include all the information provided by the volunteers.
        Species which have added votes are marked with the word "augmented". 

5)  For all other (ie not "how many" type) questions, report a simple v_f for each possible response.  This is 
        based on the votes for each response divided by the total number of classifications.  If the votes for 
        an ignored species are added to a known or indeterminate species the vote fractions can be higher than 
        the species vote_fraction.  

Note the output is a columnar format vs the answer_vector approach of the aggregated file, with columns for a 
value and a vote fraction for each How many type question, and a column for every question response option 
for the other question types"""

# Build the column headers for the questions
column_headers = []
for q_index, q_header in enumerate(question_headers):
    if q_index in show_vote_fraction:
        column_headers.extend([q_header, q_header + ' v.f.'])
    else:
        try:
            column_headers.extend(custom_headers[q_index])
        except KeyError:
            for response in responses[q_index]:
                column_headers.append(q_header + '-' + response)


def apply_tests(sub, choicevector, subjects_to_resolve_):
    # Apply test 1 - were there enough classifications done to give any answer?
    if class_totals[sub] < min_class:
        subjects_to_resolve_ |= {sub}
        generate_row(sub, 'A0 - insufficient classifications', '', '', ['' for _ in range(0, len(column_headers))])
        return subjects_to_resolve_

    # sort out the choices by choice v_f high to low
    sorted_choice = sorted(choicevector, key=operator.itemgetter(1), reverse=True)
    # count "known", "indeterminate" and "ignore" choices
    known = 0
    indeter = 0
    ignore = 0
    for choice_ in sorted_choice:
        if choice_[1] >= min_species_vf:
            known += 1
        elif choice_[1] >= ignore_vf:
            subjects_to_resolve_ |= {sub}
            indeter += 1
        else:
            ignore += 1

    # Apply test 2 - there are not enough votes to count any species
    if known == 0 and indeter == 0:
        subjects_to_resolve_ |= {sub}
        generate_row(sub, 'A1 - no species agreement', '', '', ['' for _ in range(0, len(column_headers))])
        return subjects_to_resolve_

    # Apply test 3 - add votes for ignore species to remaining species based on confusedwith links
    aug_choice = []
    if ignore > 0:
        for confused_name, confused_twin in confused:
            for choice_ in sorted_choice[: - ignore]:  # loop over known and indeterminate species
                for ignore_choice in sorted_choice[- ignore:]:
                    if choice_[0] == confused_name and ignore_choice[0] == confused_twin:
                        aug_choice.append(choice_[0])
                        for q3, _ in enumerate(questions):
                            for r3, _ in enumerate(responses[q3]):
                                choice_[2][q3][r3] += ignore_choice[2][q3][r3]

    # list all known and indeterminate including those augmented
    for choice_ in sorted_choice[: known + indeter]:
        if choice_[0] in aug_choice:
            aug = 'augmented'
        else:
            aug = ''
        if choice_[1] >= min_species_vf:
            status = 'C0 - concensus' + aug
        else:
            if indeter > 1:
                status = 'I1 - multiple_indeterminate' + aug
            else:
                status = 'I0 - indeterminate' + aug
        out_list = generate_out_list(choice_[2])
        generate_row(sub, status, choice_[0], choice_[1], out_list)
    return subjects_to_resolve_


def generate_row(subjt, status, choic, choic_v_f, outlist):
    new_line = {'subject_ids': subjt,
                'total_class': class_totals[subjt],
                'status': status,
                'choice': choic,
                'choice v_f': choic_v_f}
    if choic_v_f != '':
        new_line['species_class'] = int(choic_v_f / 100 * class_totals[subjt] + .5)
    for indx, metadata_fld in enumerate(metadata_fields):
        new_line[metadata_fld] = metadata_variables[indx]
    for r7 in range(0, len(column_headers)):
        new_line[column_headers[r7]] = outlist[r7]
    writer_col.writerow(new_line)
    return None


def generate_out_list(choice_responses):
    out_list_ = []
    for r4, _ in enumerate(responses):
        if r4 in show_vote_fraction:  # these get a value and v_f
            choice_response = reversed(choice_responses[r4])
            sum_v_f = 0
            show_value = ''
            for idx, v_f in enumerate(choice_response):
                sum_v_f += v_f
                if sum_v_f >= at_least_v_f:
                    show_value = responses[r4][len(responses[r4]) - idx - 1]
                    break
            if sum_v_f == 0:
                sum_v_f = ''
            out_list_.extend([show_value, sum_v_f])
        else:
            for custom_value in choice_responses[r4]:
                if custom_value == 0:
                    custom_value = ''
                out_list_.append(custom_value)
    return out_list_


# this section aggregates by subject, gathering all species and their response vectors together so that the filtering
# tests can be applied to each subject. Subject with unresolved issues are collected into a set
subjects_to_resolve = set()
with open(columns_location, 'w', newline='') as col_file:
    fieldnames = ['subject_ids']
    fieldnames.extend(metadata_fields)
    fieldnames.extend(['total_class', 'species_class', 'status', 'choice', 'choice v_f'])
    fieldnames.extend(column_headers)

    writer_col = csv.DictWriter(col_file, fieldnames=fieldnames)
    writer_col.writeheader()

    with open(aggregate_location) as agg_file:
        aggregated_file = csv.DictReader(agg_file)
        subject = ''
        choice_vector = []
        metadata_variables = ['' for _ in metadata_fields]
        class_count = 0
        rc3 = 0
        rc4 = 0
        # collect all the subject data together - again an old fashioned aggregation routine
        # with the filter applied to the pooled subject data.
        for row3 in aggregated_file:
            rc3 += 1
            vector = json.loads(row3['aggregated_vector'])
            species_class = int(row3['species_class'])
            total_class = int(row3['total_class'])

            new_subject = row3['subject_ids']
            if new_subject != subject:
                if rc3 != 1:  # don't want to look at the empty initial values
                    subjects_to_resolve = apply_tests(subject, choice_vector, subjects_to_resolve)
                subject = new_subject
                rc4 += 1
                metadata_variables = [row3[metadata_field] for metadata_field in metadata_fields]
                choice_vector = [(row3['choice'], int(species_class / total_class * 100 + .5), vector)]
            else:
                choice_vector.append((row3['choice'], int(species_class / total_class * 100 + .5), vector))
                subject = new_subject

        # catch the last aggregate after the end of the file is reached
        subjects_to_resolve = apply_tests(subject, choice_vector, subjects_to_resolve)
print(rc3, 'subject-choices filtered for', rc4, 'subjects' + '\n')
# __________________________________________________________________________________________________________

# This section take a list subjects with unresolved issues from the filter above and sets up a
# subject set for a verification workflow for experts to use to resolve the discrepancies.

link = input('To proceed to link unresolved subjects to a subject set, enter "y"' + '\n')
if link.lower() != 'y':
    quit()
set_name = input('Entry a name for the subject set to use or create for unresolved subjects:' + '\n')

Panoptes.connect(username=Runconfig().username, password=Runconfig().password)
project = Project.find(slug=Runconfig().project_slug)

try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
except StopIteration:
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()
print(len(subjects_to_resolve), ' will be added to subject set: {}'.format(set_name))

k = 0
#  iterate through the subjects to advance verifying they load (for now) may use a list later.
for subjet in subjects_to_resolve:
    try:
        # subject_set.add(subjet)
        k += 1
        print(subjet, 'linked')
    except ValueError:  # panoptes_client.panoptes.PanoptesAPIException:
        print(subjet, 'link failed')
print(k, 'subjects successfully linked')
#  ________________________________________________________________________________________________________________
