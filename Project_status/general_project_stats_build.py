# -*- coding: utf-8 -*-

import os
import io
import operator
import sys
import panoptes_client
from panoptes_client import Panoptes, Project

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])

project_listing = []
for project in Project.where(launch_approved=True):
    try:
        project_listing.append([int(project.id), project.subjects_count,
                                project.retired_subjects_count, project.launch_approved,
                                project.state, project.display_name])
    except panoptes_client.panoptes.PanoptesAPIException:
        print(str(sys.exc_info()[1]))
project_listing.sort(key=operator.itemgetter(0))
sorted_on_state = sorted(project_listing, key=operator.itemgetter(4))

with io.open('out_proj_stats_approved.csv', 'w', encoding='utf-8', newline='') as out_file:
    out_file.write('project.id' + ',' + 'subjects_count' + ','
                   + 'retired_subjects_count' + ',' + 'launch_approved' + ',' + 'state' + ',' + 'display_name' + '\n')
    for line in sorted_on_state:
        print(line)
        out_file.write(str(line[0]) + ',' + str(line[1]) + ',' + str(line[2]) + ',' + str(line[3]) + ',' + str(
            line[4]) + ',' + str(line[5]) + '\n')

#  ____________________________________________________________________________________________________________________
