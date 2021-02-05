## Introduction
These scripts use FFmpeg to work with video to reformat and size videos for use as zooniverse subjects.  A working installation of FFmpeg is required - See https://ffmpeg.org/ for details to download and install FFmpeg on your platform.
Then the Python packages ffmpy and ffprobe-python need to be installed in the Python environment either using pip, your Python Editor package installer or other common means on mac or linux systems.

As written the scripts need the FFmpeg suite to be included in the system path. In Windows it is easy enough to add ffmpeg/bin to the Path system environmental variable list. Depending on the Mac system you may need to use bash or add ffmpeg/bin to an existing profile.  In any case the command ffmpeg -h should produce a help file  from any cmd or terminal window on your machine.

## Video formats
In the simplest view, a video format such as .mp4 is a container which includes a video stream with some encoding, and a audio stream with some audio encoding.  How compatible the video file is depends not only on the "format" (eg .mp4) being supported but the encoding of the component streams must be supported by the platform.  So zooniverse supports .mp4 files among other formats - yes!, but not all of the possible ways the component streams can be encoded.

The uploader in this repository uses one set of encoders and a format that has worked in the past with zoonivers, but there are many choices that will work, and the best video quality at smallest file size is elusive.  In some cases a relatively small saving can be made reducing audio quality, or having no audio at all. Colour depth can be traded for resolution, or vice versa.  You may have to experiment to find a solution for your needs

One option is to look through other zooinverse projects that use video and if there are example of videos that match you project requirement for colour depth, resolution, and audio quality, use probe_video.py to determine the encoding and pixel sizes and try these with compress_video.py on your video files. You can optionally upload test videos with that script and see if they play , and if they are of sufficient quality as zooniverse subjects.  Note in particular the -c:v libx264 -crf 30 video encoding can be tailored for final file size and quality by altering the crf number. Also note the pixel format -pix_fmt yuv420p was significant for zooniverse, and files in some other common pixel formats did not play.

## Other FFmpeg functions
As well as being used for these Python scripts, FFmpeg with its command line structure, can be used for many other video operations. One use in particular is to automate cutting a long vdeo into shorter segments suitable as zooniverse subjects. The following batch file from [celdemire of Birdcams](https://github.com/celdermire/birdcams-zooniverse) runs in FFmpeg to cut longer .mp4 files into 10 sceond clips:
````
##SPLIT COMMAND
##batch file is IN the folder with the files, output file is on C:\
for %%a in ("*.mp4") do ffmpeg -i "%%a" -c copy -force_key_frames 1 -segment_time 10 -f segment -force_key_frames 1 -reset_timestamps 1 -segment_list "%%a_manifest" -segment_list_type csv -y "\split_files\%%~na_%%03d.mp4"
````
While this is set up for .mp4 input files, it can be modified to work with other video formats.  For example a longer .avi file may be split, then the clips can be individually resized and uploaded, or the file can be converted and reduced, then split, and the clips uploaded with a modified uploader or using the panoptes CLI. 
