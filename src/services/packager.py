import os
import shutil
#packager will: 
# create output: folder_name_timestamp
#                 |
#                 ---template_n.html
#                 |
#                 ---static
#                   |
#                   ---*.js
#                   ---*.css

#example list build for static path input: all_statics = [this_file.path for this_file in (os.scandir('src/web/static/'))]

def create_output_folder(output_path: str, html_path: str, static_paths: [str]) -> None:
    #create containing folders
    static_output = os.path.join(output_path, 'static/')
    os.makedirs(static_output, exist_ok=True)
    #copy html into it
    shutil.copy(html_path, output_path)
    #copy all the other shit
    for path in static_paths:
        shutil.copy(path, static_output)