# Script to back up bear notes

[Bear](http://www.bear-writer.com/) is a note taking app for mac and ios,
which syncs via icloud. Unfortunately, at the moment there is no way to
automatically back up all of your notes outside of icloud.

Thankfully, the format of the notes is fairly simple - all notes are kept in
an sqlite database and images/file attachments are kept in a folder nearby.

This script will read the sqlite database and dump all of your notes into
individual `.bearnote` files, which can be stored in somewhere like dropbox
and imported back into bear directly.

## Usage

The script requires python 3 to be installed, but doesn't require any custom
modules. Once you have python 3, you just run the script directly:

```
brew install python3
./bear_backup.py
```

The script will grab all of your notes from bear and create individual
`.bearnote` files in your current directory.

## Getting access to notes without bear

A `.bearnote` file is just a zip file, and is a variation on the
[textbundle](https://textbundle.org) file format. The primary difference is
that any assets (e.g. images or PDFs) don't use the normal markdown syntax for
embedding images, and instead the markup looks like `[assets/image1.png]`.
Aside from that however, the text.txt file is plain markdown (or bear's polar
markup if you have markdown compatibility mode turned off), and all
images/attachments are in the assets directory of the zip file.
