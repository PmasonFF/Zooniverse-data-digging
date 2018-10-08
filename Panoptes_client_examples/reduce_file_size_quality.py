from PIL import Image
import os
import io


def compress(original_file, max_size, reduced_file):
    orig_image = Image.open(original_file)
    width, height = orig_image.size
    quality = [qual for qual in range(80, 101)]

    lo = 0
    hi = len(quality)
    print(quality, lo, hi)
    file_bytes = ''
    while lo < hi:
        mid = (lo + hi) // 2

        scaled_size = (int(width * .75), int(height * .75))
        resized_file = orig_image.resize(scaled_size, Image.ANTIALIAS)

        file_bytes = io.BytesIO()
        resized_file.save(file_bytes, optimize=True, quality=quality[mid], format='jpeg')
        size = file_bytes.tell()
        print(size, quality[mid])
        if size < max_size:
            lo = mid + 1
        else:
            hi = mid
    file_bytes.seek(0, 0)
    with open(reduced_file, 'wb') as f_output:
        f_output.write(file_bytes.read())


compress(r'C:\py\image_manipulation\Data_files\04260073.JPG',
         1000000, r'C:\py\image_manipulation\reduced04260058.JPG')
