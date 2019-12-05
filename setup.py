# -*- coding: utf-8 -*-

"""setup.py: setuptools control."""


import re
from setuptools import setup, find_packages

project_name = "MTGDeckConverter"
script_file = "{project_name}/constants.py".format(project_name=project_name)
description = "Convert digital Magic The Gathering (R) deck lists between formats."

with open(script_file, "r", encoding="utf-8") as opened_script_file:
    version = re.search(
        r"""^__version__\s*=\s*"(.*)"\s*""",
        opened_script_file.read(),
        re.M
        ).group(1)


with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name=project_name,
    packages=find_packages(exclude=["tests"]),
    # add required packages to install_requires list
    # install_requires=["package", "package2"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pyhamcrest", "pyfakefs"],
    test_suite="pytest",
    entry_points={
        "console_scripts": [
            "{project_name} = {project_name}.{project_name}:main".format(project_name=project_name)
        ]
    },
    version=version,
    description=description,
    long_description=long_description,
    python_requires=">=3.7",
    author="Thomas Hess",
    author_email="thomas.hess@udo.edu",
    url="https://github.com/luziferius/MTGDeckConverter",
    license="GPLv3+",
    # list of classifiers: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Environment :: Console',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'Topic :: Games/Entertainment',
    ],
)
