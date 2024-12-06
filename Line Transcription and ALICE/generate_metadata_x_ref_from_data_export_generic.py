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
        fieldnames = ["subject_id", "group_id", "internal_id", 'image_width']  # add other metadata fields as needed

        with open(output_filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer_ = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer_.writeheader()
            previous_subjects = []
            # Iterate through each row in the input file
            i = 0
            j = 0
            for row in reader_:
                i += 1
                if row["subject_ids"] not in previous_subjects and row["workflow_id"] == workflow_id_:
                    j += 1
                    previous_subjects.append(row["subject_ids"])
                    subject_data = json.loads(row["subject_data"])
                    subject_metadata_ = subject_data[row["subject_ids"]]
                    subject_dimensions = json.loads(row["metadata"])['subject_dimensions'][0]
                    # Extract "subject_id", "group_id", "internal_id" and image_width
                    try:
                        output_row = {"subject_id": row["subject_ids"],
                                      "group_id": subject_metadata_["group_id"],
                                      "internal_id": subject_metadata_["internal_id"],
                                      'image_width': subject_dimensions['naturalWidth']
                                      }

                        # try:  # add other metadata fields for your project here as needed:
                        #     output_row["File Name"] = subject_metadata_["File Name"]
                        # except KeyError:
                        #     output_row["File Name"] = ''

                    except KeyError:
                        print(row["subject_id"], 'missing internal_id or group_id')
                        continue
                    # Write to output file
                    writer_.writerow(output_row)
                if i % 25000 == 0:
                    print(i, j)
            print(i, j)


# get data_export.csv path and file name from arguments:
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""  
        The first step is to define the input file and path for the 
        data_export using parameters.  This is done by giving 
        the script two parameters, one a working directory path where the 
        subject export used to build the x_ref, and the output file will 
        reside, and two, the id of the workflow the x-ref will include. 
        """))

parser.add_argument(
    '-d', '--directory', default='.',
    help=textwrap.dedent("""The path and directory where the input and output
    files, are located. It defaults to the directory where this script is 
    running. example '-d C:\py\BMT_collections' """))

parser.add_argument(
    '-s', '--data_export',
    help=textwrap.dedent("""The project data export.csv file which is used
    to generate a cross-reference between the zooniverse subject id and the 
    subject metadata. It must be in the working directory and is either the full 
    data export or classifications by workflow downloaded via the project builder.  
    example: "-s transcribing-birmingham-museums-accession-registers-classifications.csv" """))

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

workflow = str(args.workflow)

data_export = join(directory, args.data_export)
if not os.path.isfile(data_export):
    print('The project data_export file, parameter -s', args.data_export, 'was not found')
    quit()
create_metadata_x_ref(data_export, workflow, join(directory,
                                                  "metadata_crossreference_" + workflow + ".csv"))
