#!/usr/bin/python

import argparse
import requests
import datetime
import zipfile
import shutil
import time
import json
import os

GITHUB_URL_FMT = "https://api.github.com/users/%s/repos?page=%d&per_page=100"

REPO_FORK = 'fork'
REPO_SOURCE = 'source'
REPO_ALL = 'all'

repotypes = [REPO_SOURCE, REPO_FORK, REPO_ALL]

def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M')

def zipdir(path, zipname):
    print('Creating %s...' % zipname)
    with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zh:
    	for root, dirs, files in os.walk(path):
            for filename in files:
                zh.write(os.path.join(root, filename),
                    os.path.relpath(os.path.join(root, filename),
                    os.path.join(path, '..')))

def clone(repo_url, dirname):
    code = os.system('git clone %s %s' % (repo_url, dirname.replace(' ', '\\ ')))
    if code != 0:
        raise OSError("Can't clone %s, status %d" % (repo_url, code))

def should_clone(repotype, is_fork):
    if repotype == REPO_ALL:
        return True

    if repotype == REPO_FORK:
        return is_fork

    return not is_fork

def main():
    parser = argparse.ArgumentParser(description='Backs up repositories from a'
        ' Github user account')

    parser.add_argument('user', type=str, help="Github user name")
    parser.add_argument('-c', '--compress', action='store_true', dest='compress',
        help="Compress downloaded repositories into .zip archive")
    parser.add_argument('-o', '--outfile', dest="outfile",
        help="Name of .zip archive to write")
    parser.add_argument('-d', '--directory', dest="outdir", default=".",
        help="Name of directory to clone repositories under")
    parser.add_argument('-t', '--type', default="source",
        dest="repotype", help="Select repo type to download. Valid values are "
        "%s." % repotypes)

    args = parser.parse_args()

    if args.repotype not in repotypes:
        raise ValueError("Invalid repo type '%s': valid values are %s"
            % (args.repotype, repotypes))

    repolist = []

    # Get list of users repos through github API
    page = 1
    while True:
        # Get next page
        response = requests.get(GITHUB_URL_FMT % (args.user, page))
        if not response.content:
            break

        loaded = response.json()

        if not loaded:
            break

        repolist.extend(loaded)
        page += 1

    default_dirname = 'github_%s_%s_%s' % (args.user, args.repotype, timestamp())

    dirname = args.outdir

    if not os.path.exists(dirname):
        os.mkdir(dirname)
    else:
        dirname = os.path.join(dirname, default_dirname)

    # Clone all suitable repos   
    for repo in repolist:
        if should_clone(args.repotype, repo['fork']):
            clone(repo['clone_url'], os.path.join(dirname, repo['name']))

    if not args.compress:
        return

    if args.outfile:
        zipfile = os.path.splitext(args.outfile)[0]
    else:
        zipfile = dirname

    # Create .zip archive
    zipdir(dirname, zipfile + '.zip')

    # Delete directory containing clones
    shutil.rmtree(dirname)

if __name__ == "__main__":
    main()
