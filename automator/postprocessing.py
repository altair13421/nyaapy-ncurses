import os
from automator import MEDIA_DIR
import subprocess
import json
from automator import utils

# os.system(f'ffmpeg -hwaccel cuda -i "{os.path.join(".", item)}" -c:v h265_nvenc -profile:v high444p -pixel_format yuv444p -f mp4 "{os.path.join("converted", item)}.mp4"')
# to Copy all Subs and all Audio
# os.system(f'ffmpeg -i "{os.path.join(".", item)}" -map 0:s? -c:v hevc_nvenc -preset p4 "{os.path.join("Converted", item)}"')
# os.system(f'ffmpeg -hwaccel cuda -i "{os.path.join(path, item)}" -map 0 -c:v hevc_nvenc -preset p4 "{os.path.join(path, "converted", item)}"')
# ffmpeg -hwaccel cuda -i <VIDEOFILE> -i  <SUBFFILE> -c:v copy -c:a copy -c:s <SUBFORMAT> <OUTPUTFFILE>
# Video Related

# Showing Video_information/streams
# ffprobe -show_format -show_streams -loglevel quiet -print_format json -i
def extract_subs():
    """ for item in os.listdir():
        if item == "subs":
            continue
        foldername = f"Subs - {item}"
        os.system(f'ffmpeg -i "{item}" \
            -map 0:s:0 -c copy "{os.path.join("subs", foldername,"English.ass")}" \
            -map 0:s:1 -c copy "{os.path.join("subs", foldername,"Arabic.ass")}" \
            -map 0:s:2 -c copy "{os.path.join("subs", foldername,"Deutsch.ass")}" \
            -map 0:s:3 -c copy "{os.path.join("subs", foldername,"Espanol(Espana).ass")}" \
            -map 0:s:4 -c copy "{os.path.join("subs", foldername,"Espanol.ass")}" \
            -map 0:s:5 -c copy "{os.path.join("subs", foldername,"Francais.ass")}" \
            -map 0:s:6 -c copy "{os.path.join("subs", foldername,"Italiano.ass")}" \
            -map 0:s:7 -c copy "{os.path.join("subs", foldername,"Portuges(Brazilian).ass")}" \
            -map 0:s:8 -c copy "{os.path.join("subs", foldername,"Russian.ass")}"'
        ) """
    pass

def convert_hevc():
    pass

def check_video_information(path: str = "") -> list:
    if path == "":
        working_dir = MEDIA_DIR
    else:
        if os.path.exists(path):
            if os.path.isdir(path):
                working_dir = path
            else:
                working_dir = None
    all_media = list() # all_media in sub_folder
    if working_dir is not None:
        for root, dirs, files in os.walk(working_dir):
            for filename in files:
                if filename.__contains__(".mkv") or filename.__contains__(".mp4"):
                    video_info = json.loads(subprocess.getoutput(f'ffprobe -show_format -show_streams -loglevel quiet -print_format json -i "{os.path.join(root, filename)}"'))
                    video_info["file_loc"] = os.path.join(root, filename)
                    all_media.append(video_info)
    else:
        if path.__contains__('.mkv') or path.__contains__('.mp4'):
            video_info = json.loads(subprocess.getoutput(
                            f'ffprobe -show_format -show_streams -loglevel quiet -print_format json -i "{path}"'
                        ))
            all_media.append(video_info)
        else:
            utils.rprint_error("Not a Video File of .mkv, or .mp4 extension")
    return all_media

def delete_original():
    pass
