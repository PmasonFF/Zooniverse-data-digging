import argparse
import textwrap
import json
import os
import csv
from os.path import join


def create_metadata_x_ref(input_filename, workflow_id_, output_filename):
    # Open the input file and set up for reading
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader_ = csv.DictReader(infile)
        # add in any other metadata fields your subjects may have:
        fieldnames = ["subject_id", "group_id", "internal_id"]

        with open(output_filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer_ = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer_.writeheader()

            # Iterate through each row in the input file
            for row in reader_:
                if row["workflow_id"] == workflow_id_:
                    metadata_ = (json.loads(row["metadata"]))
                    # Extract "subject_id", "group_id", and "internal_id"
                    try:
                        output_row = {"subject_id": row["subject_id"],
                                      "group_id": metadata_["group_id"],
                                      "internal_id": metadata_["internal_id"]
                                      }  # add in any other metadata fields your subjects may have
                        
                        # try:  # add code snippets like these lines to recover other metadata fields for your subjects
                        #     output_row["File Name"] = metadata_["File Name"]
                        # except KeyError:
                        #     output_row["File Name"] = ''

                    except KeyError:
                        print(row["subject_id"], 'missing internal_id or group_id')
                        continue
                    # Write to output file
                    writer_.writerow(output_row)


# get subject_export.csv path and file name from arguments:
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""  
        The first step is to define the input file and path for the 
        subject_export using parameters.  This is done by giving 
        the script two parameters, 1) a working directory path where the 
        subject export used to build the x_ref, and the output file will 
        reside, and 2) the id of the workflow the x-ref will include. 
        """))

parser.add_argument(
    '-d', '--directory', default='.',
    help=textwrap.dedent("""The path and directory where the input and output
    files, are located. It defaults to the directory where this script is 
    running. example '-d C:\py\Project' """))

parser.add_argument(
    '-s', '--subject_export',
    help=textwrap.dedent("""The project subject_export.csv file 
    which is used to generate a cross-reference between the zooniverse subject
    id and the subject metadata. It must be in the working directory and is the 
    normal subject export file downloaded via the project builder.  
    example: "-s project-name-subjects.csv" """))

parser.add_argument(
    '-w', '--workflow',
    help=textwrap.dedent("""The transcription based workflow_id that is to be parsed.
    example: "-w 12345"""))

args = parser.parse_args()
directory = args.directory
if directory == '.':
    directory = os.getcwd()
if not os.path.exists(directory):
    print('The directory parameter -d', directory, 'is not a valid path')
    quit()

workflow = str(args.workflow)

subject_export = join(directory, args.subject_export)
if not os.path.isfile(subject_export):
    print('The project subject_export file, parameter -s', args.subject_export, 'was not found')
    quit()
create_metadata_x_ref(subject_export, workflow, join(directory,
                                                     "metadata_crossreference_" + workflow + ".csv"))