# Notes for developers

## System requirements

### just

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
just dev_setup
```

## Tests
Run the tests with:
```
just test <args>
```
