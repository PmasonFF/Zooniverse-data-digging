""" Requires packages ffmpy, and optionally panoptes_client. ffmpy requires a functioning FFmpeg installation
with the location of ffmpeg/bin included in the Path environmental variables """

import ffmpy


def compress(original_location, output_name):  # converts video container and reduces file size
    inp = {original_location: None}
    # outp = {output_name: '-loglevel 8 -t 10 -vf scale=640:480 -pix_fmt yuv420p -y'}
    outp = {output_name: '-loglevel 8 -t 10 -c:v libx264 -crf 30 -pix_fmt yuv420p -c:a aac -b:a 128k -y'}
    ff = ffmpy.FFmpeg(inputs=inp, outputs=outp)
    return ff.run()


compress('RCNX0003.AVI', 'h264crf30t10.mp4')

# # to create a subject to examine in zooniverse:
#
# from panoptes_client import Panoptes, Project, SubjectSet, Subject
# Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])  # if environmental variables used
# # Panoptes.connect(username='actual_zooniverse_user_name', password='actual_zooniverse_password')  # NOT secure!!!!
# project = Project.find(slug='elwest/woodpecker-cavity-cam')  # replace slug with required project
# sub_set = SubjectSet.find(XXXXXX)  # replace XXXXXX with existing subject set.id previously created for testing
# subject = Subject()
# subject.links.project = project
# subject.add_location(output_name)  # replace output_name with output_name called in the function call above
# subject.metadata['Filename'] = output_name
# subject.save()
# sub_set.add(subject.id)
