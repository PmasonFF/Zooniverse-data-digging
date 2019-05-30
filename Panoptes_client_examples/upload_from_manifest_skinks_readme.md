## upload_from_manifest_skink.py

Requires panoptes client to be installed, no other packages beyond a basic Python 3+ install.
requires zooniverse credentials to be set up a os environmental variables, else modify line 103.

Script requires argumnets as noted below...
Typical arg list:
-m C:\py\Skinks\manifest.csv -d "C:\py\Skinks\images" -s "Test for Skinks" -f C:\py\Skinks\upload_summary.csv
Note the subject set name is optional (will default to "New subject set"0 and the summary output is also optional.

For support contact @Pmason through zooniverse.



````
usage: upload_from_manifest_skinks.py [-h] --manifest MANIFEST
                                      --image_directory IMAGE_DIRECTORY
                                      [--subject_set SUBJECT_SET]
                                      [--save_to SAVE_TO]

This script is an uploader customized for the project skink-spotter-nz.
It requires a manifest in a specific format. It builds multiframe image 
subjects with the metadata a subject number and the image filenames.
Subjects are uploaded to a specified subject set that exists or is created 
in the project. The script reports errors that occurred and is restartable
without subject duplication. Optionally a summary file of all subjects 
successfully uploaded can be produced and saved.
To connect to panoptes the zooniverse user_name and password must be stored
in the users operating system environmental variables USERNAME and PASSWORD.
If this is not the case line 103 must be modified to the form 
Panoptes.connect(username='actual_user_namejovirens', password='actual_password'),
and steps must be taken to protect this script.
NOTE: You may use a file to hold the command-line arguments like:
@/path/to/args.txt.

optional arguments:
  -h, --help            show this help message and exit
  --manifest MANIFEST, -m MANIFEST
                        The manifest is required. It must list the image files
                        to be uploaded in columns headed image1 through
                        image10, and may have an additional column 'subject'
                        Give the full path (from the directory where this
                        script is run, or from the root directory) and the
                        file name. The manifest must be a csv file using
                        commas as the delimiter. example -m
                        C:\py\Skinks\manifest.csv
  --image_directory IMAGE_DIRECTORY, -d IMAGE_DIRECTORY
                        The directory where the images files are to be found.
                        Give the full path (from the directory where this
                        script is run, or from the root directory) example -d
                        C:\py\Skinks\images
  --subject_set SUBJECT_SET, -s SUBJECT_SET
                        The name of the subject set to create for or to add
                        the uploaded subjects to. This argument is optional
                        and defaults to "New subject set". This name can be
                        edited via the project builder. If the script is being
                        restarted with the intention of adding more subjects
                        to an existing set, the subject_set name must be
                        exactly the same. example -s "A different set" (note
                        quotes)
  --save_to SAVE_TO, -f SAVE_TO
                        An optional file name (including extension ".csv"
                        where the summary of the subjects uploaded will be
                        saved in csv format. Give the full path (from the
                        directory where this script is run, or from the root
                        directory) and the file name. example -s
                        some_path\summary_file.csv

````
