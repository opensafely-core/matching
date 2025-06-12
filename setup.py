import os

from setuptools import find_namespace_packages, setup


with open(os.path.join("osmatching", "VERSION")) as f:
    version = f.read().strip()

setup(
    name="opensafely_matching",
    version=version,
    packages=find_namespace_packages(exclude=["tests"]),
    url="https://github.com/opensafely/matching",
    description="Command line tool for matching cases to controls",
    author="OpenSAFELY",
    license="GPLv3",
    author_email="tech@opensafely.org",
    python_requires=">=3.8",
    install_requires=["pandas"],
    entry_points={"console_scripts": ["match=osmatching.__main__:main"]},
    classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"],
)
