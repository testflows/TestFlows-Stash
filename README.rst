`TestFlows.com Open-Source Software Testing Framework`_ Stash
=================================================================

**The `testflows.stash` module is still work in progress and is currently under development.
Please use it only for reference.**

Why
***

Allows to stash values or files that are generated during test program execution
that could be reused on the next test program run.

Usage
*****

Use **stashed** context manager to stash a value.
If the value identified by name is found inside the stash
then the code within the **with** block is not executed.

.. code-block:: python

    from testflows.stash import stashed

    def generate_value():
        return "my generated value"

    with stashed("value") as stash:
       stash(generate_value())

    print(stash.value())


.. _`TestFlows.com Open-Source Software Testing Framework`: https://testflows.com
