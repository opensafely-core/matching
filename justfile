export VIRTUAL_ENV  := env_var_or_default("VIRTUAL_ENV", ".venv")

export BIN := VIRTUAL_ENV + if os_family() == "unix" { "/bin" } else { "/Scripts" }
export PIP := BIN + if os_family() == "unix" { "/python -m pip" } else { "/python.exe -m pip" }

export DEFAULT_PYTHON := if os_family() == "unix" { "python3.8" } else { "python" }


# list available commands
default:
    @"{{ just_executable() }}" --list


# clean up temporary files
clean:
    rm -rf .venv


# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    set -euo pipefail

    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-$DEFAULT_PYTHON}

    # create venv and install latest pip compatible with pip-tools
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install pip==25.0.1; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    $BIN/pip-compile --allow-unsafe --output-file={{ dst }} {{ src }} {{ args }}


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev *args: (_compile 'requirements.dev.in' 'requirements.dev.txt' args)


_install env:
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.{{ env }}.txt -nt $VIRTUAL_ENV/.{{ env }} || exit 0

    $PIP install -r requirements.{{ env }}.txt
    touch $VIRTUAL_ENV/.{{ env }}


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: requirements-dev (_install 'dev')

# upgrade dev dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true "{{ just_executable() }}" requirements-{{ env }} $opts


# Upgrade all dev dependencies.
# This is the default input command to update-dependencies action
# https://github.com/bennettoxford/update-dependencies-action
update-dependencies:
    just upgrade dev

# *args is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the tests
test *args: devenv
    $BIN/coverage run --module pytest {{ args }}
    $BIN/coverage report || $BIN/coverage html


# run mypy type checker
mypy *ARGS: devenv
    $BIN/mypy osmatching/ tests/ "$@"


format *args=".": devenv
    $BIN/ruff format --check {{ args }}

lint *args=".": devenv
    $BIN/ruff check {{ args }}

# run the various dev checks but does not change any files
check: format lint mypy


# fix formatting and import sort ordering
fix: devenv
    $BIN/ruff check --fix .
    $BIN/ruff format .


# Run the CLI tool with test data by default
run cases="tests/test_data/fixtures/input_cases.csv" controls="tests/test_data/fixtures/input_controls.csv" config="tests/test_data/fixtures/config.json": devenv
    $BIN/match --cases {{ cases }} --controls {{ controls }} --config {{ config }}
    
