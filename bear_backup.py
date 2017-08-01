#!/usr/bin/env python3
import json
import os.path
import pathlib
import re
import sqlite3
import sys
import zipfile

# Paths to various files
approot = os.path.expanduser("~/Library/Containers/net.shinyfrog.bear/Data")
dbpath = os.path.join(approot, "Documents/Application Data/database.sqlite")
assetpath = os.path.join(approot, "Documents/Application Data/Local Files")
imagepath = os.path.join(assetpath, "Note Images")
filepath = os.path.join(assetpath, "Note Files")

asset_re = re.compile(r'\[(image|file):([^]]+)\]')

class Note(object):
    def __init__(self, db, note_id):
        self.db = db
        self.note_data = self.db.execute("SELECT * FROM ZSFNOTE WHERE Z_PK=?",
                                    (note_id,)).fetchone()

    def title(self):
        return self.note_data["ZTITLE"]

    def text(self):
        return self.note_data["ZTEXT"]

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
        filename = note.title()
        # Strip anything that isn't alphanumeric or spaces
        filename = re.sub('[^\w\s]+', '_', filename)
        # Collapse spaces
        filename = re.sub('\s+', ' ', filename)
        return filename

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
    bear_db = BearDb()
    notes = bear_db.all_notes()

    for note in notes:
        print(note.filename())
        note.zip_note()
