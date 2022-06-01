# [TestFlows.com Open-Source Software Testing Framework] Stash

**The `testflows.stash` module is still work in progress and is currently under development.
Please use it only for reference.**

# Why

Allows to stash values or files that are generated during test program execution
that could be reused on the next test program run.

# Usage

Use **stashed** context manager to stash a value.
If the value identified by name is found inside the stash
then the code within the **with** block is not executed.

## Example

Here is an example how to use `testflows.stash` module
and the `stashed` context manager to stash a value
returned by a function that takes a non trivial time to execute.

> example1.py
```python
import time
from testflows.stash import stashed

def generate_value():
    print("Generating a value that takes a long time...")
    time.sleep(10)
    return "my generated value"

with stashed("value") as stash:
   stash(generate_value())

print(stash.value)
```

In this example, we simulate the work done by the function using
`time.sleep(10)`. The stashed value is identified by the `name`
argument passed when creating an instance of the stash using the
`stashed()` context manager.

On the first run, when the value is not in a stash
the code within the **with** block is executed where the value
to be stashed is added by calling `stash` instance with the value
to be stashed. In this case, the result of the `generated_value()`
function.

```bash
$ python3 example1.py
Generating a value that takes a long time...
my generated value
```

Note that `stash` folder will be created in the same directory as the source file.

```bash
$ find
./stash
./stash/example1.py.stash
./example1.py
```

The `stash` folder will contain a file that stores the stashed value by using the name specified
upon creation of the stash instance. The name of the stash file will have the same prefix as the
original source file.

In general, stash file name format is defined as

```
<source file name>.<id>.stas
```

The content of the file will have the following

```bash
$ cat ./stash/example1.py.stash 
value = '"my generated value"'
```

On the second run, the value is found in a stash and the body of the
**with** block is skipped and the `generated_value()` is not called
and the stashed value is available using the `stash.value`
where `stash` is the instance of the `stashed()` context manager.

```bash
$ python3 example1.py
my generated value
```

## `stashed()`

The `stashed` context manager can take the following arguments.

```python
stashed(name, id=None, output=None, path=None, encoder=None, use_stash=True)
```

where

* `name` name of the stashed value inside the stash file
* `id` custom stash id, default: `None`
* `output` function to output the representation of the value
* `path` custom stash path, default: `./stash`
* `encoder` custom encoder for the value, default: `json`
* `use_stash` use stash, default: `True`

[TestFlows.com Open-Source Software Testing Framework]: https://testflows.com

