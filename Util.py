from os.path import exists, join, realpath, split

def get_real_filename(filename : str):
    path_to_script = realpath(__file__)
    path_to_script_directory, _ = split(path_to_script)
    return join(path_to_script_directory, filename)