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
import json
import os
import pickle

from testflows.core import *
from testflows.asserts import error, raises
from testflows.stash import stashed

class SimpleClass:
    def __init__(self):
        self.x = 1

@TestOutline(Scenario)
@Examples("name value", [
    ("str", "hello there", Name("str")),
    ("int", 1234, Name("int")),
    ("float", 12345.3234234, Name("float")),
    ("dict", {"a": "b"}, Name("dict")),
    ("list", [1, "a", 3.3], Name("list")),
    ("tuple", (-1, "hello", {"a": 1}), Name("tuple")),
    ("class", SimpleClass, Name("class")),
    ("object", SimpleClass(), Name("object"))
])
def check_value(self, name, value, encoder=None):
    """Check stashing some value.
    """
    if encoder is None:
        encoder = self.context.encoder

    name = f"{name}-{encoder.__name__}"

    with stashed(name, encoder=encoder) as stash:
        stash(value)

    assert stash.value == value, error()


@TestScenario
def check_empty_with_clause(self):
    with stashed("empty with") as stash:
        pass

    with raises(ValueError):
        stash.value

@TestScenario
def check_filepath(self):
    """Check stashing a value that contains a path to a file.
    """
    with stashed.filepath("my_file.txt") as stash:
        note("creating new file")
        with open("my_file.txt", mode="w") as fd:
            fd.write("file data")
        stash(fd.name)
        os.remove("my_file.txt")

    assert stash.value == "tests/stash/my_file.txt", error()

    with open(stash.value, mode="r") as fd:
        data = fd.read()

    assert data == "file data", error()


@TestScenario
def check_namedfile(self):
    """Check stashing a named file object.
    """
    with stashed.namedfile("my_namedfile.txt") as stash:
        note("creating new file")
        with open("my_file.txt", mode="w") as fd:
            fd.write("file data")
            stash(fd)
        os.remove("my_file.txt")

    assert stash.value.name == "tests/stash/my_namedfile.txt", error()

    with stash.value as fd:
        data = fd.read()

    assert data == b"file data", error()

@TestOutline(Suite)
@Examples("encoder", [
    (json, Name("json")),
    (pickle, Name("pickle"))
])
def check_values(self, encoder):
    """Check stashing values using different encoders.
    """
    self.context.encoder = encoder
    Scenario(run=check_value)


@TestModule
def regression(self):
    """TestFlows - Stash regression suite.
    """
    #Suite(run=check_values)
    Scenario(run=check_empty_with_clause)
    Scenario(run=check_filepath)
    Scenario(run=check_namedfile)


if main():
    Module(run=regression)
