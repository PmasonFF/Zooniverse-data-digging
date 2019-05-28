## org_workflow_stats_expanded.py

This script was written in Python 3.7 so as to work for Python 2.7 or Python 3+
It requires panoptes-client to be installed and for Python 2.7 the package futures as well.

The script assumed the user has their zooniverse credentials set up in their operating system varaibles as USERNAME and PASSWORD.  All public projects do not require login; private projects will not be shown with out login.

It uses arguments to pass required details to the script. These are detailed below. A typical command line wuld be
$ Python org_workflow_stats_expanded.py -o 16 -w workflow_list.csv -s output_file.csv
This example uses a workflow list located in the directory the script is run from (working directory) and saves the listing to a file there.

````
usage: org_workflow_stats _process_bar.py [-h]
      [--ORG_ID ORG_ID]
                                          [--workflows_list WORKFLOWS_LIST]
                                          [--projects_list PROJECTS_LIST]
                                          [--save_to SAVE_TO]

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
@/path/to/args.txt.

optional arguments:
  -h, --help            show this help message and exit
  --ORG_ID ORG_ID, -o ORG_ID
                        The organization to be queried, by organization.id. An
                        integer, with the default as 16 (for Notes From
                        Nature). example -o 16
  --workflows_list WORKFLOWS_LIST, -w WORKFLOWS_LIST
                        An optional list of workflows to include. The .csv
                        file must have a column headed 'workflows' with each
                        record a workflow.id in the organization. Give the
                        full path (from the directory where this script is
                        run, or from the root directory) and the file name.
                        example -w some_path\workflows_list.csv
  --projects_list PROJECTS_LIST, -p PROJECTS_LIST
                        An optional list of projects to include. The .csv file
                        must have a column headed 'projects' with each record
                        a project.id in the organization. Give the full path
                        (from the directory where this script is run, or from
                        the root directory) and the file name. example -p
                        some_path\projects_list.csv
  --save_to SAVE_TO, -s SAVE_TO
                        An optional file name (including extension ".csv"
                        where the output will be saved in csv format. Give the
                        full path (from the directory where this script is
                        run, or from the root directory) and the file name.
                        example -s some_path\output_file.csv
````
