"""Script to monitor storage usage on a Linux system."""
# standard libraries
import os
import subprocess
import time
import argparse
from datetime import datetime, timedelta
# 3rd party libraries
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MonitorFilesystem(FileSystemEventHandler):

    def __init__(self, filesystem_directory, excluded_files, max_storage, expiration):
        self.filesystem_directory = filesystem_directory
        self.excluded_files = excluded_files
        self.max_storage = max_storage
        self.expiration = expiration
        self.check_folder_size()
        # proposed: the converse? map of filepath -> expiration date
        # check the map: do all non-excluded filepaths have an expiration date?

    def on_created(self, event):
        if not event.is_directory:
            print(event.src_path, event.event_type)
            if not self.is_excluded(event.src_path):
                self.set_expire(event.src_path)
                # check file size before choosing to save it
            self.check_folder_size()

    def is_excluded(self, path):
        for excl_file in self.excluded_files:
            if path.endswith(excl_file):
                return True
        return False

    def set_expire(self, path):
        expiration_time = datetime.now() + timedelta(days=self.expiration)
        expiration_str = expiration_time.strftime('%H:%M %m/%d/%Y')
        # this is dependent on device staying up
        # but docker is ephemeral
        # proposed: modify a hash table "delete_on_date" and add the filepath
        # proposed: the converse? map of filepath -> expiration date
        command = f'echo "rm -f {path}" | at {expiration_str}' 
        subprocess.run(command, shell=True, check=True)

    def check_folder_size(self):
        filesystem_size = self.get_folder_size(self.filesystem_directory)
        while filesystem_size > self.max_storage:
            self.delete_oldest_file()
            filesystem_size = self.get_folder_size(self.filesystem_directory)

    def get_folder_size(self, start_path='.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def delete_oldest_file(self):
        oldest_file = None
        oldest_time = float('inf')
        for foldername, subfolders, filenames in os.walk(self.filesystem_directory):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                if not self.is_excluded(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < oldest_time:
                        oldest_time = file_time
                        oldest_file = filepath
        if oldest_file:
            os.remove(oldest_file)
            print(f'Deleted oldest file: {oldest_file}')
        else:
            print('No files to delete')
    
    # query for un-expiring files
    def check_files_expire(self):
        # run atq command (or parse 'at' command's directory)
        # pull out filepaths
        files = ['']
        file_set = set(files)
        for foldername, subfolders, filenames in os.walk(self.filesystem_directory):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                if not self.is_excluded(filepath):
                    if not filepath in file_set:
                        self.set_expire(filepath)

def run_filesystem_watcher(path, exclude_files, max_storage, expiration):
    event_handler = MonitorFilesystem(path, exclude_files, max_storage, expiration)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the filesystem directory to be monitored")
    parser.add_argument("--exclude_files", nargs='*', default=[], help="File extensions to be excluded")
    parser.add_argument("--max_storage", type=int, default=800 * 1024**3, help="Maximum storage in bytes")
    parser.add_argument("--expiration", type=int, default=7, help="Expiration time in days")
    args = parser.parse_args()
    run_filesystem_watcher(args.path, args.exclude_files, args.max_storage, args.expiration)
