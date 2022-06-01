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
import os

from testflows.core import *
from testflows.asserts import error, raises
from testflows.stash import stashed


class SimpleClass:
    def __init__(self):
        self.x = 1

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.x == self.x


@TestOutline
@Examples(
    "name value",
    [
        ("str", "hello there", Name("str")),
        ("int", 1234, Name("int")),
        ("float", 12345.3234234, Name("float")),
        ("dict", {"a": "b"}, Name("dict")),
        ("list", [1, "a", 3.3], Name("list")),
        ("tuple", (-1, "hello", {"a": 1}), Name("tuple")),
        ("class", SimpleClass, Name("class")),
        ("object", SimpleClass(), Name("object")),
    ],
)
def check_value(self, name, value, encoder=None, use_stash=None):
    """Check stashing some value."""
    if encoder is None:
        encoder = self.context.encoder
    if use_stash is None:
        use_stash = self.context.use_stash

    name = f"{name}-{encoder.__name__}"

    with stashed(name, encoder=encoder, use_stash=use_stash) as stash:
        stash(value)

    assert stash.value == value, error()


@TestScenario
def check_empty_with_clause(self):
    with stashed("empty with") as stash:
        pass

    with raises(ValueError):
        stash.value


@TestScenario
def check_filepath(self, use_stash=True):
    """Check stashing a value that contains a path to a file."""
    with stashed.filepath("my_file.txt", use_stash=use_stash) as stash:
        note("creating new file")
        with open("my_file.txt", mode="w") as fd:
            fd.write("file data")
        stash(fd.name)
        if stash.is_used:
            os.remove("my_file.txt")

    if use_stash:
        assert stash.value == "tests/stash/my_file.txt", error()
    else:
        assert stash.value == "my_file.txt", error()

    with open(stash.value, mode="r") as fd:
        data = fd.read()

    if not use_stash and self.flags & PARALLEL:
        assert data in ("file data", ""), error()
    else:
        assert data == "file data", error()


@TestScenario
def check_namedfile(self, use_stash=True):
    """Check stashing a named file object."""
    with stashed.namedfile("my_namedfile.txt", use_stash=use_stash) as stash:
        note("creating new file")
        with open("my_file.txt", mode="w") as fd:
            fd.write("file data")
            stash(fd)
        if stash.is_used:
            note("removing original file")
            os.remove("my_file.txt")

    if use_stash:
        assert stash.value.name == "tests/stash/my_namedfile.txt", error()
    else:
        assert stash.value.name == "my_file.txt", error()

    with stash.value as fd:
        data = fd.read()

    if not use_stash and self.flags & PARALLEL:
        assert data in (b"file data", b""), error()
    else:
        assert data == b"file data", error()


@TestScenario
def check_namedfile_parallel(self, count=100, use_stash=True):
    """Check stashing a named file object in parallel."""
    stash_file = "tests/stash/my_namedfile.txt"

    with Given("removing stash file if exists"):
        if os.path.exists(stash_file):
            os.remove(stash_file)

    with When("I try to access stash in parallel"):
        for i in range(count):
            By(f"try #{i}", test=check_namedfile, parallel=True)(use_stash=use_stash)


@TestScenario
def check_filepath_parallel(self, count=100, use_stash=True):
    """Check stashing a value that contains a path to a file in parallel."""
    stash_file = "tests/stash/my_file.txt"

    with Given("removing stash file if exists"):
        if os.path.exists(stash_file):
            os.remove(stash_file)

    with When("I try to access stash in parallel"):
        for i in range(count):
            By(f"try #{i}", test=check_filepath, parallel=True)(use_stash=use_stash)


@TestScenario
def check_namedfile_parallel_no_stash(self, count=100):
    """Check stashing a named file object in parallel when use_stash=False."""
    check_namedfile_parallel(use_stash=False)


@TestScenario
def check_filepath_parallel_no_stash(self, count=100):
    """Check stashing a value that contains a path to a file in parallel when use_stash=False."""
    check_filepath_parallel(use_stash=False)


@TestOutline(Scenario)
@Examples(
    "encoder",
    [
        (stashed.encoder.json, Name("json")),
        (stashed.encoder.marshal, Name("marshal")),
        (stashed.encoder.pickle, Name("pickle")),
        (stashed.encoder.jsonpickle, Name("jsonpickle")),
    ],
)
def check_values(self, encoder):
    """Check stashing values using different encoders."""
    self.context.encoder = encoder
    self.context.use_stash = True

    Scenario(run=check_value)


@TestOutline(Scenario)
@Examples(
    "encoder",
    [
        (stashed.encoder.json, Name("json")),
        (stashed.encoder.marshal, Name("marshal")),
        (stashed.encoder.pickle, Name("pickle")),
        (stashed.encoder.jsonpickle, Name("jsonpickle")),
    ],
)
def check_values_no_stash(self, encoder):
    """Check stashing values using different encoders
    when use_stash=False and stash is not used.
    """
    self.context.encoder = encoder
    self.context.use_stash = False
    Scenario(run=check_value)


@TestScenario
def check_using_hash(self):
    """Check using stashed.hash to get a unique stash name."""
    with stashed(stashed.hash([1, 2, 3])) as stash:
        stash("hello there")

    value1 = stash.value

    with stashed(stashed.hash([1, 2, 3])) as stash2:
        stash2("hello there2")

    assert value1 == stash2.value, error()

    with stashed(stashed.hash([3, 2, 3])) as stash3:
        stash3("hello there2")

    assert stash3.value == "hello there2", error()


@TestModule
@XFlags(
    {
        "check values/json/check value/tuple": (SKIP, None),
        "check values/json/check value/class": (SKIP, None),
        "check values/json/check value/object": (SKIP, None),
        "check values/marshal/check value/class": (SKIP, None),
        "check values/marshal/check value/object": (SKIP, None),
    }
)
def regression(self):
    """TestFlows - Stash regression suite."""
    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    Module(run=regression)
