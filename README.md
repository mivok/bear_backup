# Script to back up bear notes

[Bear](http://www.bear-writer.com/) is a note taking app for mac and ios,
which syncs via icloud. Unfortunately, at the moment there is no way to
automatically back up all of your notes outside of icloud.

Thankfully, the format of the notes is fairly simple - all notes are kept in
an sqlite database and images/file attachments are kept in a folder nearby.

This script will read the sqlite database and dump all of your notes into
individual `.bearnote` files, which can be stored in somewhere like dropbox
and imported back into bear directly.


## Installation

The script requires python 3 to be installed, but doesn't require any custom
modules. It can be run directly from the git checkout or any other location if
desired.

Alternatively, there is a homebrew formula to install using homebrew:

```
brew install https://raw.githubusercontent.com/mivok/bear_backup/master/Formula/bear_backup.rb
```

The homebrew script also provides a launchctl module to back up every night at
midnight to a dropbox directory. If you want to use this, run:

```
brew service start bear_backup
```

## Usage

At a minimum, you need to specify a directory to back up to:

```
bear_backup.py ~/Dropbox/backups/bear
```

The script will grab all of your notes from bear and create individual
`.bearnote` files in the backup directory.

If you want to remove any notes from an existing backup that have been deleted
from bear, then you will also want to add the `-r` option:

```
bear_backup.py -r ~/Dropbox/backups/bear
```

This will clean up any notes in the backup directory that have been deleted
from bear, and is useful when you run the script against the same backup
directory multiple times. Without this, you will end up with stale notes in
the backup that are no longer in bear.

### Options

* `-v`, `--verbose` - Print out additional information, such as which notes
  are being backed up and any old notes that are removed.
* `-d`, `--debug` - This will bring up an interactive python console rather
  than back up any notes. This is only used during development.
* `-f`, `--force` - By default, bear_backup won't overwrite any notes from an
  old backup if the note hasn't been modified in bear. It does this by
  comparing modification times of the backed up file. Set `--force` to
  disable this behavior and always back up all notes, overwriting any existing
  files.
* `-n`, `--dry-run` - Don't back up or remove any notes, just show what would
  be done. Implies `--verbose`.
* `-o`, `--notify` - Prints a desktop notification once the backup is
  complete. This is useful when run as a scheduled task.
* `-r`, `--remove` - Remove any bearnote files from the destination that
  aren't in the list of notes to be backed up. In other words, this will
  remove any notes from an existing backup that have been deleted from bear.

## Restoring backups

The files are stored as individual .bearnote files, which you can import
directly into bear using bear's import option. They are stored like this
rather than as a single file to allow you to restore individual notes as
needed.

Alternatively, just double click on a note in finder and it will be imported
into bear.

## Getting access to notes without bear

A `.bearnote` file is just a zip file, and is a variation on the
[textbundle](https://textbundle.org) file format. The primary difference is
that any assets (e.g. images or PDFs) don't use the normal markdown syntax for
embedding images, and instead the markup looks like `[assets/image1.png]`.
Aside from that however, the text.txt file is plain markdown (or bear's polar
markup if you have markdown compatibility mode turned off), and all
images/attachments are in the assets directory of the zip file.
