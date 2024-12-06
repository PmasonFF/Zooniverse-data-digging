import argparse
import textwrap
import csv
import re
import os
import sys
import pandas as pd
from os.path import join

# version = 0.  # parse_alice_exports_with BOM.py version 0.2 with added sort function

reg_0 = re.compile(r'\d\d\d\d[A-Z][0-9]+')
reg_2 = re.compile(r'[.\d]*[_\- ]*[a-z]')


# extract text from a 'transcription_line_metadata_XXXXXXX.csv' file found
# in a subdirectory (folder) named  'transcription_XXXXXXX' based on the value
# of the transcription id 'XXXXXXX'.
def extract_text(directory_, transcription_id_):
    # find and verify subdirectory
    transcription_folder = join(directory_, 'transcription_' + str(transcription_id_))
    if not os.path.exists(transcription_folder):
        print('No transcription folder found for '
              'transcription_id', transcription_id_, 'and object number', metadata[transcription_id_])
        return ''
    else:
        # find and verify transcription_line_metadata file
        transcription_line_file = join(transcription_folder,
                                       'transcription_line_metadata_' + str(transcription_id_) + '.csv')
        if not os.path.isfile(transcription_line_file):
            print('No transcription_line_metadata file found for '
                  'transcription_id', transcription_id_, 'and object number', metadata[transcription_id_])
            return ''
    # open and read text in the transcription_line_metadata file
    with open(transcription_line_file, 'r', encoding='utf-8') as text_line_file:
        line_reader = csv.DictReader(text_line_file)
        text = ''
        for row1 in line_reader:
            text += (row1['consensus text'] + '\n')
        return text.strip('\n')


def sort_index(object_number):
    # print('0', reg_0.search(object_number))
    if reg_0.search(object_number):  # test for year + single Letter + numbers
        object_number = object_number[5:]
        letter_number = ''
    else:
        return 0.0  # force to top of sorted file
    if reg_2.search(object_number):  # test for trailing letter and convert to ordinal
        # print('2', reg_2.search(object_number))
        letter_number = ('0' + str(ord(object_number[-1])))[-3:]
        object_number = object_number.replace('_', '').replace('-', '').replace(' ', '')[:-1]

    split = object_number.split('.')  # list base number and extensions
    # print(split)
    object_number = split[0] + '.'  # start with base number
    if len(split) > 1:  # first extension if any padded to five digits
        object_number += ('00000' + split[1])[-5:]
    if len(split) > 2:  # second and subsequent extensions padded to three digits
        for string in split[2:]:
            object_number += ('000' + string)[-3:]
    # print(object_number + letter_number)
    try:
        return float(object_number + letter_number)
    except (TypeError, ValueError):  # if padded object number can not be converted to a float
        return 0.0


# get transcriptions_metadata.csv path and file name from arguments:
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""  
        The first step is to define the input file and path for the 
        transcriptions_metadata using parameters.  This is done by giving 
        the script two parameters, one a working directory path where the 
        transcriptions_metadata, the individual transcription directories 
        by subject, and the output file will reside, and two, the name of 
        the transcriptions_metadata.csv file if it is not the default. 
        """))

parser.add_argument(
    '-d', '--directory', default='.',
    help=textwrap.dedent("""The path and directory where the input and output
    files, are located. It defaults to the directory where this script is 
    running. example '-d C:\py\BMT_collections' """))

parser.add_argument(
    '-f', '--file', default='transcriptions_metadata.csv',
    help=textwrap.dedent("""The transcriptions_metadata.csv file to parse. 
    It must be in the working directory and contain a column 'transcription id'
    which is the zooniverse subject number, and a column 'internal id' which is
    the BMT Collection's object number. The output file will have the same name 
    as the transcriptions_metadata input file with "_parsed" added prior to the 
    file extension.   example: "-f transcriptions_metadata.csv" """))

args = parser.parse_args()
directory = args.directory
if directory == '.':
    directory = os.getcwd()
if not os.path.exists(directory):
    print('The directory parameter -d', directory, 'is not a valid path')
    quit()
transcription_metadata = join(directory, args.file)
if not os.path.isfile(transcription_metadata):
    print('The file parameter -f', args.file, 'was not found')
    quit()

# open and read transcriptions_metadata.csv
with open(transcription_metadata, 'r', encoding='utf-8') as metadata_file:
    metadata_reader = csv.DictReader(metadata_file)
    metadata = {}
    for row in metadata_reader:
        metadata[row['transcription id']] = row['internal id']

# open the output file
unsorted_output_file = transcription_metadata[:-4] + '_parsed.csv'
with open(unsorted_output_file, 'w', newline='', encoding='utf-8-sig') as out_file:
    fieldnames = ['transcription_id', 'internal_id', 'consensus_text']
    writer = csv.DictWriter(out_file, fieldnames=fieldnames)
    writer.writeheader()
    # loop through the transcription_metadata and output data
    for transcription_id in metadata:
        print(transcription_id)
        new_line = {
            'transcription_id': transcription_id,
            'internal_id': metadata[transcription_id],
            'consensus_text': extract_text(directory, transcription_id)
        }
        writer.writerow(new_line)

sorted_output_file = transcription_metadata[:-4] + '_parsed' + '_sorted.csv'
print(sorted_output_file)

df = pd.read_csv(unsorted_output_file, encoding='utf-8-sig')
columns = list(df)

try:  # generate sort index from ColObjectNumber
    df['sort_index'] = df['internal_id'].map(sort_index)
    df['Base_object_number'] = df['sort_index'].map(lambda x: int(x))
    columns.append('Base_object_number')
except:
    print('Error generating sort index')
    print(str(sys.exc_info()[1]))
    quit()
else:
    try:  # output sorted data frame
        df.sort_values(by=['sort_index']).to_csv(sorted_output_file, sep=',', columns=columns, index=False,
                                                 encoding='utf-8-sig')
    except:
        print('Error outputing sorted dataframe')
        print(str(sys.exc_info()[1]))
        quit()