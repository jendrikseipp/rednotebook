#!/usr/bin/env python

"""Merges two rednotebook directories

To merge .txt files into a destination rednotebook:

1. Quit rednoteboot
2. Run it again and do a backup
3. Quit it
4. Merge in your files:

   rednotebook-merge.py -n -d ~/.rednotebook/data -t "title" /path/to/*.txt

You will see a log like this:

    Updating file /home/sglass/.rednotebook/data/2023-02.txt
       - merging day 1
       - merging day 2
       - added new day 3
       - merging day 6
       written
    Updating file /home/sglass/.rednotebook/data/2023-03.txt
       - merging day 1
       - added new day 21
       written
    Adding new file 2023-04.txt
       - added new day 2
       written

If that looks OK, then

5. Run that again but without the -n flag

It should merge in the files. You can see things that were merged in since
each item as an 'Added from <title>: /path/to/xxx.txt' before the merged text.
"""

import argparse
import os
import sys
import yaml

def doit(argv):
    """Merge a list of files into another .rednotebook directory

    Args:
        argv (list of str): Program arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dest-dir', type=str, required=True,
        help='Rednotebook data directory to merge into')
    parser.add_argument('-t', '--title', type=str, default='',
        help='Title of source files, to use when merging')
    parser.add_argument('src_files', type=str, nargs='+',
        help='Files to merge in')
    parser.add_argument('-n', '--dry-run', action='store_true',
        help="Don't update destination files")
    args = parser.parse_args(argv[1:])

    for fname in args.src_files:
        header = f'Added from {args.title}: {fname}:\n'

        # Load data from the source file
        with open(fname, encoding='utf-8') as inf:
            in_data = yaml.safe_load(inf)

        base = os.path.basename(fname)

        # Figure out what the destination filename will be
        dest_fname = os.path.join(args.dest_dir, base)

        # If it exists, read it in, since we'll need to update it...
        if os.path.exists(dest_fname):
            with open(dest_fname, encoding='utf-8') as inf:
                dest_data = yaml.safe_load(inf)
            print(f'Updating file {dest_fname}')

        # ...but if it doesn't exist, create it
        else:
            dest_data = {}
            print(f'Adding new file {base}')

        # Work through day by day, merging in the data
        for day in sorted(in_data.keys()):
            text = in_data[day]['text']

            # If the day exists, append this text at the end...
            if day in dest_data:
                print(f'   - merging day {day}')
                dest_data[day]['text'] += '\n\n' + header + text

            # but if the day does not exist, create it
            else:
                print(f'   - added new day {day}')
                dest_data[day] = {'text': header + text}

        # Write out the resulting file, if requested
        if not args.dry_run:
            with open(dest_fname, 'w', encoding='utf-8') as outf:
                yaml.dump(dest_data, outf)
            print('   written')


if __name__ == '__main__':
    sys.exit(doit(sys.argv))
