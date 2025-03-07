import argparse
import textwrap
import csv
import os
from os.path import join

"""
Version = 0.2.1
0.2.1 - raw docstring to remove syntax warning re '/p' line 58
0.2.0 - save file with BOM character (encoding='uft-8-sig')
0.1.0 - added encoding= 'utf-8' for open "transcription_line_file"
"""

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


# get transcriptions_metadata.csv path and file name from arguments:
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""  
        The first step is to define the input file and path for the 
        transcriptions_metadata using parameters.  This is done by giving 
        the script two parameters, 1) a working directory path where the 
        transcriptions_metadata, the individual transcription directories 
        by subject, and the output file will reside, and 2) the name of 
        the transcriptions_metadata.csv file if it is not the default. 
        """))

parser.add_argument(
    '-d', '--directory', default='.',
    help=textwrap.dedent(r"""The path and directory where the input and output
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
output_file = transcription_metadata[:-4] + '_parsed.csv'
with open(output_file, 'w', newline='', encoding='utf-8-sig') as out_file:
    # encoding='utf-8-sig' is so Microsoft Excel will open the file with utf-8 encoding automatically, depending
    # on the spreadsheet you use to view files this encoding may need to be changed to uft-8.
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

