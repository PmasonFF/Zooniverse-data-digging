import os
import io
from PIL import Image
from panoptes_client import SubjectSet, Subject, Project, Panoptes


def compress(original_file, resized_width):
    orig_image = Image.open(original_file)
    width, height = orig_image.size
    scale = float(resized_width) / width
    scaled_size = (resized_width, int(height * scale))
    resized_file = orig_image.resize(scaled_size, Image.Resampling.LANCZOS)
    file_bytes = io.BytesIO()
    resized_file.save(file_bytes, optimize=True, quality=100, format='jpeg')
    file_bytes.seek(0, 0)
    return file_bytes


Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='pmason/fossiltrainer')

filename = r'C:\py\Skunks\Images 2021\Site_A\SPIL04_SD05_21-09-01\11080025.JPG'

subject = Subject()
subject.links.project = project
# subject.add_location(compress(filename, 960), manual_mimetype='image/jpeg')
subject.add_location(compress(filename, 960))  # fails with a broken libmagic with no error
subject.save()
subject_set = SubjectSet(128505)
subject_set.add(subject.id)
