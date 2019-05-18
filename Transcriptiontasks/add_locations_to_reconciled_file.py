# -*- coding: utf-8 -*-
import argparse
import textwrap
import csv
import sys
import os
from panoptes_client import Subject, Panoptes
Panoptes.connect()
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description=textwrap.dedent("""
            This takes Notes from Nature reconciled file and adds the 
            zooniverse subject url's (locations) as retrieved from zooniverse
            using the panoptes client and the subject-id field of the reconciled
            file.  In its current form it adds only the first image file of a 
            multi-frame subject, and can not be used on audio or video format subjects.
            NOTE: You may use a file to hold the command-line arguments like:
            @/path/to/args.txt."""))

parser.add_argument('--input_file', '-f', required=True,
                    help="""The reconciled file as returned by reconcile.py. 
                    The first field in the file must be identified 'subject_id' """)
args = parser.parse_args()

input_file = args.input_file
if not os.path.exists(input_file):
    print('[%s] does not exist.' % input_file)
    sys.exit()

output_file = input_file.split('.')[0] + '_with_locations' + '.' + input_file.split('.')[1]
with open(input_file, 'r') as in_file:

    in_put = csv.reader(in_file, dialect='excel')
    headers = in_put.__next__()
    headers.append('subject_locations')
    with open(output_file, 'w', newline='') as out_file:
        write_added = csv.writer(out_file, delimiter=',')
        write_added.writerow(headers)
        line_counter = 0
        for line in in_put:
            try:
                subject = Subject(line[0])
                line.append(subject.locations[0]['image/jpeg'])
            except KeyError:
                print(line[0], 'Did not find a subject image file for this subject')
            if line_counter % 25 == 0:
                print('.')
            write_added.writerow(line)
            line_counter += 1
        print('Added subject locations to', input_file, '. Rewritten as', output_file, ',', line_counter, 'subjects located.')
