import shutil

def is_exiftool_installed():
    return shutil.which('exiftool') != None
