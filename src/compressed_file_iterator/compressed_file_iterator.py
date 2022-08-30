#!/usr/bin/python3
# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4:
"""
Example code to create an iterator (for use in a for-loop) that can read
a GZipped file using '/usr/bin/zcat' as a subprocess or a regular file
using Python's internal file handling methods. The contents of the file
are returned by the iterator one line at a time, with CR/LF characters
('\r' and '\n') stripped.

For testing, 'numbers.txt' was a text file containing the numbers 1 to
50_000 in order, each on a single line. For other compression methods
such as gzip, the compressed version of the file would be named
'numbers.txt.gz'.
"""

# Subprocess code based on:
#     https://stackoverflow.com/questions/11728915/python-iterate-on-subprocess-popen-stdout-stderr

# import async
# import collections
import collections.abc
# from configparser import ConfigParser, ExtendedInterpolation
import json
import os
# import os.path
import pathlib
import pprint
import subprocess
# import sys


def left_join(strings: list[str]):
    acc = ""
    for s in strings:
        acc = s + acc
        yield acc


def flatten(x):
    result = []
    for el in x:
        if isinstance(x, collections.abc.Iterable) and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

# print(flatten(["junk",["nested stuff"],[],[[]]]))


class Shell:
    """
    Run a command and iterate over the stdout/stderr lines
    """

    def __init__(self, args, cwd="./"):
        self.args = args

        self.pro_cess = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.line = ""
        self.code = ""

    def __iter__(self):
        return self

    def __next__(self):
        self.line = self.pro_cess.stdout.readline()
        self.code = self.pro_cess.poll()

        do_it_001 = False
        if do_it_001:
            print("self.code = ")
            pprint.pprint(self.code)
            print("self.line = ")
            pprint.pprint(self.line)

        if len(self.line) == 0 or self.code is not None:
            if len(self.line) == 0:
                raise StopIteration
        return str(self.line, encoding="utf-8").rstrip("\r\n")


class MyFile:
    """
    Open a file and iterate over the lines
    """

    def __init__(self, args, cwd="./"):
        self.args = args
        self.cwd = cwd
        self.fn = args[0]
        self.fh = open(self.fn, "r", encoding="utf-8")
        self.line = ""

    def __iter__(self):
        return self

    def __next__(self):
        self.line = self.fh.readline()
        if self.line == "":
            raise StopIteration
        return str(self.line).rstrip("\r\n")

    def __del__(self):
        self.fh.close()


class MyIterator:
    """
    Fake class to iterate over content in either case
    """

    def __init__(self, args, cwd="./",
                 config_file='compressed_file_iterator.json',
                 ):
        self.args = args
        self.cwd = cwd

        config = None
        with open(config_file, encoding="utf-8") as f:
            config = json.load(f)

        suffix = pathlib.Path(args[0]).suffixes
        suffix_len = len(suffix)

        suffix_str = []
        for i in range(suffix_len + 1):
            suffix_str.append("")
            for j in range(i, suffix_len):
                suffix_str[i] += suffix[j]

        # # foo = ['as', 'df', 'gh', 'jk']
        # # print(list(left_join(reversed(foo))))
        suffix_str = list(reversed(list(left_join(reversed(suffix)))))

        my_os = os.name
        my_args = list()
        for i in range(len(suffix_str)):
            if suffix_str[i] in config:
                my_args = flatten(
                    (
                        config[suffix_str[i]]["base_command"][my_os],
                        config[suffix_str[i]]["base_options"][my_os],
                        args[0],
                    )
                )
                break
        else:
            my_args = flatten(
                (
                    config[".*"]["base_command"][my_os],
                    config[".*"]["base_options"][my_os],
                    args[0],
                )
            )

        self.mi = None

        self.mi = Shell(my_args)

        # if 'gz' in args[0]:
        #     self.mi = Shell(args)
        # else:
        #     self.mi = MyFile(args)

    def __iter__(self):
        return self.mi

    def __next__(self):
        line = self.__next__()
        if line == "":
            raise StopIteration
        return line


def main():
    """
    Main testing routine.
    """

    if not os.path.exists('numbers.txt'):
        with open('numbers.txt', 'w', encoding='utf-8', ) as file:
            for i in range(1, 10001):
                file.write(str(i) + "\n")
    if not os.path.exists('foo.json'):
        dictionary = {
                '.*': {
                    'base_command': {
                        'posix': '/bin/cat',
                        },
                    'base_options': {
                        'posix': [],
                        },
                    'type': 'Plain',
                    },
                }
        json_object = json.dumps(dictionary, indent=4)
        with open('foo.json', 'w', encoding='utf-8', ) as file:
            file.write(json_object)

    tests = [
        (False, "numbers.7z"),
        (False, "numbers.zip"),
        (False, "numbers.tar"),
        (False, "numbers.tar.Z"),
        (False, "numbers.tar.bz2"),
        (False, "numbers.tar.gz"),
        (False, "numbers.tar.lz"),
        (False, "numbers.tar.lzma"),
        (False, "numbers.tar.lzo"),
        (False, "numbers.tar.xz"),
        (False, "numbers.tar.zst"),
        (True, "numbers.txt"),
        (False, "numbers.txt.Z"),
        (False, "numbers.txt.bz2"),
        (False, "numbers.txt.gz"),
        (False, "numbers.txt.lz"),
        (False, "numbers.txt.lz4"),
        (False, "numbers.txt.lzma"),
        (False, "numbers.txt.lzo"),
        (False, "numbers.txt.xz"),
        (False, "numbers.txt.zst"),
    ]
    for go, fn in tests:
        if go:
            args = [ fn, ]
            # shell = MyIterator(args, config_file='foo.json', )
            shell = MyIterator(args, config_file='foo.json', )
            if shell is not None:
                c = 0
                for line in shell:
                    if len(line):
                        c = c + int(line)
                print(fn, ": ", c)


if __name__ == "__main__":
    main()
