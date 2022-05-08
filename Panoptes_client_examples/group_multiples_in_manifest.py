from PIL import Image
import os
import re
import csv
import json
import operator
from datetime import datetime

max_frames = 8
max_seq_len = 24

reg_file_name = re.compile(r'[A-Z]+19[_\d]* ')
# reg_file_name = re.compile(r'\d+_')


def get_files_in(folder):
    file_types = ['jpg', 'jpeg']
    file_listing = []
    for entry in os.listdir(folder):
        for file_type in file_types:
            if entry.lower().find(file_type) > 0:
                if reg_file_name.search(entry):
                    file_listing.append([entry, get_date_time(folder + os.sep + entry), entry.partition(' ')[0]])
                    #  file_listing.append([entry, get_date_time(folder + os.sep + entry), entry.partition('_')[0]])
                else:
                    print('Acquiring exif data for ', folder + os.sep + entry,
                          ' failed - Unexpected filename structure_____________________')
    files_by_time = sorted(file_listing, key=operator.itemgetter(1))
    return sorted(files_by_time, key=operator.itemgetter(2))  # files sorted by camera and time


def get_date_time(image_file):
    try:
        img = Image.open(image_file)
        exif_dict = img._getexif()
        date_time = exif_dict[36868]
    except (IOError, KeyError, TypeError):
        print('Acquiring exif data for ', image_file, ' failed___________________________________________________')
        date_time = '2000:01:01 00:00:00'
    return date_time


def reduce_frames(count, keep):
    step_list = []
    bins = count - keep + 1
    for st in range(1, bins):
        x = int(keep / (bins - st + 1) + .5)
        step_list.append(x)
        keep -= x
    step_list.append(keep)
    full_list = []
    for y in step_list:
        full_list.extend(['1' for _ in range(0, y)])
        full_list.append('0')
    return full_list[:-1]


def split_long_seq(all_seq, max_len):
    rebuild_all_seq = []
    for sq in all_seq:
        tdelta_ = datetime.strptime(sq[0][1],
                                    '%Y:%m:%d %H:%M:%S') - datetime.strptime(sq[-1][1], '%Y:%m:%d %H:%M:%S')
        if tdelta_.seconds < len(sq) / 3 and len(sq) > 3:
            print('Some sequences may have bad exif data', sq[0][0], sq[-1][0])
            quit()
        if len(sq) > max_len:
            make_groups = int(len(sq) / max_len) + 1
            group_count = int(len(sq) / make_groups)
            for mk in range(0, make_groups - 1):
                rebuild_all_seq.append(sq[mk * group_count:(mk + 1) * group_count])
            rebuild_all_seq.append(sq[(make_groups - 1) * group_count:])
        else:
            rebuild_all_seq.append(sq)
    return rebuild_all_seq


while True:
    location = input('Enter the full path for the image directory, or enter "." '
                     'to use the current directory' + '\n')
    if location == '.':
        location = os.getcwd()
        break
    else:
        if os.path.exists(location):
            break
        else:
            print('That entry is not a valid path for an existing directory')
            retry = input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

delay = input('Entry maximum time interval in seconds for images within an event:' + '\n')

file_list = get_files_in(location)
number = len(file_list)
previous_time = file_list[0][1]
all_images = []
sequence = []
file_count = 0
for file in file_list:
    current_time = file[1]
    tdelta = datetime.strptime(current_time,
                               '%Y:%m:%d %H:%M:%S') - datetime.strptime(previous_time, '%Y:%m:%d %H:%M:%S')
    file_count += 1
    if tdelta.seconds <= int(delay):
        sequence.append(file)
    else:
        all_images.append(sequence)
        sequence = [file]
    previous_time = current_time
all_images.append(sequence)
all_images = split_long_seq(all_images, max_seq_len)

print('Found ', file_count, ' files in', len(all_images), ' sequences to upload in this directory.')

with open(location + os.sep + 'manifest.csv', 'w', newline='') as file:
    fieldnames = ['Sequence',
                  'Number in sequence',
                  'File_group',
                  'Number of files',
                  'file_list',
                  'Date_times'
                  ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    total_images = 0
    images_grouped = 0
    for seq_num, seq in enumerate(all_images):
        sequence_len = len(seq)
        new_line = {}
        file_list = []
        keep_list = reduce_frames(sequence_len, max_frames)
        for index, image in enumerate(seq):
            total_images += 1
            if keep_list[index] == '1':
                file_list.append(image[0])
                images_grouped += 1
        new_line['Sequence'] = seq_num + 1
        new_line['Number in sequence'] = sequence_len
        new_line['File_group'] = seq[0][0]
        new_line['Number of files'] = len(file_list)
        new_line['file_list'] = json.dumps(file_list)
        if len(seq) > 1:
            new_line['Date_times'] = seq[0][1] + ' - ' + seq[-1][1]
        else:
            new_line['Date_times'] = seq[0][1]

        print('Saving group', seq_num + 1, 'with', len(file_list), ' files of ',
              sequence_len, 'images in the sequence')
        writer.writerow(new_line)
    print(total_images, 'total images reduced to ', images_grouped,
          'images grouped into', len(all_images), 'subjects, ')
