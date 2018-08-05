Github backup utility
---------------------

A simple pure-python script to back up repositories on a github
account. Works on Python 2x and 3x.

Install
=======

Clone this repository

::

    git clone https://github.com/eriknyquist/github-backup
    cd github-backup
    sudo install.sh

Usage
=====

Run ``github-backup -h`` to see all available options.

Clone all repositories from the specified user account:

::

    github-backup username

Clone only source repositories

::
    github-backup username -t source

Clone only forked repositories

::
    github-backup username -t fork

Clone all repositories (default)

::

    github-backup username -t all

Clone only source repositories and create a .zip archive

::

    github-backup username -t source -c

Clone all repositories and create .zip archive in specific directory (/home/erik):

::

    github-backup username -d /home/erik -c

Clone all repositories and create .zip archive with specific name (archive.zip)
in specific directory (/home/erik):

::

    github-backup username -d /home/erik -o archive.zip -c
