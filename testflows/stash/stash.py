# Copyright 2021 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
import os
import sys
import json
import pickle
import marshal
import inspect
import hashlib

import testflows.stash.contrib.jsonpickle as jsonpickle

from importlib.machinery import SourceFileLoader

__all__ = ["stashed"]


def varname(s):
    """Make valid Python variable name.
    """
    invalid_chars = re.compile("[^0-9a-zA-Z_]")
    invalid_start_chars = re.compile("^[^a-zA-Z_]+")

    name = invalid_chars.sub('_', str(s))
    name = invalid_start_chars.sub('', name)
    if not name:
        raise ValueError(f"can't convert to valid name '{s}'")
    return name


def make_filename(name):
    """Make valid file name.
    """
    return "".join(l for l in name if (l.isalnum() or l in "._- ") and l not in "/")


class Hash:
    """Class that provides hashing for any object that is pickle-able.
    """
    def __init__(self, encoder=pickle):
        self._encoder = encoder

    @staticmethod
    def encoder(encoder):
        """Return hash object with custom encoder.
        """
        return Hash(encoder=encoder)

    def __call__(self, *args, **kwargs):
        """Return hash for anything that is pickle-able.
        """
        return hashlib.sha1(self._encoder.dumps([args, kwargs])).hexdigest()


class StashValueFound(Exception):
    """Exception when stashed value
    was not found in stash.
    """
    pass


class stashed:
    """Context manager for stashed values.
    """
    class encoder:
        """Available encoders.
        """
        pass

    def __init__(self, name, id=None, output=None, path=None,
            encoder=None):
        """Stash value representation to a stored stash.

        Stash files have format:

            <test file name>.<id>.stash

        :param name: name of the stashed value inside the stash file
        :param id: custom stash id, default: None
        :param output: function to output the representation of the value
        :param path: custom stash path, default: `./stash`
        :param encoder: custom encoder for the value, default: json
        """
        self.name = varname(name)
        self.encoder = encoder if encoder is not None else stashed.encoder.json
        self.output = output
        self._was_empty = True

        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)

        filename = os.path.basename(frame_info.filename)
        if id is not None:
            filename += "." + str(id).lower()
        filename += ".stash"

        if path is None:
            path = os.path.join(os.path.dirname(frame_info.filename), "stash")

        self.filename = os.path.join(path, filename)

        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(self.filename):
            stash_module = SourceFileLoader("stash", self.filename).load_module()
            if hasattr(stash_module, self.name):
                self._value = self.encoder.loads(getattr(stash_module, self.name))
                self._was_empty = False

    def __skip__(self, *args):
        sys.settrace(self._trace)
        raise StashValueFound()

    def __enter__(self):
        if hasattr(self, "_value"):
            self._trace = sys.gettrace()
            sys.settrace(self.__skip__)

        return self

    def __call__(self, value):
        """Stash value representation.
        """
        if hasattr(self, "_value"):
            raise ValueError("value already set")

        self._value = value

        with open(self.filename, "a") as fd:
            try:
                repr_value = repr(self.encoder.dumps(value))
            except:
                raise ValueError("can't be encoded")

            if self.output:
                self.output(repr_value)

            fd.write(f"""{self.name} = {repr_value}\n\n""")

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_value is not None:
            if isinstance(exc_value, StashValueFound):
                return True
            return False

    @property
    def was_empty(self):
        """Return True if stash was empty.
        """
        return bool(self._was_empty)

    @property
    def value(self):
        """Set stashed value.
        """
        if hasattr(self, "_value"):
            return self._value
        raise ValueError("not found")


class FilePath(stashed):
    """Stashed file specified by a filepath.
    """
    def __init__(self, name, id=None, path=None):
        """Stash value that contains a path to a file.

        The file is copied and stashed as:

            <name>

        :param name: name of the stashed file specified by file path
        :param id: custom stash id, default: None
        :param path: custom stash path, default: `./stash`
        """
        self.name = name
        self._was_empty = True

        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)

        filename = f"{self.name}"
        if id is not None:
            filename += f".{id}"
        filename = make_filename(filename)

        if path is None:
            path = os.path.join(os.path.dirname(frame_info.filename), "stash")

        self.filename = os.path.join(path, filename)

        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(self.filename):
            self._value = self.filename
            self._was_empty = False

    def __call__(self, value):
        """Stash filepath value.
        """
        if hasattr(self, "_value"):
            raise ValueError("value already set")

        if value != self.filename:
            if os.path.exists(self.filename):
                raise FileExistsError("filename already in stash")

            with open(self.filename, mode="wb") as dst:
                with open(value, mode="rb") as src:
                    while True:
                        data = src.read(65536)
                        if not data:
                            break
                        dst.write(data)

        self._value = self.filename


class NamedFile(stashed):
    """Stashed named file.
    """
    def __init__(self, name, mode="rb", id=None, path=None):
        """Stash a named file object.

        The file is copied and stashed as:

            <os.path.basename(name)>

        :param name: name of the file object to be stashed
        :param mode: file mode, default: `rb`
        :param id: custom stash id, default: None
        :param path: custom stash path, default: `./stash`
        """
        self.name = name
        self.mode = mode
        self._was_empty = True

        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)

        filename = f"{self.name}"
        if id is not None:
            filename += f".{id}"
        filename = make_filename(filename)

        if path is None:
            path = os.path.join(os.path.dirname(frame_info.filename), "stash")

        self.filename = os.path.join(path, filename)

        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(self.filename):
            self._value = self.filename
            self._was_empty = False

    def __call__(self, file_object):
        """Stash file object.
        """
        if hasattr(self, "_value"):
            raise ValueError("value already set")

        if file_object.name != self.filename:
            if os.path.exists(self.filename):
                raise FileExistsError("filename already in stash")

            file_object.flush()

            with open(self.filename, mode="wb") as dst:
                with open(file_object.name, mode="rb") as src:
                    while True:
                        data = src.read(65536)
                        if not data:
                            break
                        dst.write(data)

        self._value = self.filename

    @property
    def value(self):
        if hasattr(self, "_value"):
            return open(self._value, mode=self.mode)
        raise ValueError("not found")


# available encoders
stashed.encoder.json = json
stashed.encoder.marshal = marshal
stashed.encoder.jsonpickle = jsonpickle
stashed.encoder.pickle = pickle

# set custom stash types
stashed.filepath = FilePath
stashed.namedfile = NamedFile

# set hash
stashed.hash = Hash()
