# -*- coding: utf-8 -*-
"""
    Requires panoptes-client and (on Python 2) futures.
    pip install panoptes-client futures
"""
import argparse
import textwrap
import csv
import os
import io
import sys
import panoptes_client
from panoptes_client import Panoptes, Project, Workflow, Organization


def output(location, build):
    with io.open(location, 'w', encoding='utf-8', newline='') as out_file:
        out_file.write(build)
    return


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    fromfile_prefix_chars='@',
    description=textwrap.dedent("""
            This script produces a listing of the workflow details for projects 
            and workflows in a specified organization. 
            It requires the panoptes_client to be installed, and if run with 
            Python 2.7, it also requires the package futures as well.             
            It can optionally accept a list of either workflows or projects to 
            restrict the listing that is produced to the projects or workflows 
            requested.
            If both a workflow list AND a project list is provided, only the 
            workflow list is used, and all workflows listed will be shown regardless
            of which project they are in.
            If accepts an optional path and filename for a location to save the 
            output in a csv file format. 
            It assumes the user's zooniverse users_name and password are set up
            in the operating system's environmental variables.  If this is not the
            case, replace line 86 with Panoptes.connect(username= '', password='')
            with your credentials hard coded in that line. (Login is actually only
            required if any of the projects queried are Private) 
            NOTE: You may use a file to hold the command-line arguments like:
            @/path/to/args.txt."""))

parser.add_argument('--ORG_ID', '-o', required=False, default=16,
                    help="""The organization to be queried, by organization.id. 
                    An integer, with the default as 16 (for Notes From Nature).
                    example -o 16 """)
parser.add_argument('--workflows_list', '-w', required=False, default='None',
                    help="""An optional list of workflows to include. The .csv
                    file must have a column headed 'workflows' with each record
                    a workflow.id in the organization. Give the full path (from
                    the directory where this script is run, or from the root
                    directory) and the file name. 
                    example -w some_path\workflows_list.csv """)
parser.add_argument('--projects_list', '-p', required=False, default='None',
                    help="""An optional list of projects to include.  The .csv
                    file must have a column headed 'projects' with each record
                    a project.id in the organization.  Give the full path (from the directory 
                    where this script is run, or from the root directory) and 
                    the file name.  
                    example -p some_path\projects_list.csv """)
parser.add_argument('--save_to', '-s', required=False, default='None',
                    help="""An optional file name (including extension ".csv"
                    where the output will be saved in csv format. Give the full
                    path (from the directory where this script is run, or from the
                    root directory) and the file name. 
                    example -s some_path\output_file.csv """)
args = parser.parse_args()

ORG_ID = args.ORG_ID
project_file = args.projects_list
workflow_file = args.workflows_list
save_to = args.save_to

save = False
if '.csv' in save_to:
    save = True

build_file = ''
build_part = "Detailed Workflow Information for:" + '\n'
build_part += "Organization = {}, Workflows list = {}, Projects list = {}, Save location = {}" \
                  .format(ORG_ID, workflow_file, project_file, save_to) + '\n' + '\n'

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
all_projects = Organization(ORG_ID).links.projects
all_workflows = []
for project in all_projects:
    try:
        for workflow in project.links.workflows:
            all_workflows.append([workflow.id, project.id])
    except panoptes_client.panoptes.PanoptesAPIException:
        build_part += str(sys.exc_info()[1]) + ". You may not have permission to view that project" + '\n' + '\n'
# ____________________________________________________________________________________________________________________

workflow_list = []
if workflow_file != 'None':
    if not os.path.isfile(workflow_file):
        print('[%s] does not exist.' % workflow_file)
        sys.exit()
    build_part += "From workflow list:" + '\n' + '\n'
    print(build_part)
    if save:
        build_file += build_part
    build_part = "{:<12},{:<14},{:<28},{:<28},{:<10},{}".format('Project_id', 'Workflow_id', 'Created date',
                                                                'Finished date', 'Finished date', 'Subjects',
                                                                'Workflow name') + '\n'
    with open(workflow_file, 'r') as w_file:
        r = csv.DictReader(w_file)
        workflow_list = []
        for row in r:
            workflow_list.append(row['workflows'])
    not_found = workflow_list[:]
    sys.stdout.write('processing..')
    sys.stdout.flush()
    i = 0
    for workflow_id, project_id in all_workflows:
        i += 1
        if i % 5 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        if workflow_id in workflow_list:
            not_found.remove(workflow_id)
            wrkflw = Workflow(int(workflow_id))
            finished_at = wrkflw.finished_at
            if finished_at is None:
                finished_at = ' '
            build_part += u"{:<12},{:<14},{:<28},{:<28},{:<10},{}".format(project_id, wrkflw.id,
                                                                          wrkflw.created_at, finished_at,
                                                                          wrkflw.subjects_count,
                                                                          wrkflw.display_name) + '\n'
    print('\n')
    for item in not_found:
        build_part += "Workflow not found in specified organization: {}".format(item) + '\n'
    print(build_part)
    if save:
        output(save_to, build_file + build_part)
    quit()
# ____________________________________________________________________________________________________________________

project_list = []
if project_file != 'None':
    if not os.path.isfile(project_file):
        print('[%s] does not exist.' % project_file)
        sys.exit()
    build_part += 'From project list:' + '\n' + '\n'
    print(build_part)
    if save:
        build_file += build_part

    with open(project_file, 'r') as p_file:
        r = csv.DictReader(p_file)
        project_list = []
        for row in r:
            project_list.append(row['projects'])

    i = 0
    for prjct in project_list:
        sys.stdout.write('processing..')
        sys.stdout.flush()
        try:
            build_part = "{:<8},{}".format(prjct, Project(int(prjct)).display_name) + '\n'
            build_part += "{:<12},{:<14},{:<28},{:<28},{:<10},{}".format('Project_id', 'Workflow_id',
                                                                         'Created date',
                                                                         'Finished date', 'Subjects',
                                                                         'Workflow name') + '\n'
            for workflow_id, project_id in all_workflows:
                i += 1
                if i % 5 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                if prjct == project_id:
                    wrkflw = Workflow(int(workflow_id))
                    finished_at = wrkflw.finished_at
                    if finished_at is None:
                        finished_at = ' '
                    build_part += u"{:<12},{:<14},{:<28},{:<28},{:<10},{}".format(prjct, wrkflw.id, wrkflw.created_at,
                                                                                  finished_at, wrkflw.subjects_count,
                                                                                  wrkflw.display_name) + '\n'
        except panoptes_client.panoptes.PanoptesAPIException:
            build_part = "{:<8} Project not found in specified organization".format(prjct) + '\n'
        print('\n')
        build_part += '\n'
        print(build_part)
        if save:
            build_file += build_part
    if save:
        output(save_to, build_file)
    quit()
# ______________________________________________________________________________________________________________________

build_part += "All projects and workflows in Organization" + '\n' + '\n'
print(build_part)
if save:
    build_file += build_part
i = 0
for prjct in all_projects:
    build_part = ''
    sys.stdout.write('processing..')
    sys.stdout.flush()
    try:
        build_part += "{:<8}{}".format(prjct.id, prjct.display_name) + '\n'
        build_part += "{:<12},{:<14},{:<28},{:<28},{:<10},{}".format('Project_id', 'Workflow_id', 'Created date',
                                                                     'Finished date', 'Finished date', 'Subjects',
                                                                     'Workflow name') + '\n'
        for workflow_id, project_id in all_workflows:
            i += 1
            if i % 5 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            if prjct.id == project_id:
                wrkflw = Workflow(int(workflow_id))
                finished_at = wrkflw.finished_at
                if finished_at is None:
                    finished_at = ' '
                build_part += u"{:<12},{:<14},{:<28},{:<28},{:<10},{}".format(prjct.id, wrkflw.id, wrkflw.created_at,
                                                                              finished_at, wrkflw.subjects_count,
                                                                              wrkflw.display_name) + '\n'
    except panoptes_client.panoptes.PanoptesAPIException:
        build_part += str(sys.exc_info()[1]) + ". You may not have permission to view that project" + '\n'
    build_part += '\n'
    print('\n')
    print(build_part)
    if save:
        build_file += build_part
if save:
    output(save_to, build_file)
# ____________________________________________________________________________________________________________________
