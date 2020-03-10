# -*- coding: utf-8 -*-
# !/usr/bin/env python3

""" increase dynamic eps for tip points from .11 to .15
There are major changes to this script in the Animalus git hub version (all the file definition and naming).
"""

import csv
import json
import os
import sys
import operator
from math import cos, atan, degrees
from statistics import median
import piexif
import dbscan
import cv2 as cv
from matplotlib import pyplot as plt


def show(plot, title):  # just for viewing results while bebugging
    plt.imshow(plot, cmap='gray')
    plt.title(title)
    plt.axis('off')
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()
    plt.close()


# Copies metadata from `src` file to `dst`
def copy_metadata(src, dst):
    # Copy Exif data
    exif_dict = piexif.load(src)
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, dst)


# define a function that returns True or False based on whether the record is to be included
def include(class_record):
    if int(class_record['workflow_id']) == 84:
        pass  # this one selects the workflow to include in the analysis.
    else:
        return False
    if float(class_record['workflow_version']) >= 1.00:
        pass  # this one selects the first version of the workflow to include.
    else:
        return False
    if 40000000 >= int(class_record['subject_ids']) >= 1000:
        pass  # this one can be used to select a range of subjects
    else:
        return False
    # otherwise :
    return True


# pulls and formats the points
def pull_point(drawn_object):
    try:
        x = round(drawn_object['x'], 0)
        y = round(drawn_object['y'], 0)
        drawing = [x, y]
    except TypeError:
        drawing = None
    return drawing


# pulls the box info and converts to a centroid, height, width description
def pull_rectangle(drawn_object):
    try:
        x = round(drawn_object['x'], 1)
        y = round(drawn_object['y'], 1)
        w = round(drawn_object['width'], 0)
        h = round(drawn_object['height'], 0)
        drawing = [x + w / 2, y + h / 2, w, h]
    except TypeError:
        drawing = None
    return drawing


#  ___________________________________________________________________________________________

#  The next section flattens the zooniverse data, pulling out the tip, notch points and the boxes by subject
def flatten_class(out_loc, zoo_file):
    with open(out_loc, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['subject_ids',
                      'filename',
                      'user_name',
                      'workflow_id',
                      'workflow_version',
                      'classification_id',
                      'created_at',
                      'fluke_bounding_boxes',
                      'fluke_tip_points',
                      'fluke_notch_points'
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
                # if i == 1000:
                #     break
                if include(row) is True:
                    j += 1
                    anns = json.loads(row['annotations'])
                    subj = json.loads(row['subject_data'])

                    # recover the subject filename from the subject-data
                    filename = ''
                    for k in subj:
                        if "filename" in subj[k]:
                            filename = subj[k]['filename']
                        elif "Filename" in subj[k]:
                            filename = subj[k]['Filename']
                        else:
                            print("No filename found")
                            print(subj)
                    filename = filename.lower()

                    fluke_bounding_boxes = []
                    fluke_tip_points = []
                    fluke_notch_points = []
                    for ann in anns:
                        try:
                            # pull out boxes
                            if ann['task'] == 'T1':
                                for drawing_object in ann['value']:
                                    if pull_rectangle(drawing_object):
                                        fluke_bounding_boxes.append(pull_rectangle(drawing_object))
                            # pull out tip points
                            if ann['task'] == 'T2':
                                for drawing_object in ann['value']:
                                    if pull_point(drawing_object):
                                        fluke_tip_points.append(pull_point(drawing_object))
                            # pull out notch points
                            if ann['task'] == 'T3':
                                for drawing_object in ann['value']:
                                    if pull_point(drawing_object):
                                        fluke_notch_points.append(pull_point(drawing_object))
                        except KeyError:
                            continue

                    writer.writerow({'subject_ids': row['subject_ids'],
                                     'filename': filename,
                                     'user_name': row['user_name'],
                                     'workflow_id': row['workflow_id'],
                                     'workflow_version': row['workflow_version'],
                                     'classification_id': row['classification_id'],
                                     'created_at': row['created_at'],
                                     'fluke_bounding_boxes': json.dumps(fluke_bounding_boxes),
                                     'fluke_tip_points': json.dumps(fluke_tip_points),
                                     'fluke_notch_points': json.dumps(fluke_notch_points)
                                     })
                if i % 10000 == 0:
                    print('flatten', i, j)
    return str(i) + ' Lines read and ' + str(j) + ' records processed'


#  ___________________________________________________________________________________________


# This section defines a sort function.
def sort_file(input_file, output_file_sorted, field, reverse, clean):
    #  This allows a sort of the output file on a specific field.
    with open(input_file, 'r', encoding='utf-8') as in_file:
        in_put = csv.reader(in_file, dialect='excel')
        headers = in_put.__next__()
        sort = sorted(in_put, key=operator.itemgetter(field), reverse=reverse)
        with open(output_file_sorted, 'w', newline='', encoding='utf-8') as out_file:
            write_sorted = csv.writer(out_file, delimiter=',')
            write_sorted.writerow(headers)
            sort_counter = 0
            for row in sort:
                write_sorted.writerow(row)
                sort_counter += 1
    if clean:  # clean up temporary file
        try:
            os.remove(input_file)
        except OSError:
            print('temp file not found or not deleted')
    return str(sort_counter) + ' lines sorted and written'


#  ___________________________________________________________________________________________


# this function selects boxes that have exactly two tip points in them, and no extraneous points
def fluke_pos(subj, sorted_tips, sorted_boxes):
    margin = 20
    box_points = []
    nomatch = sorted_tips[:]
    for _ in range(0, len(sorted_boxes)):
        box_points.append([])
    for idx in range(0, len(sorted_boxes)):
        box_points[idx] = sorted_boxes[idx][1][:]

        for (number, point) in sorted_tips:
            # noinspection PyChainedComparisons
            if point[0] > box_points[idx][0] - box_points[idx][2] / 2 - margin and \
                    point[1] > box_points[idx][1] - box_points[idx][3] / 2 - margin and \
                    point[0] < box_points[idx][0] + box_points[idx][2] / 2 + margin and \
                    point[1] < box_points[idx][1] + box_points[idx][3] / 2 + margin:
                box_points[idx].append(point)
                try:
                    nomatch.remove((number, point))
                except ValueError:
                    continue

    # Deal with the "normal" cases first - boxes with exactly two enclosed tip points and no nomatch points
    flukes = []
    for box in box_points:
        if len(box) == 6 and len(nomatch) == 0:
            # print("\t normal situation one box, two enclosed tips.")
            flukes.append(box)
    if len(flukes) > 0:
        return flukes
    elif len(box_points) == 0:
        return []
    else:
        return 'Some weird situation ' + str(subj)


# The actual resolution of the aggregated tip point and boxes into fully defined fluke positions - uses a
# homegrown dbscan to cluster the points and box centroids using an eps and min_points based on the data.
def process_aggregation(subj, filename, clas, boxes, tips, notches):
    # scale a suitable eps for clustering the boxes from the median box width
    w = []
    for idn in range(0, len(boxes)):
        w.append(boxes[idn][2])
    if len(w) > 0:
        typ_width = median(w)
    else:
        typ_width = 60

    # scale a suitable min_points from the number of classifications
    min_point = max(int(clas * .405), 2)

    # cluster the boxes centroids
    epb = max(typ_width * .20, 20)
    scanb = dbscan.DBSCAN(epb, min_point)
    scanb.cluster(boxes)
    sorted_boxes = sorted(scanb.points, key=operator.itemgetter(0), reverse=True)
    bc_p = json.dumps(sorted_boxes)
    bclusters = json.dumps(scanb.clusters)

    # cluster the tip and notch points
    ept = max(typ_width * .15, 20)
    scant = dbscan.DBSCAN(ept, min_point)
    scant.cluster(tips)
    sorted_tips = sorted(scant.points, key=operator.itemgetter(1))
    tc_p = json.dumps(sorted_tips)
    tclusters = json.dumps(scant.clusters)
    scann = dbscan.DBSCAN(ept, min_point)
    scann.cluster(notches)
    nc_p = json.dumps(scann.points)
    nclusters = json.dumps(scann.clusters)

    # clean up the clusters to settle on boxes with exactly two enclosed tip points
    fluke_positions = fluke_pos(subj, sorted_tips, sorted_boxes)

    # prepare a row for write the resolved fluke boxes and points to file
    new_row = {'subject_ids': subj,
               'filename': filename,
               'classifications': clas,
               'boxes': json.dumps(boxes),
               'box_clusters': bc_p,
               'bclusters': bclusters,
               'tips': json.dumps(tips),
               'tip_clusters': tc_p,
               'tclusters': tclusters,
               'notches': json.dumps(notches),
               'notch_clusters': nc_p,
               'nclusters': nclusters,
               'flukes': json.dumps(fluke_positions)
               }
    return new_row


# a simple aggregation routine that collects all the tip points and boxes for a subject and passes them to be
# clustered, tested and output to the final output file for the resolved fluke positions.
def aggregate(sorted_loc, aggregated_loc):
    with open(aggregated_loc, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['subject_ids', 'filename', 'classifications',
                      'boxes', 'box_clusters', 'bclusters',
                      'tips', 'tip_clusters', 'tclusters',
                      'notches', 'notch_clusters', 'nclusters', 'flukes'
                      ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # set up to read the flattened file
        with open(sorted_loc, 'r', encoding='utf-8') as f:
            r = csv.DictReader(f)
            # initialize a starting point subject and empty bins for aggregation
            subject = ''
            users = ''
            filename = ''
            i = 1
            j = 0
            boxes = []
            tips = []
            notches = []

            # Loop over the flattened classification records
            for row in r:
                j += 1
                if j % 10000 == 0:
                    print('aggregating', j)
                # read a row and pullout the flattened data fields we need to aggregate, or output.
                new_subject = row['subject_ids']
                new_filename = row['filename']
                new_user = row['user_name']
                row_boxes = json.loads(row['fluke_bounding_boxes'])
                row_tips = json.loads(row['fluke_tip_points'])
                row_notches = json.loads(row['fluke_notch_points'])

                # test for change in selector - output on change
                if new_subject != subject:
                    if i != 1:  # if not the first line analyse the aggregated fields and output the results
                        new_row = process_aggregation(subject, filename, i, boxes, tips, notches)
                        writer.writerow(new_row)

                    # reset the selector, those things we need to output and the bins for the aggregation.
                    i = 1
                    subject = new_subject
                    filename = new_filename
                    users = {new_user}
                    boxes = row_boxes
                    tips = row_tips
                    notches = row_notches

                else:
                    # do the aggregation - clean for excess classifications and multiple classifications by the same
                    # user on this subject
                    if users != users | {new_user}:
                        users |= {new_user}
                        boxes.extend(row_boxes)
                        tips.extend(row_tips)
                        notches.extend(row_notches)
                        i += 1

            # catch and process the last aggregated group
        new_row = process_aggregation(subject, filename, i, boxes, tips, notches)
        writer.writerow(new_row)


# _____________________________________________________________________________________________


# Acquire image filenames from given directory.
def get_filenames(fluke_img_dir):
    # We store both a list of all cleaned filenames,
    # and a mapping of those clean filenames back to the original names.
    image_filenames = []
    image_filename_map = {}
    for dirname, dirnames, filenames in os.walk(fluke_img_dir + os.sep):
        for filename in filenames:
            image_filenames.append(filename.lower())
            image_filename_map[filename.lower()] = filename

    print("Found " + str(len(image_filenames)) + " fluke images.")
    return image_filenames, image_filename_map


# _____________________________________________________________________________________________

# calculates the crop region from the fluke positions in the aggregated file. Note this could be incorporated
# into the final aggregated output file, and calculated once rather than each time a set of images are cropped.
def crop_region(box):
    radians = atan((box[5][1] - box[4][1]) / (box[5][0] - box[4][0]))
    rot_width = box[2] / cos(radians)
    offset = 250 / 550 * rot_width / image_ratio

    # force box ratio to image_ratio with a fixed vertical offset to the centroid defined above
    top = box[1] - offset
    left = box[0] - rot_width / 2
    bottom = box[1] + rot_width / image_ratio - offset
    right = box[0] + rot_width / 2

    # translate box if there are negative coordinates
    if top < 0:
        bottom -= top
        top = 0
    if left < 0:
        right -= left
        left = 0

    return {
        'radians': radians,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right
    }


# _____________________________________________________________________________________________


# The main script. The analysis on the zooniverse data is done once and stored as aggregated_location.
# It need not be repeated until further subject sets are completed in WAI. The existing data can be used
# to test and crop any of the various subject sets previously fed into SAS.
if __name__ == '__main__':

    # Script settings and file locations: These have to be modified to locations specific to the user's directorys
    zooniverse_file = r'C:\py\Whales\whales-as-individuals-classifications.csv'

    # the output files can be named and placed anywhere
    out_location = r'C:\py\Whales\WAI_flatten_data.csv'
    sorted_location = r'C:\py\Whales\WAI_flatten_data_sorted.csv'
    aggregated_location = r'C:\py\Whales\WAI_aggregate_data.csv'

    while True:
        fluke_images_dir = input('Enter the full path for the image directory to test and crop, or enter "." '
                                 'to use the current directory' + '\n')
        if fluke_images_dir == '.':
            fluke_images_dir = os.getcwd()
            break
        else:
            if os.path.exists(fluke_images_dir):
                break
            else:
                print('That entry is not a valid path for an existing directory')
                retry = input('Enter "y" to try again, any other key to exit' + '\n')
                if retry.lower() != 'y':
                    quit()
    cropped_image_dir = fluke_images_dir + r'\cropped_ images'
    # if subdirectory does not exist make it
    if not os.path.exists(cropped_image_dir):
        os.mkdir(cropped_image_dir)

    image_ratio = 7 / 4

    # Test for an existing aggregated_location output file and if present ask if the file is to be used or rebuilt.
    if os.path.isfile(aggregated_location):
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(aggregated_location)
        print('Found a aggregated out put file of fluke position created', ctime)
        while True:
            rebuild = input('Do you want to use this file (y) or rebuild it? (r)' + '\n')
            if rebuild.lower() == 'r':
                flatten_class(out_location, zooniverse_file)
                sort_file(out_location, sorted_location, 0, False, True)
                aggregate(sorted_location, aggregated_location)
                break
            elif rebuild.lower() == 'y':
                break
            else:
                print('That entry is not a valid response (y or r)')
                retry = input('Enter "y" to try again, any other key to exit' + '\n')
                if retry.lower() != 'y':
                    quit()
    else:
        flatten_class(out_location, zooniverse_file)
        sort_file(out_location, sorted_location, 0, False, True)
        aggregate(sorted_location, aggregated_location)

    # crawl the image directory and acquire the filenames
    imageFilenames, imageFilenameMap = get_filenames(fluke_images_dir)

    # load the aggregated WAI data and proceed to loop over the valid flukes. Load the matching image if any and
    # rotate and crop the image and save the cropped image.
    with open(aggregated_location, 'r', encoding='utf-8') as ag_file:
        images_not_processed = []
        r_ag = csv.DictReader(ag_file)
        for line in r_ag:
            fluke_positons = json.loads(line['flukes'])
            image = line['filename']
            if image not in imageFilenames:
                continue
            else:
                # a match has been found with one of the current images being analysed.
                realFilename = imageFilenameMap[image]
                # Read the image
                imageData = cv.imread(fluke_images_dir + os.sep + realFilename)
                width, height = imageData.shape[1], imageData.shape[0]
                counter = 0
                if len(fluke_positons) < 5:  # the invalid "something weird" fluke positions fail this test
                    for bx in fluke_positons:
                        counter += 1
                        for ind in range(0, 4):
                            bx[ind] = width / 960 * bx[ind]
                        cropRegion = crop_region(bx)
                        file_name = cropped_image_dir + os.sep + image[:-4] + "-cr" + str(counter) + ".jpg"
                        # Rotate and crop image
                        try:
                            warp_matrix = cv.getRotationMatrix2D((bx[0], bx[1]),
                                                                 degrees(cropRegion['radians']), 1)
                            rotated = cv.warpAffine(imageData, warp_matrix, (width, height), flags=cv.INTER_LINEAR)

                            cropped = rotated[int(cropRegion['top']): int(cropRegion['bottom']),
                                              int(cropRegion['left']): int(cropRegion['right'])]

                            # show(cropped[:, :, ::-1], 'cropped')
                            cv.imwrite(file_name, cropped)
                            copy_metadata(fluke_images_dir + os.sep + realFilename, file_name)
                            print(image, ' processed')
                        except sys.exc_info()[0]:
                            e = sys.exc_info()[0]
                            print("Encountered exception processing file " + file_name + ":")
                            print(str(e))
                            images_not_processed.append([line['subject_ids'], image])
                else:
                    print(str(image) + ' aggregated data was not usable')
                    images_not_processed.append([line['subject_ids'], image])
# _____________________________________________________________________________________________
