# Project structure

`eulertools` can be invoked from everywhere inside the project, as it
recursively looks for the project root. The project root is marked by
the existence of a `.euler` directory. The required files and directories
inside it are:

- `.euler/euler.toml`
- `.euler/statements/<problem_name>.toml` for every problem

The problem name

## `euler.toml`

The project can be configured using a TOML file, called `euler.toml`,
inside the `.euler` directory.

Also, json and yaml file types are allowed, and the type is chosen from
the suffix of the file.

Each language is a section `[language.<language_name>]`, with the
following fields:

- extension: \[optional\] the filename extension for the problems solved
  in this language. Defaults to `./<language_name>`
- path: \[optional\] the path (relative to the project root)
  of the language solution. Defaults to `./<language_name>`
- runner: the path (relative to the project root) of the solution runner

There is a section called `$meta`, that allows to add some info for `eulertools` themselves.
At the moment, the only field that is used is `__version__`, and specifies the min `eulertools`
version to be used.

```toml linenums="1" title="euler.toml"
["$meta"]
version = "3.0"

[languages.java]
runner = "java/out/release/runner"

[languages.rust]
extension = "rs"
runner = "rust/out/release/runner"

["languages.c++"]
extension = "cpp"
path = "cpp"
runner = "cpp/cli/runner"
```

## Problem runner

the runner is a cli app that runs the problems for a specific language. It should be able to run with the
following positional arguments:

```console
user@localhost $ <runner> <problem_name> <times>
```

This command runs the problem named `problem_name` `<times>` times.
It expects that each run returns a pair of lines in the following format:

```console linenums="1"
Time <response_key> <timing in ns>
Answer <response_key> <answer>
```

The `response_key` is used to differentiate between different test cases.

A simple program runner in python can look like:

```py linenums="1" title="Python runner"
#!/usr/bin/env python
from argparse import ArgumentParser, Namespace
from importlib import import_module


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("problem")
    parser.add_argument("times", type=int)
    return parser.parse_args()


def main() -> None:
    options = parse_args()
    times = options.times
    for _ in range(times):
        module = f"solutions.{options.problem}"
        import_module(module).run()


if __name__ == "__main__":
    main()
```

## Statements directory

The `.euler` directory should have a subdirectory named `statements`, and inside it, it should be a file
for each problem, using the name `<problem_name>.toml`. The runner will use this to find which problems
have been solved. The file must have a table (even empty) for every language that is needed. Furthermore,
there are two required sections if the `euler generate` or `euler statement` are to be used.

For `euler statement`, the following toml tables are required:

```toml title="p0001.toml"
[common]
id = "1"
title = "Two Sum"
description = """
Given an array of integers, return indices of the two numbers such that they
add up to a specific target.
You may assume that each input would have exactly one solution, and you may not
use the same element twice.
"""
hint = """
For better than O(n^2) complexity, keep a dictionary of the complements.
"""
```

## Generate-specific structure

`eulertools` can generate new solution files based on a template. In order to use this, the following structure is
needed.

There should be a `.euler/templates/<language_name>.jinja` file. Also, the `.euler/statements/<problem_name>.toml`
needs to have a toml table named `<language_name>` to that will be treated as the context of the solution. When the solution
is generated, it will create a file in the `<language_path>/src/solutions` with the name `<language_name>.<language_extension>`.

For the above problem an example python template and toml table are the following:

```jinja title="solution.jinja"
from time import perf_counter_ns


class Solution:
    def {{method}}(self{% for arg in args %}, {{arg}}: {{types.get(arg)}}{% endfor %}) -> {{rtype}}:
        pass


def proxy({% for arg in args %}{{arg}}: {{types.get(arg)}}, {% endfor %}response_key: int) -> None:
    solution = Solution()
    begin = perf_counter_ns()
    answer = solution.{{method}}({{args|join(", ")}})
    end = perf_counter_ns()
    print(f"Time {response_key} {end - begin}")
    print(f"Answer {response_key} {answer}")


def run() -> None:
    proxy(..., response_key=1)
    proxy(..., response_key=1)
```

```toml title="p0001.toml"
[python]
method = "twoSum"
args = [
    "nums",
    "target",
]
types = { nums = "list[int]", target = "int" }
rtype = "list[int]"
```

## General considerations

It is advised that the runner is importing the solution and runs it within the language, to
have the best timings. This will allow some optimisations with jit compilers to happen, and can
reveal issues with memory leaks.

A good idea is that there is a `run` method for each problem that is responsible for passing
the different test arguments to the actual runner. The `run` can be the only public method of the
problem. This will make it easier to have a similar format for all the languages that you'll attempt
to solve the problem.

The response_key can be any string that contains no spaces, but it's better to use an small integer.
It makes the debugging of a failed case easier, as it's one of the most readable id formats.
