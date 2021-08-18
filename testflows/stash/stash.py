# Copyright 2019 Katteli Inc.
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
import inspect
import textwrap

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


class StashValueFound(Exception):
    pass


class stashed:
    def __init__(self, name, *args, id=None, output=None, path=None, encoder=json):
        """Stash value representation to a stored stash.
    
        Stash files have format:
    
            <test file name>.<id>.stash
    
        :param name: name of the stashed value inside the stash file
        :param id: custom stash id, default: None
        :param output: function to output the representation of the value
        :param path: custom stash path, default: `./stash`
        :paran encoder: custom stash encoder, default: `repr`
        """
        self.name = varname(name)
        self.encoder = encoder
        self.output = output
    
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
                self._value = encoder.loads(getattr(stash_module, self.name))


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
        self._value = value

        with open(self.filename, "a") as fd:
            try:
                repr_value = repr(self.encoder.dumps(value))
            except:
                raise ValueError("failed to get representation of the value being stashed")

            if self.output:
                self.output(repr_value)

            fd.write(f'''{self.name} = {repr_value}\n\n''')
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_value is not None:
            if isinstance(exc_value, StashValueFound):
                return True
            return False

    @property
    def value(self):
        if hasattr(self, "_value"):
            return self._value
        raise ValueError("stash value not found")


