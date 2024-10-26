import argparse
import textwrap
import json
import operator
import os
import csv
from natsort import natsorted
from os.path import join
from panoptes_client import Subject, Panoptes

# version = 0.


def load_metadata_x_ref(input_filename):
    # Open the input file and set up for reading
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader_ = csv.DictReader(infile)
        metadata_x_ref_ = {}
        # Iterate through each row in the input file
        for row in reader_:
            # Extract metadata
            try:
                # add in any other metadata fields your subjects may have
                metadata_x_ref_[row["subject_id"]] = {"group_id": row["group_id"],
                                                      "internal_id": row["internal_id"]
                                                      }
            except KeyError:
                print(row["subject_id"], 'missing metadata fields')
                continue
        return metadata_x_ref_


# get path and file names from arguments:
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""  
        The first step is to define the input file and path for the 
        subject reducer export from caesar using parameters.  This is 
        done by giving the script two parameters, 1) a working directory
        path and 2) the file name of the reducer export. The output file 
        will also be placed in the working directory. Then 3) a cross-reference
        file and 4) workflow_id need to be defined. 
        """))

parser.add_argument(
    '-d', '--directory', default='.',
    help=textwrap.dedent("""The path and directory where the input and output
    files, are located. It defaults to the directory where this script is 
    running. example '-d C:\py\BMT_collections' """))

parser.add_argument(
    '-f', '--file',
    help=textwrap.dedent("""The subject_reducer_export.csv file to parse. 
    It is the caesar subject reducer export file for the Transcription workflow
    to be parsed,  It must be in the working directory and contain a column 
    'subject_id' which is the zooniverse subject number, a column 'reducer_key' 
    some of which are of type "alice", and a column "data.frame0" which contains
    the consensus text for the subject. The output file will have the same name 
    as the subject_reducer_export file with "_parsed" added prior to the 
    file extension.   example: "-f Subject_reducer_export_workflow_date.csv" """))

parser.add_argument(
    '-m', '--metadata',
    help=textwrap.dedent("""The cross-reference file is the link between the 
    zooniverse subject id and the subject metadata. This is a csv file is stored
    locally in the working directory.  As a minimum, it must have columns for the 
    zooniverse "subject_id", and the metadata fields "internal_id" and "group_id". 
    Other metadata is optional. This file may be limited to subjects linked to the 
    specific workflow being parsed.  These cross-reference files can be created 
    from a project subject export for a given workflow using the script 
    "generate_metadata_x_ref_by_workflow.py" 
    example: "-m metadata_crossreference_workflow.csv" """))

parser.add_argument(
    '-w', '--workflow',
    help=textwrap.dedent("""The transcription based workflow_id that is to be parsed.
    example: "-w 25224"""))

args = parser.parse_args()
directory = args.directory
if directory == '.':
    directory = os.getcwd()
if not os.path.exists(directory):
    print('The directory parameter -d', directory, 'is not a valid path')
    quit()

subject_reducer_export = join(directory, args.file)
if not os.path.isfile(subject_reducer_export):
    print('The subject_reducer_export file parameter -f', args.file, 'was not found')
    quit()

workflow = str(args.workflow)

metadata_crossreference = join(directory, args.metadata)
if not os.path.isfile(metadata_crossreference):
    print('The specified metadata_crossreference file, parameter -m', args.metadata, 'was not found')
    quit()
metadata_x_ref = load_metadata_x_ref(metadata_crossreference)

Panoptes.connect()  # used as last ditch effort to get subject metadata

# Set up and open output file
out_put_fieldnames = ["subject_id", "year", "group_id", "internal_id", "consensus_text"]
# add in any other metadata fields your subjects may have that are extracted in the x_reference file

with open(subject_reducer_export[:-4] + '_parsed.csv', mode='w', newline='', encoding='utf-8-sig') as parsedfile:
    # encoding='utf-8-sig' is so Microsoft Excel will openthe file with utf-8 encoding automatically, depending
    # on the spreadsheet you use to view files this encoding may need to be changed to uft-8.
    writer = csv.DictWriter(parsedfile, fieldnames=out_put_fieldnames)
    writer.writeheader()

    with open(subject_reducer_export, mode='r', encoding='utf-8') as reducerfile:
        reader = csv.DictReader(reducerfile)

        for line in reader:
            if line['reducer_key'] == 'alice':
                subject_id = str(line['subject_id'])
                if 1200000000 > int(subject_id) > 10000000:  # conditional statements can be used to limit the output
                    if line['data.frame0']:
                        data_frame_text = json.loads(line['data.frame0'])
                    else:
                        print(subject_id, 'No dataframe0 content')
                        continue
                    # print('Acquiring text for subject', subject_id)
                    text = ''
                    for text_line in data_frame_text:
                        text += text_line['consensus_text'] + '\n'
                    text.strip('\n')
                    internal_id = metadata_x_ref[subject_id]["internal_id"]
                    try:
                        new_line = {"subject_id": subject_id,
                                    "year": metadata_x_ref[subject_id]["year"],
                                    "group_id": metadata_x_ref[subject_id]["group_id"],
                                    "consensus_text": text
                                    }  # add in any other metadata fields your subjects may have that
                        # are extracted in the x_reference file
                    except KeyError:
                        subject = Subject(int(subject_id))  # uses panoptes_client to try to get metadata if
                        # subject is not in the x_reference.
                        try:
                            new_line = {"subject_id": subject_id,
                                        "consensus_text": text,
                                        "group_id": subject.metadata["group_id"],
                                        "internal_id": subject.metadata["internal_id"]
                                        }
                        except KeyError:
                            print('No group_id or internal_id metadata available for subject', subject_id)
                            continue

                        # try:  # add code snippets like these lines to recover other metadata fields for your subjects
                        #     new_line["File Name"] = subject.metadata["File Name"]
                        # except KeyError:
                        #     new_line["File Name"] = ''

                    writer.writerow(new_line)

sorted_output_file = subject_reducer_export[:-4] + 'parsed_and_sorted.csv'


# This section defines a sort function. Note the sort fields are numbered starting from '0' and may differ based on
# the metadata columns in the x-reference.

def sort_file(input_file, output_file_sorted, field_1, field_2, reverse, clean):
    #  This allows a sort of the output file on a specific field.
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


print(sort_file(subject_reducer_export[:-4] + '_parsed.csv', sorted_output_file, 2, 1, False, False))
