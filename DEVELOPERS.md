# Notes for developers

## System requirements

### just[1]

Follow installation instructions from the [Just Programmer's Manual](https://just.systems/man/en/chapter_4.html) for your OS.

Add completion for your shell. E.g. for bash:
```
source <(just --completions bash)
```

Show all available commands
```
just #  shortcut for just --list
```


## Local development environment


Set up a local development environment with:
```
just devenv
```

## Tests
Run the tests with:
```
just test <args>
```


### Environments

A reusable action is run within a container,
which is created from a image,
which in turn is created from a repository.
As this is a Python reusable action, it is run within a Python container,
which is created from a Python image,
which in turn is created from the [opensafely-core/python-docker][] repository.

The Python container provides the reusable action with its production environment.
From a developer's perspective, the most important characteristic of the production environment is that it contains __Python 3.10__.
The next most important characteristic is that it contains the versions of the packages listed in [_v2/requirements.txt_][2] from the opensafely-core/python-docker repository.

Notice, however, that there are two sets of requirements files within this reusable action's repository:

* The versions of the packages listed in _requirements.prod.in_ are for local development
  and should mirror the production environment.
  In other words,
  the versions of the packages listed in _requirements.prod.in_
  should mirror the versions of the packages listed in _v2/requirements.txt_ from the opensafely-core/python-docker repository.

* The versions of the packages listed in _requirements.dev.in_ are for local development
  and need not mirror the production environment.


## Tagging a new version

This reusable action follows [Semantic Versioning, v2.0.0][3] and [semantic-release][4] conventions.

New tags are created automatically by the GitHub Actions `Tag new version` workflow when commits
are pushed to the `main` branch (i.e. when a pull request is merged to `main`). The tag created
depends on the commit messages included in the push.

A new __patch__ version is tagged if a commit is detected (since the previous tag) with a message 
prefixed with `fix`.

For example, a commit with the following message title would tag a new patch version when it is pushed to the `main` branch:

```
fix: a bug fix
```
If the current tag is `v0.0.1`, this will tag `v0.0.2`.

A new __minor__ version is tagged if a commit is detected with a message prefixed with `feat`.

For example, a commit with the following message title would tag a new minor version when it is pushed to the `main` branch:

```
feat: a new feature
```
If the current tag is `v0.0.1`, this will tag `v0.1.0`.


A new __major__ version is tagged if a commit is detected that has `BREAKING CHANGE` in its message body.
For example, a commit with the following message body would tag a new major version:

```
Remove a function

BREAKING CHANGE: Removing a function is not backwards-compatible.
```
If the current tag is `v0.0.1`, this will tag `v1.0.0`.

Whilst there are other prefixes besides `fix` and `feat`, they do not tag new versions.

[1]: https://github.com/casey/just/
[2]: https://github.com/opensafely-core/python-docker/blob/main/v2/requirements.txt
[3]: https://semver.org/spec/v2.0.0.html
[4]: https://github.com/semantic-release/semantic-release
[opensafely-core/python-docker]: https://github.com/opensafely-core/python-docker
