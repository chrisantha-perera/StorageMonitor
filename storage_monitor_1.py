"""Script to monitor storage usage on a Linux system."""
import time
import os
import argparse


def run_filesystem_watcher(fs_path, exclude_files, max_storage):
    try:
        while True:
            # Get the storage usage of fs_path
            while fs_size(fs_path) > max_storage:
                delete_oldest_file(fs_path, exclude_files)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")


def fs_size(fs_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(fs_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def delete_oldest_file(filesystem_directory, excluded_files):
    oldest_file = None
    oldest_time = float('inf')
    for foldername, subfolders, filenames in os.walk(filesystem_directory):
        for filename in filenames:
            filepath = os.path.join(foldername, filename)
            if not is_excluded(filepath, excluded_files):
                file_time = os.path.getmtime(filepath)
                if file_time < oldest_time:
                    oldest_time = file_time
                    oldest_file = filepath
    if oldest_file:
        os.remove(oldest_file)
        print(f'Deleted oldest file: {oldest_file}')
    else:
        print('No files to delete')

def is_excluded(path, excluded_files):
    for excl_file in excluded_files:
        if path.endswith(excl_file):
            return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("fs_path", help="Path to the filesystem directory to be monitored")
    parser.add_argument("--exclude_files", nargs='*', default=[], help="File extensions to be excluded")
    parser.add_argument("--max_storage", type=int, default=800 * 1024**3, help="Maximum storage in bytes")
    args = parser.parse_args()
    run_filesystem_watcher(args.fs_path, args.exclude_files, args.max_storage)