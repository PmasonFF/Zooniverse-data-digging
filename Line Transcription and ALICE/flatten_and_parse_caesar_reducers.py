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
from natsort import natsorted


# define a function that returns True or False based on whether the record is to be included
def include(class_record, sub_limits_, group_ids_):
    if class_record['reducer_key'] != 'alice':
        return False
    else:
        pass
    if sub_limits_:
        if sub_limits_[0] >= int(class_record['subject_id']) >= sub_limits_[1]:
            return True  # this condition can be used to select a range of subjects
        else:
            return False
    if group_ids_:
        if metadata_x_ref[class_record['subject_id']]['group_id'] in group_ids_:
            return True  # this condition selects based on group_id
        else:
            return False
            # otherwise :
    return True


def load_metadata_x_ref(input_filename):
    # Open the cross reference file and set up for reading
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader_ = csv.DictReader(infile)
        metadata_x_ref_ = {}
        # Iterate through each row in the input file
        for row in reader_:
            metadata_x_ref_[row["subject_id"]] = row
        columns_ = list(row.keys())
        return columns_, metadata_x_ref_


def clean_and_decorate(text):
    return text.replace('\n', ''). \
        replace('[deletion]', '˄').replace('[/deletion]', '˄'). \
        replace('[insertion]', '˅').replace('[/insertion]', '˅'). \
        replace('[unclear]', '‽').replace('[/unclear]', '‽'). \
        replace('[underline]', 'µ').replace('[/underline]', 'µ'). \
        replace('[Underline]', 'µ').replace('[/Underline]', 'µ').strip(' ')


def positional_sort_bmt(line_height_, grp_trans):
    if len(grp_trans) == 1:
        return grp_trans
    sorted_y = sorted(grp_trans, key=operator.itemgetter(1))
    final_sorted_grp_trans = []
    x_left = 0

    # get header - consecutive lines x aligned to left half of top of page
    header = []
    for line in sorted_y:
        if line[0] > 12 * line_height_:  # test for line(s) at top with min x to right side (header)
            header.append(line)
        else:
            break
    if header:
        for line in header:
            sorted_y.remove(line)
        final_sorted_grp_trans.extend(header)

    # get top lines of text that are within .7 lh vertical of upper-most line, after header removed:
    top_lines = []
    if sorted_y:
        y_top_line = sorted_y[0][1]
        for line in sorted_y:
            if line[1] - y_top_line <= .7 * line_height_:
                top_lines.append(line)
            else:
                break

    # get object number column - lines that are x aligned +- 1 lh of left-most top line
    # and y aligned within 1.3 lh of previous object line - generally the object number and revisions below it,
    # but it can include part or all of the middle block if there is no object number indent
    if top_lines:
        object_lines = []
        sorted_top_x = sorted(top_lines, key=operator.itemgetter(0))
        current_y_min = top_lines[0][1]
        x_left = sorted_top_x[0][0]
        for line in sorted_y:
            if abs(line[0] - x_left) <= line_height_ and line[1] - current_y_min < 1.3 * line_height_:
                object_lines.append(line)
                current_y_min = line[1]
        if object_lines:
            for line in object_lines:
                sorted_y.remove(line)
            final_sorted_grp_trans.extend(object_lines)

    # get far left notes - these are x aligned at least 3 lh left of the left-most line so far
    far_left = []
    if sorted_y:
        for line in sorted_y:
            if x_left - line[0] > 3 * line_height_:
                far_left.append(line)
        if far_left:
            for line in far_left:
                sorted_y.remove(line)

    # everything else is in the main block
    main_block = []
    if sorted_y:
        current_y_min = sorted_y[0][1]
        while True:
            same_line = [sorted_y[0]]
            for line in sorted_y[1:]:
                if line[1] - current_y_min <= .5 * line_height_:
                    same_line.append(line)
            main_block.extend(sorted(same_line, key=operator.itemgetter(0)))
            if same_line:
                for line in same_line:
                    sorted_y.remove(line)
            if sorted_y:
                current_y_min = sorted_y[0][1]
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
            sorted_grp_trans.append((0, 0, '\n'))
    return sorted_grp_trans


#  The next section flattens the Subject reducers by subject
def flatten_class(zoo_file, out_loc, sub_limits_, group_ids_, page_):
    with open(out_loc, 'w', newline='', encoding='utf-8-sig') as file:
        columns.extend(['workflow_id', 'transcription_text'])
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        # this area for initializing counters:
        i = 0
        j = 0
        with open(zoo_file, 'r', encoding='utf-8') as csvfile:
            dictreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in dictreader:
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
                        next_row = metadata_x_ref[row['subject_id']]  # bring in metadata from cross reference
                        next_row['workflow_id'] = row['workflow_id']
                        transcription_list = []
                        for text_line in data:
                            # pull out transcription , midpoint y, min x
                            try:
                                x = min(int(text_line['clusters_x'][0] + .5),
                                        int(text_line['clusters_x'][1] + .5))  # x is leftmost end of line
                                y = int((text_line['clusters_y'][0] +
                                         text_line['clusters_y'][1]) / 2 + .5)  # y is vertical midpoint
                                transcription_list.append((x, y, clean_and_decorate(text_line['consensus_text'])))
                            except KeyError:
                                print(row['subject_id'], 'Check reducer structure, failed flattening step')
                                continue
                        image_width = int(metadata_x_ref[row['subject_id']]["image_width"])
                        line_height = round(image_width / width_to_line_ratio)
                        if page_ == 'bmt':
                            sorted_transcription_list = positional_sort_bmt(line_height, transcription_list)
                        elif page_ == 'single':
                            sorted_transcription_list = positional_sort_single_page(line_height, transcription_list)
                        else:  # default or 'double' page
                            sorted_transcription_list = positional_sort_double_page(image_width,
                                                                                    line_height, transcription_list)
                        full_text = ''
                        for text in sorted_transcription_list:
                            full_text += text[2] + '\n'  # assemble full text in sorted order
                        next_row['transcription_text'] = full_text.strip('\n')  # remove final line feed
                        writer.writerow(next_row)
                        j += 1
                if i % 20000 == 0:
                    print(i, j)
            print(i, j)
        return str(i) + ' Lines read and ' + str(j) + ' records processed'


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
    # get subject extracts file, and cross reference file,  path and file names from arguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description=textwrap.dedent("""  
            The first step is to define the input files and path for the subject 
            reducer export file using parameters. This is done by giving the 
            script two parameters, 1) a working directory path where the subject 
            reducer export file, the cross reference to the metadata and the 
            output file will reside, and 2) the name of the subject_reducer.csv 
            file if it is not renamed to the default name 
            "Subject_reducer_export_XXXXXX.csv where "XXXXXXX" is the workflow-id. 
                        
            Then define the workflow_id and the name of the metadata cross reference 
            file if it has not been named the default 
            "metadata_crossreference_[workflow_id].csv".
            
            Finally various limits to the output may be defined:  The default is 
            "all", where all available records will be output, option 1)is a upper 
            and lower limit for subject_ids to be included, and option 2)is a list 
            of the group_id's to be included. 
            """))

    parser.add_argument(
        '-d', '--directory', default='.',
        help=textwrap.dedent("""The path and directory where the input and 
        output files, are located. It defaults to the directory where this 
        script is running.  example '-d C:\py\BMT_collections' """))

    parser.add_argument(
        '-f', '--file', default='Subject_reducer_export',
        help=textwrap.dedent("""The subject_reducer export.csv file to parse. 
        It must be in the working directory.  This is a copy of the caesar 
        reductions as requested and downloaded from the caesar data requests 
        for the workflow in question.
        The output files will have the same name as the subject_reducer input 
        file with "_sorted" added prior to the file extension. Generally the 
        reducer export file should be renamed to  
        "Subject_reducer_export_XXXXXX.csv where "XXXXXXX" is the workflow-id.
        If this is done, this parameter is optional.
        example: "-s Subject_reducer_export_26197.csv" """))

    parser.add_argument(
        '-x', '--xreference', default='metadata_crossreference',
        help=textwrap.dedent("""The metadata_crossreference_[workflow_id].csv 
        file. It must be in the working directory.  This is a cross reference 
        between the zooniverse subject number and the subject metadata.  It is 
        produced from a workflow data export requested through the project 
        builder using the script "generate_metadata_x_ref_from_data_export.py".  
        Generally it will be called "metadata_crossreference_XXXXXX.csv where 
        XXXXXXX" is the workflow_id, in  which case this parameter is optional.  
        The cross reference must have at least four columns: subject_id, 
        internal_id, group_id, and image_width, and may have others.
        example: "-x metadata_crossreference_25224.csv" """))

    parser.add_argument(
        '-w', '--workflow',
        help=textwrap.dedent("""The transcription based workflow_id that is to 
        be parsed. This is a required field and is used to generate the default 
        names for the input files.   example: "-w 25224"""))

    parser.add_argument(
        '-l', '--limits', default='all',
        help=textwrap.dedent("""This parameter is used to limit the output to 
        selected ranges of zooniverse subject_id or group_id's.  The default is 
        for all records in the subject reductions, but in general unless all the 
        data is complete at the time the reductions were exported, some form of 
        limits need to be given.  
        There are two options:
        1) A range of subject_ids to include - two integers in any order being 
        the upper and lower limits of the range of subject id's to be included.l 
        example: "-l 1000;103000000"  This would effectively include any 
        subject_id  less than 103000000. Note use of semicolon and no spaces.
        2) A list of group_id's to include.  These must listed EXACTLY as the 
        group_id given in the subject metadata. The easiest way to create the 
        list is to copy and paste from the metadata cross reference file, though 
        the group_id can be obtained from the project lab for a subject set by 
        looking at the metadata of an included subject.                        
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
        formating for Brimingham Museum Trust can be selected using a value "bmt".   
        The latter may be useful where the text is in rough columns with multiple 
        segments spread across the page.  All versions add a horizontal sort for line 
        segments that are nearly at the same vertical position, listing them from left 
        to right for each page.  example: "-p single" """))

    parser.add_argument(
        '-s', '--width_to_line_ratio', default=30,
        help=textwrap.dedent("""This parameter is used to adjust the sorting and 
        display of the consensus text into pages. In this script using the subject 
        reductions. It DOES NOT affect the clustering of text lines.  It is not directly 
        the line height which may vary from subject to subject depending on how the  
        material was scanned. To estimate a reasonable number, divide the width of a 
        typical subject image in pixels by the pixel height of an average line of text 
        in that image.  Hopefully this ratio is consistent across subjects which have 
        been scanned similarly but possibly resized variable amounts for uploading.  
        If this number as selected is too small or too large the order that the 
        consensus text is listed may be less than desirable. Scans which are narrower 
        in width relative to the line height need a smaller number.  Text that is 
        spread out in width relative to line height need a larger number.                         
        example: "-s 40" """))

    args = parser.parse_args()
    directory = args.directory
    if directory == '.':
        directory = os.getcwd()
    if not os.path.exists(directory):
        print('The directory parameter -d', directory, 'is not a valid path')
        quit()

    workflow = str(args.workflow)

    subject_reducer = args.file
    if subject_reducer == 'Subject_reducer_export':  # ie the default file name with the workflow_id added in
        subject_reducer = join(directory, subject_reducer + '_' + workflow + '.csv')
    else:
        subject_reducer = join(directory, subject_reducer)
    if not os.path.isfile(subject_reducer):
        print('The file ', subject_reducer, 'was not found')
        quit()

    metadata_crossreference = args.xreference
    if metadata_crossreference == 'metadata_crossreference':  # ie the default file name with the workflow_id added in
        metadata_crossreference = join(directory, metadata_crossreference + '_' + workflow + '.csv')
    else:
        metadata_crossreference = join(directory, metadata_crossreference)
    if not os.path.isfile(metadata_crossreference):
        print('The cross-reference file ', metadata_crossreference, 'was not found')
        quit()

    raw_limits = args.limits  # obtain the limit parameter and determine the type of limit provided
    if raw_limits == 'all':  # default, no limit applied
        sub_limits = []
        group_ids = []
    else:
        limits = raw_limits.split(';')
        try:  # integer limits are subject_id limits
            sub_limits = [max(int(limits[0]), int(limits[1])), min(int(limits[0]), int(limits[1]))]
            group_ids = []
        except ValueError:  # otherwise we have group_id limits
            sub_limits = []
            group_ids = limits

    try:
        width_to_line_ratio = int(args.width_to_line_ratio)
    except ValueError:
        print('The width_to_line_ratio "', args.width_to_line_ratio, '" is not an integer.')
        quit()

    page = args.pagination  # get preferred pagination type

    parsed_file = subject_reducer[:-4] + '_' + raw_limits + '_parsed.csv'
    columns, metadata_x_ref = load_metadata_x_ref(metadata_crossreference)
    print(flatten_class(subject_reducer, parsed_file, sub_limits, group_ids, page))
    print(natsort_double(parsed_file, subject_reducer[:-4] + '_'
                         + raw_limits + '_sorted.csv', 4, 2, False, True))
