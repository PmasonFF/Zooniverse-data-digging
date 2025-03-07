# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# built in packages:
import argparse
import textwrap
import csv
import json
import ast
import os
from os.path import join
import operator
import time
# third party packages - must be installed
from fuzzywuzzy import fuzz
import numpy as np
from natsort import natsorted
# modules - must be in directory with script
import line_scan
import wordcan

"""
Version 0.1.1
0.1.1 - raw docstring to remove syntax warning re '/p' line 613
0.1.0 - version with peel end groups, lcs, and remove outliers
        Currently set for maximum display of all differences,
        with no difference shown meaning full agreement between all responses. 
"""


# define a function that returns True or False based on whether the record is to be included
def include(class_record, group_id_, sub_limits_, group_ids_):
    if class_record['workflow_id'] == workflow:
        pass  # this one selects the workflow to include in the analysis.
    else:
        return False
    if sub_limits_:
        if sub_limits_[0] >= int(class_record['subject_ids']) >= sub_limits_[1]:
            return True  # this one can be used to select a range of subjects
        else:
            return False
    if group_ids_:
        if group_id_ in group_ids_:
            return True  # this one selects based on group_id
        else:
            return False
            # otherwise :
    return True


def clean_and_decorate(text):
    return text.replace('\n', ''). \
        replace('[deletion]', '˄').replace('[/deletion]', '˄'). \
        replace('[insertion]', '˅').replace('[/insertion]', '˅'). \
        replace('[unclear]', '‽').replace('[/unclear]', '‽'). \
        replace('[underline]', 'µ').replace('[/underline]', 'µ'). \
        replace('[Underline]', 'µ').replace('[/Underline]', 'µ').strip(' ')


#  The next section flattens the data export
def flatten_class(zoo_file, out_loc, sub_limits_, group_ids_):
    with open(out_loc, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['subject_id',
                      'workflow_id'
                      ]
        fieldnames.extend(metadata_fields)
        fieldnames.extend(['image_width',
                           'transcription_list'])

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # this area for initializing counters:
        i = 0
        j = 0
        with open(zoo_file, 'r', encoding='utf-8') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                i += 1
                # # useful for debugging - set the number of record to process at a low number ~1000
                # if outlier == 1000:
                #     break
                subject_data = json.loads(row['subject_data'])[row['subject_ids']]
                group_id = subject_data['group_id']

                if include(row, group_id, sub_limits_, group_ids_) is True:
                    subject_dimensions = json.loads(row["metadata"])['subject_dimensions'][0]
                    annotations = json.loads(row['annotations'])
                    next_row = {'subject_id': row['subject_ids'],
                                'workflow_id': row['workflow_id']
                                }
                    for metadata_field in metadata_fields:
                        try:
                            next_row[metadata_field] = subject_data[metadata_field]
                        except KeyError:
                            try:
                                next_row[metadata_field] = subject_data[metadata_field.lower()]
                            except KeyError:
                                print(subject_data, 'did not match metadata fields')
                                next_row[metadata_field] = ''
                    next_row['image_width'] = subject_dimensions['naturalWidth']

                    transcription_list = []
                    text_list = []
                    point_list = []
                    for task in annotations:
                        # pull out transcription
                        if task['task'] == line_trans_task:
                            for line in task['value']:
                                x = min(int(line['x1'] + .5),
                                        int(line['x2'] + .5))
                                y = int((line['y1'] +
                                         line['y2']) / 2 + .5)
                                point_list.append([x, y])

                        if task['task'] == line_task_details:
                            text_list.append([task['value']])

                    if len(text_list):
                        if len(text_list) == len(point_list):
                            for index, text in enumerate(text_list):
                                transcription_list.append(
                                    (point_list[index][0], point_list[index][1], clean_and_decorate(text[0])))
                            j += 1
                            next_row['transcription_list'] = json.dumps(transcription_list)
                            writer.writerow(next_row)
                        else:
                            print(row['subject_ids'], 'Check export structure, failed flattening step')
                            quit()

                if i % 50000 == 0:
                    print(i, j)
            print(i, j)
        return str(i) + ' Lines read and ' + str(j) + ' records processed'


# _____________________________________________________________________________________________
# This section defines a sort function. Note the last parameter is the field to sort by where fields
# are numbered starting from '0'
def sort_file(input_file, output_file_sorted, field, reverse, clean):
    #  This allows a sort of the output file on a specific field.
    with open(input_file, 'r', encoding='utf-8') as in_file:
        in_put = csv.reader(in_file)
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


def positional_sort_bmt(line_height_, grp_trans):
    if len(grp_trans) == 1:
        return grp_trans
    sorted_x_y = sorted(grp_trans, key=operator.itemgetter(1))
    final_sorted_grp_trans = []
    x_left = 0

    # get header - consecutive lines x aligned to left half of top of page
    header = []
    for line in sorted_x_y:
        if line[0] > .5 * width_to_line_ratio * line_height_:
            header.append(line)
        else:
            break
    if header:
        for line in header:
            sorted_x_y.remove(line)
        final_sorted_grp_trans.extend(header)

    # get top lines of text that are within .7 lh of upper-most line:
    top_lines = []
    if sorted_x_y:
        y_min = sorted_x_y[0][1]
        for line in sorted_x_y:
            if line[1] - y_min <= .7 * line_height_:
                top_lines.append(line)
            else:
                break

    # get object column lines - lines that are x aligned +- 1 lh of left-most top line
    # and y aligned within 1.3 lh of previous object line - generally the object number and revisions below it,
    # but it can include part or all of the middle block if there is no object number indent
    if top_lines:
        object_lines = []
        sorted_top_x = sorted(top_lines, key=operator.itemgetter(0))
        current_y_min = top_lines[0][1]
        x_left = sorted_top_x[0][0]
        for line in sorted_x_y:

            if abs(line[0] - x_left) <= line_height_ and line[1] - current_y_min < 1.3 * line_height_:
                object_lines.append(line)
                current_y_min = line[1]
        if object_lines:
            for line in object_lines:
                sorted_x_y.remove(line)
            final_sorted_grp_trans.extend(object_lines)

    # get far left notes - these are x aligned at least 3 lh left of the left-most line so far
    far_left = []
    if sorted_x_y:
        for line in sorted_x_y:
            if x_left - line[0] > 3 * line_height_:
                far_left.append(line)
        if far_left:
            for line in far_left:
                sorted_x_y.remove(line)

    # everything else is in the main block
    main_block = []
    if sorted_x_y:
        current_y_min = sorted_x_y[0][1]
        while True:
            same_line = [sorted_x_y[0]]
            for line in sorted_x_y[1:]:
                if line[1] - current_y_min <= .5 * line_height_:
                    same_line.append(line)
            main_block.extend(sorted(same_line, key=operator.itemgetter(0)))
            if same_line:
                for line in same_line:
                    sorted_x_y.remove(line)
            if sorted_x_y:
                current_y_min = sorted_x_y[0][1]
            else:
                break

    final_sorted_grp_trans.extend(sorted(main_block, key=operator.itemgetter(1)))
    final_sorted_grp_trans.extend(far_left)
    return final_sorted_grp_trans


def positional_sort_single_page(line_height_, grp_trans):
    if len(grp_trans) == 1:
        return grp_trans
    sorted_grp_trans = []
    sorted_y = sorted(grp_trans, key=operator.itemgetter(1))
    similar_y = [sorted_y[0]]
    for i in range(1, len(sorted_y)):
        if sorted_y[i][1] - sorted_y[i - 1][1] < .5 * line_height_:
            similar_y.append(sorted_y[i])
        else:
            sorted_similar_y = sorted(similar_y, key=operator.itemgetter(0))
            sorted_grp_trans.extend(sorted_similar_y)
            similar_y = [sorted_y[i]]
    sorted_grp_trans.extend(sorted(similar_y, key=operator.itemgetter(0)))
    return sorted_grp_trans


def positional_sort_double_page(image_width, line_height_, grp_trans):
    if len(grp_trans) == 1:
        return grp_trans
    paged_grp_ = [[], []]

    for grp_ in grp_trans:
        if grp_[0] > .45 * image_width:
            paged_grp_[1].append(grp_)
        else:
            paged_grp_[0].append(grp_)
    sorted_grp_trans = []
    for p in (0, 1):
        if paged_grp_[p]:
            sorted_y = sorted(paged_grp_[p], key=operator.itemgetter(1))
            similar_y = [sorted_y[0]]
            for i in range(1, len(sorted_y)):
                if sorted_y[i][1] - sorted_y[i - 1][1] < .4 * line_height_:
                    similar_y.append(sorted_y[i])
                else:
                    sorted_similar_y = sorted(similar_y, key=operator.itemgetter(0))
                    sorted_grp_trans.extend(sorted_similar_y)
                    similar_y = [sorted_y[i]]
            sorted_grp_trans.extend(sorted(similar_y, key=operator.itemgetter(0)))
            sorted_grp_trans.append((0, 0, [[0, 0, '\n']]))
    return sorted_grp_trans


def check_outlier(grp_):
    consensus_index = -1
    to_remove_ = []
    similarity_ = np.zeros(shape=(len(grp_), len(grp_)))
    max_ones_id = 0
    max_ones = 0
    for i in range(0, len(grp_)):
        for j in range(i, len(grp_)):
            if i == j:
                similarity_[i, i] = 1.0
            else:
                similarity_[i, j] = fuzz.ratio(grp_[i].replace(' ', ''), grp_[j].replace(' ', '')) / 100
                similarity_[j, i] = similarity_[i, j]

    for i in range(0, len(grp_)):
        if (similarity_[i] == 1.0).sum() > max_ones:
            max_ones = (similarity_[i] == 1.0).sum()
            max_ones_id = i

        acceptable_match = 0
        for j in range(0, len(grp_)):
            if similarity_[i, j] > .60:  # ie an acceptable match to some other text
                acceptable_match += 1
        if acceptable_match < 2:
            to_remove_.append(grp_[i])

    cleaned_grp_ = [grp_[k] for k in range(0, len(grp_)) if grp_[k] not in to_remove_]

    if max_ones / len(grp_) >= 1.0:  # changes level of differences shown, does not change reconciled text
        consensus_index = max_ones_id
    return consensus_index, cleaned_grp_, str(to_remove_)[1: -1]


def common_start(sa, sb):
    def _iter():
        for a, b in zip(sa, sb):
            if a == b:
                yield a
            else:
                return

    start = ''.join(_iter())
    return len(start), start


def common_finish(sa, sb):
    def _iter():
        for a, b in zip(sa[::-1], sb[::-1]):
            if a == b:
                yield a
            else:
                return

    finish = ''.join(_iter())[::-1]
    return len(finish), finish


def peel_common_end_groups(grp_):
    # peel off common start
    s, start = common_start(grp_[0], grp_[1])
    if len(grp_) == 2:
        grp_ = [grp_[0][s:], grp_[1][s:]]
    for index in range(2, len(grp_)):
        s, start = common_start(grp_[index], start)
    if s > 0:
        grp_ = [gr[s:] for gr in grp_]
    else:
        start = ''
    # peel off common finish
    f, finish = common_finish(grp_[0], grp_[1])
    if len(grp_) == 2:
        grp_ = [grp_[0][:-f], grp_[1][:-f]]
    for index in range(2, len(grp_)):
        f, finish = common_finish(grp_[index], finish)
    if f > 0:
        grp_ = [gr[: -f] for gr in grp_]
    else:
        finish = ''
    return [start, ['ø' if t == '' else t for t in grp_], finish]


def longest_common_substr(s1, s2):
    m, n = len(s1), len(s2)
    # Create a 1D array to store the previous row's results
    prev = [0] * (n + 1)
    start_ = 0
    end_ = 0
    res_ = 0
    for i in range(1, m + 1):
        # Create a temporary array to store the current row
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1] + 1
                if curr[j] > res_:
                    res_ = curr[j]
                    end_ = i
            else:
                curr[j] = 0
        # Move the current row's data to the previous row
        prev = curr
        start_ = end_ - res_
    return start_, end_, s1[end_ - res_:end_]


def peel_longest_common_substring(snip):
    start, end, lcs = longest_common_substr(snip[0], snip[1])
    if end - start > 2:
        if len(snip) == 2:
            snip_before = [snip[0][:start], snip[1][:start]]
            snip_after = [snip[0][end:], snip[0][end:]]
            return [snip_before, lcs, snip_after]
        else:
            for index in range(2, len(snip)):
                start, end, lcs = longest_common_substr(snip[index], lcs)
            if end - start > 2:
                snip_before = []
                snip_after = []
                for gr in snip:
                    if (gr.split(lcs))[0]:
                        snip_before.append((gr.split(lcs))[0])
                    else:
                        snip_before.append('ø')
                    if (gr.split(lcs))[1]:
                        snip_after.append((gr.split(lcs))[1])
                    else:
                        snip_after.append('ø')
                return [snip_before, lcs, snip_after]
            else:
                return snip
    return snip


def reconcile_and_assemble(sorted_grp_trans):
    full_reconciled_text = ''
    full_differences_text = ''
    full_outliers = ''
    for line_group in sorted_grp_trans:
        grp = [text for _, _, text in line_group[2]]
        outliers_ = ''
        if len(grp) == 1:
            reconcile = grp[0]
            differences = ''
        else:
            consensus_ind, clean_grp, outliers_ = check_outlier(grp)
            if consensus_ind >= 0 and len(clean_grp) >= 1:
                reconcile = grp[consensus_ind]
                differences = ''
            elif len(clean_grp) >= 2:
                reconcile = ''
                differences = peel_common_end_groups(clean_grp)
                flag = True
                while flag:
                    flag = False
                    next_differences = []
                    for snippet in differences:
                        if type(snippet) is list:
                            expanded_snippet = peel_longest_common_substring(snippet)
                            if expanded_snippet == snippet:  # ie no common substring longer than 3
                                next_differences.append('§' + str(sorted(sorted(sorted(snippet),
                                                                                key=len, reverse=True),
                                                                         key=snippet.count, reverse=True)))
                            else:
                                flag = True
                                next_differences.extend(expanded_snippet)
                        else:
                            next_differences.append(snippet)
                    differences = next_differences
            else:  # clean_grp is empty - normally an error with the lines drawn or low agreement between all responses
                reconcile = 'UNRESOLVED '
                differences = str(grp)

        if differences:
            for string in differences:
                if string.find('§') >= 0:
                    reconcile += ast.literal_eval(string[1:])[0]
                else:
                    reconcile += string
        full_reconciled_text += ''.join(reconcile).replace('ø', '') + '\n'
        full_differences_text += '·' + ''.join(differences).replace('§', '') + '\n'
        full_outliers += '·' + outliers_ + '\n'
    return full_reconciled_text.strip('\n'), full_differences_text.strip('\n'), full_outliers.strip('\n')


def process_aggregation(sub, metadata_, image_width_, agg_list):
    line_height = round(image_width_ / width_to_line_ratio)
    positional_scan = line_scan.LINESCAN(.7 * line_height)
    positional_scan.cluster(agg_list)
    positional_clusters = positional_scan.clusters
    to_replace = []
    to_add = []
    for ind, cluster in enumerate(positional_clusters):
        if len(cluster[2]) > 5:
            word_grp = wordcan.WORDCAN(20, 2, ratio='ratio')
            word_grp.cluster(cluster[2])
            if len(word_grp.clusters) > 1:
                to_replace.append(ind)
                to_add.extend(word_grp.clusters)
    if to_replace:
        for index in reversed(to_replace):
            del positional_clusters[index]
        positional_clusters.extend(to_add)
    if page == 'bmt':
        sorted_grouped_transcriptions = positional_sort_bmt(line_height, positional_clusters)

    elif page == 'single':
        sorted_grouped_transcriptions = positional_sort_single_page(line_height, positional_clusters)
    else:  # default or 'double' page
        sorted_grouped_transcriptions = positional_sort_double_page(image_width_,
                                                                    line_height, positional_clusters)
    text_format, differences, outliers = reconcile_and_assemble(sorted_grouped_transcriptions)
    # and then write the grouped transcriptions to a file
    new_row = {'subject_id': sub,
               'text_format': text_format,
               'differences': differences,
               'outliers': outliers,
               'noise': str(positional_scan.noise)[1:-1]
               }
    new_row.update(metadata_)
    return new_row


def aggregate(sort_loc, aggregate_loc):
    with open(aggregate_loc, 'w', newline='', encoding='utf-8-sig') as ag_file:
        fieldnames = ['subject_id']
        fieldnames.extend(metadata_fields)
        fieldnames.extend(['text_format', 'differences', 'outliers', 'noise'])
        writer = csv.DictWriter(ag_file, fieldnames=fieldnames)
        writer.writeheader()

        # set up to read the flattened file

        with open(sort_loc, encoding='utf-8') as s_file:
            r = csv.DictReader(s_file)

            # initialize a starting point subject and empty bins for aggregation
            subject = ''
            i = 0
            j = 0
            aggregate_list = []
            metadata = {}
            # Loop over the flattened records
            for row in r:
                j += 1
                # read a row and pullout the flattened data fields we need to aggregate, or pass through.
                new_subject = row['subject_id']
                transcription_list = json.loads(row['transcription_list'])
                # test for a change in the selector - in this case the selector is the subject
                if new_subject != subject:
                    if i != 0:  # if not the first line, we have aggregated all the classifications for
                        # this subject and we can analyse the aggregated fields and output the results.

                        writer.writerow(process_aggregation(subject, metadata, image_width, aggregate_list))

                    # To star the next group, reset the selector, and the bin for the next aggregation.
                    i = 1
                    subject = new_subject
                    aggregate_list = transcription_list[:]
                    image_width = int(row['image_width'])
                    for metadata_field in metadata_fields:
                        metadata[metadata_field] = row[metadata_field]

                else:
                    # the selector has not yet changed so we continue the aggregation:
                    # First test for multiple classifications by the same user on this subject, and
                    # if we want to use a fixed number of classifications and a few subjects have
                    # more than the retirement limit (here set at 40).
                    aggregate_list.extend(transcription_list[:])
                    i += 1
                if j % 10000 == 0:
                    print(j)

            # catch and process the last aggregated group
            writer.writerow(process_aggregation(subject, metadata, image_width, aggregate_list))
            print(j)
    return True


# This section defines a sort function. Note the fields are numbered starting from '0'
def natsort_double(input_file, output_file_sorted, field_1, field_2, reverse, clean):
    #  This allows a sort of the output file on two specific fields.  In this case internal_id then group_id
    with open(input_file, 'r', encoding='utf-8-sig') as in_file:
        in_put = csv.reader(in_file)
        headers = in_put.__next__()
        sort_on_internal_id = natsorted(in_put, key=operator.itemgetter(field_1), reverse=reverse)
        sort_on_group_id = natsorted(sort_on_internal_id, key=operator.itemgetter(field_2), reverse=reverse)
        with open(output_file_sorted, 'w', newline='', encoding='utf-8-sig') as sorted_out:
            write_sorted = csv.writer(sorted_out, delimiter=',')
            write_sorted.writerow(headers)
            sort_counter = 0
            for line_ in sort_on_group_id:
                write_sorted.writerow(line_)
                sort_counter += 1
    if clean:  # clean up temporary file
        try:
            os.remove(input_file)
        except OSError:
            print('temp file not found and not deleted')
    return sort_counter


# The main script.
if __name__ == '__main__':
    # get data export file path and file name from arguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description=textwrap.dedent("""  
            The first step is to define the input files and path for the 
            data export file using parameters. This is done by giving the 
            script two parameters, 1) a working directory path where the 
            data export and the output file will reside, and 2) the name of 
            the data export file if has not been renamed to the default name 
            "workflow_data_XXXXXX.csv where "XXXXXXX" is the workflow-id.

            Then the workflow_id and the list of the of the metadata field names
            if it is not the default list given below.

            Finally various limits to the output may be defined:  The default is "all",
            where all available records will be output, option one is a upper and 
            lower limit for subject_ids to be included, and option two is a 
            list of the group_id's to be included. 
            """))

    parser.add_argument(
        '-d', '--directory', default='.',
        help=textwrap.dedent(r"""The path and directory where the input and output
        files, are located. It defaults to the directory where this script is 
        running.         
        example '-d C:\py\BMT_collections' """))

    parser.add_argument(
        '-f', '--file', default='workflow_data',
        help=textwrap.dedent("""The data export .csv file to flatten. 
        It must be in the working directory.  This is a copy of the data export
        as requested and downloaded from the project builder, preferably by workflow.
        The output files will have the same name as the data export input file, 
        with the limits if any, and with either "_sorted", (the flattened data) or 
        "reconciled" (the aggregated and reconciled data) added prior to the file extension. 
        Generally the data export file should be renamed to  "workflow_data_XXXXXX.csv where 
        "XXXXXXX" is the workflow-id, in which case this parameter is optional.
        example: "-f workflow_data_26197.csv" """))

    parser.add_argument(
        '-m', '--metadata_fields', default='Year;"File Name";register_name',
        help=textwrap.dedent("""This is a list of the subject metadata fields to extract and 
        add to the output files.  Two fields "group_id" and "internal_id" are mandatory and 
        do not need top be listed. The list is strings separated by semicolons with any value 
        with spaces enclosed in quotes (see default).  If the default value shown here has 
        been modified for your project, then this parameter is optional.
        example: "-m filename;"page number"; """))

    parser.add_argument(
        '-w', '--workflow',
        help=textwrap.dedent("""The transcription based workflow_id that is to be parsed.
        This is a required field and is used to generate the default names for the input 
        files.
        example: '-w 25224'"""))

    parser.add_argument(
        '-t', '--task', default='T0',
        help=textwrap.dedent("""The line transcription task number that is to be parsed.
        This defaults to 'T0' where the line transcription task was defined as the first  
        task in the workflow and is not required if that is the case.
        example: "-t T0"""))

    parser.add_argument(
        '-l', '--limits', default='all',
        help=textwrap.dedent("""This parameter is used to limit the output to selected 
        ranges of zooniverse subject_id or group_id's.  The default is for all records
        in the data export for the workflow, but in general unless all the data is complete 
        at the time the export was requested, some form of limits need to be given.  
        There are two options:
        1) A range of subject_ids to include - two integers in any order representing the 
        upper and lower limits of the range of subject id's to be included 
        example: "-l 1000;103000000"  This would effectively include any subject_id  less 
        than 103000000. Note use of semicolon and no spaces
        2) A list of group_id's to include.  These must listed EXACTLY as the group_id given 
        in the subject metadata. The easiest way to create the list is to copy and paste from 
        the metadata for an example subject in the desired subject set via the project builder.                        
        example 1: "-l archaeology_and_folk_life_1962" 
        example 2: "-l archaeology_and_folk_life_1961;archaeology_and_folk_life_1962"
        Note use of semicolon and no spaces.  """))

    parser.add_argument(
        '-p', '--pagination', default='double',
        help=textwrap.dedent("""This parameter is used to adjust the sorting of 
        the consensus text into pages. Currently there are three options, the default 
        assumes double pages and places lines beginning 45%% of the image width from 
        the left into Page 2, separated from Page 1 lines by two empty lines. This 
        option also works fine for single page images where lines all begin at the 
        left margin.  Single page can be forced using a value "single" and a special 
        formatting for Birimingham Museum Trust can be selected using a value "bmt".   
        The latter may be useful where the text is in rough columns with multiple 
        segments spread across the page.  All versions add a horizontal sort for line 
        segments that are nearly at the same vertical position, listing them from left 
        to right for each page.  example: "-p single" """))

    parser.add_argument(
        '-s', '--width_to_line_ratio', default=26,
        help=textwrap.dedent("""This parameter is used to adjust the clustering of drawn lines
        to aggregate correlated text.  This value may vary from subject set to subject set depending 
        on the typeset, hand writing, paper or journal size, and how the material was scanned.
        To estimate a reasonable number, divide the width of a scanned cropped subject in pixels
        by the pixel height of an average line of text in the image.  If this number as selected 
        is too large, lines that should NOT be aggregated together will be, though there is a 
        second step that would then separate the lines IF the text in the two lines is dissimilar.
        If the value is too small, then lines that should aggregate together may end up being 
        reconciled separately adding additional near identical lines of text.  Scans which are 
        narrower in width relative to the line height need smaller number.  Text that is spread 
        out in width relative to line height need a larger number.                         
        example: "-s 40" """))

    args = parser.parse_args()
    directory = args.directory
    if directory == '.':
        directory = os.getcwd()
    if not os.path.exists(directory):
        print('The directory parameter -d', directory, 'is not a valid path')
        quit()

    workflow = str(args.workflow)

    line_trans_task = args.task
    line_task_details = line_trans_task + '.0.0'

    workflow_data = args.file
    if workflow_data == 'workflow_data':  # default
        workflow_data = join(directory, workflow_data + '_' + workflow + '.csv')
    else:
        workflow_data = join(directory, workflow_data)
    if not os.path.isfile(workflow_data):
        print('The file ', workflow_data, 'was not found')
        quit()

    metadata_list = args.metadata_fields
    metadata_fields = ['group_id', 'internal_id']
    metadata_fields.extend([a.replace('"', '') for a in metadata_list.split(';')])

    raw_limits = args.limits
    if raw_limits == 'all':
        sub_limits = []
        group_ids = []
    else:
        limits = raw_limits.split(';')
        try:
            sub_limits = [max(int(limits[0]), int(limits[1])), min(int(limits[0]), int(limits[1]))]
            group_ids = []
        except ValueError:
            sub_limits = []
            group_ids = limits

    try:
        width_to_line_ratio = int(args.width_to_line_ratio)
    except ValueError:
        print('The width_to_line_ratio "', args.width_to_line_ratio, '" is not an integer.')
        quit()

    page = args.pagination  # get preferred pagination type

    # Script settings and file locations:
    unsorted_location = workflow_data[:-4] + '_flattened.csv'
    sorted_location = workflow_data[:-4] + '_' + raw_limits + '_sorted.csv'
    aggregated_location = workflow_data[:-4] + '_aggregated.csv'
    tic = time.perf_counter()
    print(flatten_class(workflow_data, unsorted_location, sub_limits, group_ids))
    print(sort_file(unsorted_location, sorted_location, 0, False, True), 'lines sorted and written')
    print(aggregate(sorted_location, aggregated_location))
    toc = time.perf_counter()
    print(natsort_double(aggregated_location, workflow_data[:-4] + '_'
                         + raw_limits + '_reconciled.csv', 2, 1, False, True))
    print(f"aggregated and processed {toc - tic:0.2f} seconds")
