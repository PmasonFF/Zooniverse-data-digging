## Generate Classification and Subject exports

The script generate_export.py logs into the Panoptes client using User_name and Password previously set up as Environmental Variables in your Operating system.  Alternately these can be hardcoded if the code is kept secure to protect your password. It is also necessary to hardcode the desired project slug in line 7 to use the script as a stand-alone rather than a module.

The script first tests to see if 24 hours have elapsed since the last classification export was requested, and warns and terminates if not. If the last export request is more than 24 hours previous it attempts to generate a new one.  The script then waits 30 seconds for Panoptes to begin to create the export and then tests to see if thart has happened. If not it warns the export request is not being produced.

These same steps are then repeated for the Subject export.

## Download exports and slice

The script download_export_and_slice.py logs into the Panoptes client using User_name and Password previously set up as Environmental Variables in your Operating system.  Alternately these can be hardcoded if the code is kept secure to protect your password. It is also necessary to hardcode the desired project slug in line 7 to use the script as a stand-alone rather than a module.
The destination path and filenames for both the classification file and the subject export need to be hardcoded 


Unlike the code suggested in the Panoptes Client documentation, this script can handle large export files (easily > 1Gb) since it does not read the file into memory all in one go but streams the data to a file in chunks. All subsequent operations from the file are handled by Python to avoid overloading the memory available.

The script determines the age of the classification export file based on the current time and the last update to the export.  This age is calculated for EST - other time zones will need to change the hardcoded offset to zulu time.  If the export file has not completed generating the download will fail with the message 'Classifications download did not complete' and the function returns False.

If the export file exists it is then downloaded to a file 
