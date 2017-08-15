This is an attempt to open a repository of the scripts I have written for various zooniverse projects.
It is a work in progress.

## DBSCAN clustering script

The first script I want to set up is a DBSCAN point clustering routine and Demo for it.
This DBSCAN clustering algorithm is intended for data sets which are limited to a few hundred points – it is not optimized for R-trees or large data sets, but works well for the data sets expected from drawing tool uses in zooniverse projects. 

## Flatten classification file building blocks

The next group of scripts is my approach to the problem of flattening the JSON formatted strings in the Zooniverse classification download.  This is directed at project owners with little IT support using the project builder to create their project. Like the project builder the effort is made up of a basic framework on which blocks are added - basically the correct blocks are added to handle the output from each particular task in the project. Each block of code must be slightly modified in a easy to understand way to match the project's task labels so the output data is labeled in a way the project owner expects.
The following modules or blocks are planned:
#### 1) The basic framework with ability to Slice the Classification file in various ways to select the pertinent records.
This will provide the framework the other blocks will be added onto. By itself it can be used to slice the Classification file based on various conditional clauses using specificed fields in the classification records.

#### 2) General utility blocks to provide: 
These are available now in some form, they will be generalized and added asap.
  -	user_name This block replaces not-logged-in user_name based on an external picklist prepared elsewhere and keyed off user_ip.  The scripts to generate a picklist can use ip or browser data to group the not-logged-in users.
  -	image_number This block attempts to get subject image metadata from the subject_data field and generate a image identifier that may be more significant to the project owner. Alternately a cross-reference csv file can be provided - subject_id:image_number. The image_number will be a field in the output file to aid analysis.
  -	elapsed_time This block pulls the started and finished times from the metadata field and calculates the elapsed time the user spent on the classification.
  -	image_size This block attempts to pull the natural height and width for the subject image from the metadata file. This can be used for various scaling operations for plotting, clustering or for testing out-of-bounds drawing tools.

#### 3) Task specific blocks that handle the various task types allowed by the project builder.  The following blocks are planned. Those with an asterix are written and working in some form:
- *Question with single answer
- *Question with Multiple answers 
- *Drawing tool - Point
- Drawing tool - Line
- *Drawing tool - Circle
- Drawing tool - Box (rectangle and column)
- Drawing tool - Triangle
- Drawing tool - Polygon
- Drawing tool - Elipse
- Drawing tool - Bezier
- Transcription - single field
- Transcriptiion - drop-down
- Transcription - multiple fields
- Survey - 2D (choice and howmany) full array
- Survey - 3D (choice, howmany, behaviour) full array
- Survey - 2D non-zero elements only
- Survey - 3D non-zero elements only_

#### 4) Test blocks which will preform simple tests on the output from one or more of the blocks listed in 3):
-	*Test points from point drawing tools lay within the image_size (ie no out-of-bounds points.)
-	*Test circle centers are within a fixed percentage of the circle radius of an image edge (ie part of the circle lies within the image.)
-	*Test that no two points of the same type are placed within a distance “eps” of each other on the same subject by the same classifier (ie test for double clicks)
-	*As for above except for circle centres.
-	*Test the radius of a circle is within a range specified (relative to the image_size)
-	Test the duration is consistent with a human classifier.







