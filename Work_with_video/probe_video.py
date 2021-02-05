""" Requires packages ffprobe-python. ffprobe-python requires a functioning FFmpeg installation
with the location of ffmpeg/bin included in the Path environmental variables """

from ffprobe import FFProbe

metadata = FFProbe('RCNX0003.AVI')
print(metadata)

print(metadata.streams)
print(metadata.streams[0])
print(metadata.streams[0].codec_description())