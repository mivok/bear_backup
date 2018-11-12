#!/usr/bin/env python3
import argparse
import datetime
import glob
import json
import os.path
import pathlib
import re
import sqlite3
import subprocess
import sys
import zipfile

# Paths to various files
approot = os.path.expanduser("~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear")
dbpath = os.path.join(approot, "Application Data/database.sqlite")
assetpath = os.path.join(approot, "Application Data/Local Files")
imagepath = os.path.join(assetpath, "Note Images")
filepath = os.path.join(assetpath, "Note Files")

asset_re = re.compile(r'\[(image|file):([^]]+)\]')

# The epoch for apple timestamps in the bear database is 1 Jan 2001, so we
# need to add the following offset to the timestamps to get a unix timestamp
apple_epoch = 978307200

class Note(object):
    def __init__(self, db, note_id):
        self.db = db
        self.note_data = self.db.execute("SELECT * FROM ZSFNOTE WHERE Z_PK=?",
                                    (note_id,)).fetchone()

    def title(self):
        return self.note_data["ZTITLE"]

    def text(self):
        return self.note_data["ZTEXT"]

    def last_modified(self):
        return datetime.datetime.fromtimestamp(
            self.note_data["ZMODIFICATIONDATE"] + apple_epoch)

    def text_with_converted_asset_paths(self):
        """Returns the note text, but with any asset paths changed to point to
        the textbundle location.

        In addition, the image/file prefixes to the image path are removed
        too, because in an exported bearnote file it's just
        [assets/filename.ext]
        """
        return re.sub(asset_re,
                      lambda m: "[%s]" % (self.convert_asset_path(m[2])),
                      self.text())

    def convert_asset_path(self, filename):
        """Strips any path to an asset and replaces it with assets/ for use in
        textbundles"""
        return re.sub(r'^.*/', 'assets/', filename)

    def asset_filenames(self):
        filenames = set()
        for m in re.findall(asset_re, self.text()):
            if m[0] == 'file':
                filenames.add(os.path.join(filepath, m[1]))
            elif m[0] == 'image':
                filenames.add(os.path.join(imagepath, m[1]))
        return filenames

    def filename(self):
        """Generates a filename from the note title, without any file
        extension"""
        filename = self.title()
        # Strip anything that isn't alphanumeric or spaces
        filename = re.sub('[^\w\s]+', '_', filename)
        # Collapse spaces
        filename = re.sub('\s+', ' ', filename)
        return filename

    def full_filename(self):
        """Gets the full filename of the note on disk, including the .bearnote
        extension"""
        return pathlib.Path(self.filename()).with_suffix(".bearnote")

    def existing_file_is_newer(self):
        filename = self.full_filename()
        if not filename.exists():
            return False
        mtime = datetime.datetime.fromtimestamp(filename.stat().st_mtime)
        if mtime < self.last_modified():
            return False
        return True

    def zip_note(self, filename=None):
        """Adds the note to a zipfile in bearnote format.

        The bearnote format is almost identical to the textbundle format,
        except that asset (image and pdf) links aren't markdown images,
        they're just `[path/to/file]` (without backticks)
        """
        if filename is None:
            filename = self.filename()
        filename = pathlib.Path(filename).with_suffix(".bearnote")
        zip_file = zipfile.ZipFile(str(filename), "w",
                               compression=zipfile.ZIP_DEFLATED)
        # Add info.json
        zip_file.writestr(os.path.join(filename, "info.json"), json.dumps({
            "type": "public.plain-text",
            "version": "2"
        }))
        # Add text
        zip_file.writestr(os.path.join(filename, "text.txt"),
                          self.text_with_converted_asset_paths())
        # Add assets
        for filename in self.asset_filenames():
            zip_file.write(filename,
                           os.path.join(filename,
                                        self.convert_asset_path(filename)))

class BearDb(object):

    def __init__(self):
        self.db = sqlite3.connect("file:%s?mode=ro" % dbpath, uri=True)
        self.db.row_factory = sqlite3.Row

    def all_notes(self):
        ids = self.db.execute(
            "SELECT Z_PK FROM ZSFNOTE WHERE ZTRASHED != 1").fetchall()
        notes = [Note(self.db, i["Z_PK"]) for i in ids]
        return notes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Back up bear notes")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print additional messages during backup')
    parser.add_argument('-d', '--debug', action='store_true',
                        help="don't back up - bring up a debug console instead")
    parser.add_argument('-f', '--force', action='store_true',
                        help="Overwrite existing files even if newer")
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help="Don't create/delete any files, just print "
                        "what would happen")
    parser.add_argument('-o', '--notify', action='store_true',
                        help="Show an OSX notification once backup is complete")
    parser.add_argument('-r', '--remove', action='store_true',
                        help="Remove any deleted notes from the backup")
    parser.add_argument('dirname', metavar='DIRECTORY', type=os.path.expanduser,
                        help='directory to back up notes to')
    args = parser.parse_args()

    if args.dry_run:
        # Dry run implies verbose
        args.verbose = True

    if args.verbose:
        print("Backing up to: %s" % args.dirname)

    # Make sure the directory we are backing up to exists, then cd into it
    os.makedirs(args.dirname, exist_ok=True)
    os.chdir(args.dirname)

    bear_db = BearDb()
    notes = bear_db.all_notes()

    if args.debug:
        import code
        code.interact(banner="Debug console", local=locals())
        sys.exit(0)

    for note in notes:
        if not args.force:
            if note.existing_file_is_newer():
                continue

        if args.dry_run:
            print("Would back up: %s" % note.filename())
        else:
            if args.verbose:
                print("Backing up: %s" % note.filename())
            note.zip_note()

    if args.remove:
        keep_notes = {str(note.full_filename()) for note in notes}
        all_notes = set(glob.glob("*.bearnote"))
        delete_notes = all_notes - keep_notes
        for note in delete_notes:
            if args.dry_run:
                print("Would delete: %s" % note)
            else:
                if args.verbose:
                    print("Deleting %s" % note)
                os.remove(note)

    if args.notify:
        text = "Backed up notes to %s" % args.dirname
        title = "Bear notes backup"
        subprocess.run(["osascript","-e",
                        "display notification \"%s\" with title \"%s\"" % (
                            text, title)])
