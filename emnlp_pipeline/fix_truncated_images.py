from PIL import Image, ImageFile
from pathlib import Path
from tqdm import tqdm
import io

# https://bloom-vist.s3.amazonaws.com/Tulo%20ka%20Batang%20Babaye/IMG_20180909_130314.jpg
# https://bloom-vist.s3.amazonaws.com/Tulo%20ka%20Batang%20Babaye/IMG_20180909_130349.jpg
# s3://bloom-vist/Tulo ka Batang Babaye/
# Traceback (most recent call last):
#   File "/home/cleong/projects/personal/SIL/bloom-captioning/test_load.py", line 502, in <module>
#     download_dataset_and_images_and_show_one(alpha3_lang="ceb")
#   File "/home/cleong/projects/personal/SIL/bloom-captioning/test_load.py", line 128, in download_dataset_and_images_and_show_one
#     image.save(buffer, format=format)
#   File "/home/cleong/miniconda3/envs/bloom/lib/python3.9/site-packages/PIL/Image.py", line 2264, in save
#     self._ensure_mutable()
#   File "/home/cleong/miniconda3/envs/bloom/lib/python3.9/site-packages/PIL/Image.py", line 626, in _ensure_mutable
#     self._copy()
#   File "/home/cleong/miniconda3/envs/bloom/lib/python3.9/site-packages/PIL/Image.py", line 619, in _copy
#     self.load()
#   File "/home/cleong/miniconda3/envs/bloom/lib/python3.9/site-packages/PIL/ImageFile.py", line 251, in load
#     raise OSError(
# OSError: image file is truncated (42 bytes not processed)

if __name__ == "__main__":
    jpegs = list(Path("./data/bloom_downloads/Tulo ka Batang Babaye/").rglob("*.jpg"))
    # jpegs = list(Path("./data/bloom_downloads/").rglob("*.jpg"))
    out_folder = Path("./fixed_images")
    out_folder.mkdir(exist_ok=True)
    problem_files = []
    for jpeg in tqdm(jpegs):
        with Image.open(str(jpeg)) as image:
            # image.save()
            out_file = out_folder / jpeg.name
            try:
                image.load()
            except OSError:
                problem_files.append(jpeg)

    ImageFile.LOAD_TRUNCATED_IMAGES = True
    for problem_file in problem_files:
        with Image.open(str(problem_file)) as image:
            # image.save()
            out_file = out_folder / f"{problem_file.stem}.bmp"
            image.save(out_file)

    for bmp_file in out_folder.glob("*.bmp"):
        with Image.open(str(bmp_file)) as image:
            out_file = out_folder / f"{bmp_file.stem}.jpg"
            image.save(out_file)

    ImageFile.LOAD_TRUNCATED_IMAGES = False
    for fixed_jpeg in out_folder.glob("*.jpg"):
        with Image.open(str(fixed_jpeg)) as image:
            image.load()
# ImageFile.LOAD_TRUNCATED_IMAGES = True
