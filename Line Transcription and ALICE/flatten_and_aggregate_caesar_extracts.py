# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# built in packages:
import argparse
import textwrap
import csv
import json
import os
from os.path import join
import operator
from fuzzywuzzy import fuzz
import numpy as np
from natsort import natsorted
import line_scan
import wordcan


# define a function that returns True or False based on whether the record is to be included
def include(class_record, sub_limits_, group_ids_):
    if class_record['extractor_key'] != 'alice':
        return False
    else:
        pass
    if sub_limits_:
        if sub_limits_[0] >= int(class_record['subject_id']) >= sub_limits_[1]:
            return True  # this one can be used to select a range of subjects
        else:
            return False
    if group_ids_:
        if metadata_x_ref[class_record['subject_id']]['group_id'] in group_ids_:
            return True  # this one selects based on group_id
        else:
            return False
            # otherwise :
    return True


def load_metadata_x_ref(input_filename):
    # Open the input file and set up for reading
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader_ = csv.DictReader(infile)
        metadata_x_ref_ = {}
        # Iterate through each row in the input file
        for row in reader_:
            # Extract metadata
            try:
                metadata_x_ref_[row["subject_id"]] = {"group_id": row["group_id"],
                                                      "internal_id": row["internal_id"],
                                                      "year": row["year"],
                                                      "File Name": row["File Name"],
                                                      "register_name": row["register_name"],
                                                      "image_width": int(row["image_width"])
                                                      }
            except KeyError:
                print(row["subject_id"], 'missing metadata fields')
                continue
        return metadata_x_ref_


def clean_and_decorate(text):
    return text.replace('\n', ''). \
        replace('[deletion]', '˄').replace('[/deletion]', '˄'). \
        replace('[insertion]', '˅').replace('[/insertion]', '˅'). \
        replace('[unclear]', '‽').replace('[/unclear]', '‽').\
        replace('[underline]', 'µ').replace('[/underline]', 'µ').\
        replace('[Underline]', 'µ').replace('[/Underline]', 'µ').strip(' ')


#  The next section flattens the Subject extracts by subject
def flatten_class(zoo_file, out_loc, sub_limits_, group_ids_):
    with open(out_loc, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['subject_id',
                      'workflow_id',
                      'transcription_list'
                      ]
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
                if include(row, sub_limits_, group_ids_) is True:
                    data_frame0 = row['data.frame0']
                    if data_frame0:
                        try:
                            data = json.loads(data_frame0)
                        except json.decoder.JSONDecodeError:
                            print(data_frame0)
                            print('json error', row['subject_id'])
                            quit()
                        next_row = {'subject_id': row['subject_id'],
                                    'workflow_id': row['workflow_id']
                                    }
                        transcription_list = []
                        for index in range(0, len(data['text'])):
                            # pull out transcription , midpoint y,  min x
                            try:
                                x = min(int(data['points']['x'][index][0] + .5),
                                        int(data['points']['x'][index][1] + .5))
                                y = int((data['points']['y'][index][0] +
                                         data['points']['y'][index][1]) / 2 + .5)
                                transcription_list.append((x, y, clean_and_decorate(data['text'][index][0])))
                            except KeyError:
                                print(row['subject_id'], 'Check extracts structure, failed flattening step')
                                continue
                        next_row['transcription_list'] = json.dumps(transcription_list)

                        writer.writerow(next_row)
                        j += 1
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


def positional_sort(line_height_, grp_trans):
    if len(grp_trans) == 1:
        return grp_trans
    sorted_x_y = sorted(grp_trans, key=operator.itemgetter(1))
    final_sorted_grp_trans = []
    x_left = 0

    # get header - consecutive lines x aligned to left half of top of page
    header = []
    for line in sorted_x_y:
        if line[0] > 12 * line_height_:
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

        poor_match = 0
        for j in range(0, len(grp_)):
            if similarity_[i, j] <= .65:
                poor_match += 1
        if poor_match > int(len(grp_) / 2 + 1):
            to_remove_.append(grp_[i])

    cleaned_grp_ = [grp_[k] for k in range(0, len(grp_)) if grp_[k] not in to_remove_]

    if max_ones / len(grp_) >= .8:
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
        start = 'ø'
    # peel off common finish
    f, finish = common_finish(grp_[0], grp_[1])
    if len(grp_) == 2:
        grp_ = [grp_[0][:-f], grp_[1][:-f]]
    for index in range(2, len(grp_)):
        f, finish = common_finish(grp_[index], finish)
    if f > 0:
        grp_ = [gr[: -f] for gr in grp_]
    else:
        finish = 'ø'
    return [start, ['ø' if t == '' else t for t in grp_], finish]


def longestcommonsubstr(s1, s2):
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
    s, end, lcs = longestcommonsubstr(snip[0], snip[1])
    if end - s > 2:
        if len(snip) == 2:
            snip_before = [snip[0][:s], snip[1][:s]]
            snip_after = [snip[0][end:], snip[0][end:]]
            return [snip_before, lcs, snip_after]
        else:
            for index in range(2, len(snip)):
                s, end, lcs = longestcommonsubstr(snip[index], lcs)
            if end - s > 2:
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


def sort_clean(snippet_):
    sorted_snippet_ = sorted(sorted(snippet_), key=snippet_.count, reverse=True)
    string_snippet_ = str(['ø' if t == '' else t for t in sorted_snippet_])
    whitespace_snippet = [t for t in sorted_snippet_ if t.replace(' ', '') not in ['ø', '']]
    if not whitespace_snippet:
        return '', ''
    return string_snippet_, sorted_snippet_[0]


def reconcile_and_assemble(sorted_grp_trans):
    full_reconciled_text = ''
    full_differences_text = ''
    full_outliers = ''
    for line_group in sorted_grp_trans:
        grp = [text for _, _, text in line_group[2]]
        differences = ''
        outliers_ = ''
        if len(grp) == 1:
            reconcile = grp[0]
        else:
            consensus_ind, clean_grp, outliers_ = check_outlier(grp)
            if consensus_ind >= 0 and len(clean_grp) >= 1:
                reconcile = grp[consensus_ind]
            elif len(clean_grp) >= 2:
                reconcile = peel_common_end_groups(clean_grp)
                while True:
                    next_reconcile = []
                    next_differences = []
                    for snippet in reconcile:
                        if type(snippet) is list:
                            expanded_snippet = peel_longest_common_substring(snippet)
                            if expanded_snippet == snippet:  # ie no common substring longer than 3
                                string_snippet, resolved_string = sort_clean(snippet)
                                next_reconcile.append(resolved_string)
                                next_differences.append(string_snippet)
                            else:
                                next_reconcile.extend(expanded_snippet)
                                next_differences.extend(expanded_snippet)
                        else:
                            next_reconcile.append(snippet)
                            next_differences.append(snippet)
                    reconcile = next_reconcile
                    differences = next_differences
                    if 'list' not in list(type(x).__name__ for x in reconcile):
                        break
            else:  # clean_grp is empty - normally an error with the lines drawn
                reconcile = ['UNRESOLVED']
                differences = str(grp)
        if reconcile:
            full_reconciled_text += ''.join(reconcile).replace('ø', '') + '\n'
            full_differences_text += '·' + ''.join(differences) + '\n'  # .replace('ø', '')
            full_outliers += '·' + outliers_ + '\n'
    return full_reconciled_text.strip('\n'), full_differences_text.strip('\n'), full_outliers.strip('\n')


def process_aggregation(sub, agg_list):
    line_height = round(int(metadata_x_ref[sub]["image_width"]) / width_to_line_ratio)
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
    sorted_grouped_transcriptions = positional_sort(line_height, positional_clusters)
    text_format, differences, outliers = reconcile_and_assemble(sorted_grouped_transcriptions)
    # and then write the grouped transcriptions to a file
    new_row = {'subject_id': sub,
               "year": metadata_x_ref[sub]["year"],
               "group_id": metadata_x_ref[sub]["group_id"],
               "File Name": metadata_x_ref[sub]["File Name"],
               "internal_id": metadata_x_ref[sub]["internal_id"],
               "register_name": metadata_x_ref[sub]["register_name"],
               'text_format': text_format,
               'differences': differences,
               'outliers': outliers,
               'noise': str(positional_scan.noise)[1:-1]
               }
    return new_row


def aggregate(sort_loc, aggregate_loc):
    with open(aggregate_loc, 'w', newline='', encoding='utf-8-sig') as ag_file:
        fieldnames = ['subject_id',
                      "group_id",
                      "internal_id",
                      "year",
                      "File Name",
                      "register_name",
                      'text_format',
                      'differences',
                      'outliers',
                      'noise'
                      ]
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

                        writer.writerow(process_aggregation(subject, aggregate_list))

                    # To star the next group, reset the selector, and the bin for the next aggregation.
                    i = 1
                    subject = new_subject
                    aggregate_list = transcription_list[:]
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
            writer.writerow(process_aggregation(subject, aggregate_list))
            print(j)
    return True


# This section defines a sort function. Note the fields are numbered starting from '0'
def natsort_double(input_file, output_file_sorted, field_1, field_2, reverse, clean):
    #  This allows a sort of the output file on a specific fields.
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
    # get subject extracts file, and cross reference file,  path and file names from arguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description=textwrap.dedent("""  
            The first step is to define the input files and path for the 
            subject extracts file using parameters. This is done by giving the 
            script two parameters, 1) a working directory path where the 
            subject extracts file, the cross reference to the metadata and 
            the output file will reside, and 2) the name of 
            the subject_extracts.csv file if it is not the default name 
            "Subject_extracts_XXXXXX.csv where "XXXXXXX" is the workflow-id.
             
            Then the workflow_id and the name of the metadata cross reference 
            file if it is not the default "metadata_crossreference_[workflow_id].csv".
            Finally various limits to the output may be defined:  The default is "all",
            where all available records will be output, option one is a upper and 
            lower limit for subject_ids to be included, and option two is a 
            list of the group_id's to be included. 
            """))

    parser.add_argument(
        '-d', '--directory', default='.',
        help=textwrap.dedent("""The path and directory where the input and output
        files, are located. It defaults to the directory where this script is 
        running.         
        example '-d C:\py\BMT_collections' """))

    parser.add_argument(
        '-f', '--file', default='Subject_extracts',
        help=textwrap.dedent("""The subject_extracts.csv file to parse. 
        It must be in the working directory.  This is a copy of the caesar extracts
        as requested and downloaded from the caesar data requests for the workflow.
        The output files will have the same name as the subject_extracts input file 
        with either "_sorted", (the flattened data) or "aggregated_sorted" (the 
        aggregated and reconciled data) added prior to the file extension. Generally 
        the extracts file should be renamed to  "Subject_extracts_XXXXXX.csv where 
        "XXXXXXX" is the workflow-id, in which case this parameter is optional.
        example: "-f Subject_extracts_26197.csv" """))

    parser.add_argument(
        '-x', '--xreference', default='metadata_crossreference',
        help=textwrap.dedent("""The metadata_crossreference_[workflow_id].csv file. 
        It must be in the working directory.  This is a cross reference between the 
        zooniverse subject number and the subject metadata.  It is produced from a 
        workflow data export requested through the project builder using the script 
        "generate_metadata_x_ref_from_data_export.py".  Generally it will be called
        "metadata_crossreference_XXXXXX.csv where "XXXXXXX" is the workflow_id, in 
        which case this parameter is optional.
        example: "-x metadata_crossreference_25224.csv" """))

    parser.add_argument(
        '-w', '--workflow',
        help=textwrap.dedent("""The transcription based workflow_id that is to be parsed.
        This is a required field and is used to generate the default names for the input 
        files.
        example: "-w 25224"""))

    parser.add_argument(
        '-l', '--limits', default='all',
        help=textwrap.dedent("""This parameter is used to limit the output to selected 
        ranges of zooniverse subject_id or group_id's.  The default is for all records
        in the subject extracts, but in general unless all the data is complete at the 
        time the extracts were exported, some form of limits need to be given.  
        There are two options:
        1) A range of subject_ids to include - two integers in any order representing the 
        upper and lower limits of the range of id's to be included 
        example: "-l 1000;103000000"  This would effectively include any subject_id  less 
        than 103000000. Note use of semicolon and no spaces
        2) A list of group_id's to include.  These must listed EXACTLY as the group_id given 
        in the subject metadata. The easiest way to create the list is to copy and paste from 
        the metadata cross reference file, though the group_id can be obtained from the project 
        lab for a subject set by looking at the metadata of an included subject.                        
        example 1: "-l archaeology_and_folk_life_1962" 
        example 2: "-l archaeology_and_folk_life_1961;archaeology_and_folk_life_1962"
        Note use of semicolon and no spaces.  """))

    parser.add_argument(
        '-s', '--width_to_line_ratio', default=26,
        help=textwrap.dedent("""This parameter is used to adjust the clustering of drawn lines
        to aggregate correlated text.  This value may vary from register to register depending 
        on the typeset, hand writing, paper or journal size, and how the material was scanned.
        To estimate a reasonable number, divide the width of a scanned cropped subject in pixels
        by the pixel height of an average line of text in the image.  If this number as selected 
        is too large, lines that should NOT be aggregated together will be, though there is a 
        second step that would then separate the lines IF the text in the two lines is dissimilar.
        If the value is too small, then lines that should aggregate together may end up being 
        reconciled separately adding additional near identical lines of text.  Much of the 
        handwritten entries have been resolved with a value of 26 while the typewritten work may 
        require a larger number.  Scans which are narrower in width relative to the line height 
        need smaller number.  Text that is spread out in width relative to line height need a 
        larger number.                         
        example: "-s 40" """))

    args = parser.parse_args()
    directory = args.directory
    if directory == '.':
        directory = os.getcwd()
    if not os.path.exists(directory):
        print('The directory parameter -d', directory, 'is not a valid path')
        quit()

    workflow = str(args.workflow)

    subject_extracts = args.file
    if subject_extracts == 'Subject_extracts':  # default
        subject_extracts = join(directory, subject_extracts + '_' + workflow + '.csv')
    else:
        subject_extracts = join(directory, subject_extracts)
    if not os.path.isfile(subject_extracts):
        print('The file ', subject_extracts, 'was not found')
        quit()

    metadata_crossreference = args.xreference
    if metadata_crossreference == 'metadata_crossreference':  # default
        metadata_crossreference = join(directory, metadata_crossreference + '_' + workflow + '.csv')
    else:
        metadata_crossreference = join(directory, metadata_crossreference)
    if not os.path.isfile(metadata_crossreference):
        print('The cross-reference file ', metadata_crossreference, 'was not found')
        quit()

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

    # Script settings and file locations:
    unsorted_location = subject_extracts[:-4] + '_flattened.csv'
    sorted_location = subject_extracts[:-4] + '_' + raw_limits + '_sorted.csv'
    aggregated_location = subject_extracts[:-4] + '_aggregated.csv'
    metadata_x_ref = load_metadata_x_ref(metadata_crossreference)

    print(flatten_class(subject_extracts, unsorted_location, sub_limits, group_ids))
    print(sort_file(unsorted_location, sorted_location, 0, False, True), 'lines sorted and written')
    print(aggregate(sorted_location, aggregated_location))

    print(natsort_double(aggregated_location, subject_extracts[:-4] + '_'
                         + raw_limits + '_reconciled.csv', 2, 1, False, True))