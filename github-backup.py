#!/usr/bin/python

import argparse
import requests
import datetime
import zipfile
import getpass
import shutil
import time
import json
import os

GITHUB_API = 'https://api.github.com'

GITHUB_URL_FMT = GITHUB_API + "/%s/%s/repos?page=%d&per_page=100"
REQUEST_TIMEOUT_SECS = 10.0

REPO_FORK = 'fork'
REPO_SOURCE = 'source'
REPO_ALL = 'all'

repotypes = [REPO_SOURCE, REPO_FORK, REPO_ALL]

# So we can use 'input()' in python 2 and 3...
try:
    input = raw_input
except NameError:
    pass

def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M')

def get_creds_from_user():
    username = input('Github username: ')
    password = getpass.getpass('Github password: ')
    return username, password

def get_oauth(username, password):
    payload = {"note": "github-backup_%s" % time.time()}
    res = requests.post('%s/authorizations' % GITHUB_API,
        auth=(username, password), data=json.dumps(payload))

    if res.status_code != 201:
        raise RuntimeError('Authorization failed, got %d from Github'
            % res.status_code)

    return res.json()['token']

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

def get_repos(url_fmt, name, isorg):
    repolist = []
    page = 1

    while True:
        request_url = (url_fmt % ("orgs" if isorg else "users", name, page))

        # Get next page
        response = requests.get(request_url, timeout=REQUEST_TIMEOUT_SECS)
        if response.status_code != 200:
            raise RuntimeError('Error: got response %d from %s'
                % (response.status_code, request_url))

        if not response.content:
            break

        loaded = response.json()

        if not loaded:
            break

        repolist.extend(loaded)
        page += 1

    return repolist

def main():
    parser = argparse.ArgumentParser(description='Backs up repositories from a'
        ' Github user account')
    parser.add_argument('name', type=str, help="Github user or org. name to "
        "back up repositories from")
    parser.add_argument('-o', '--org', action='store_true', dest='org',
        help="Indicates that the provided name is an organization name. If "
        "unset, the provided name will be treated as a username.")
    parser.add_argument('-c', '--compress', action='store_true', dest='compress',
        help="Compress downloaded repositories into .zip archive")
    parser.add_argument('-a', '--auth', action='store_true', dest='auth',
        help="Enter Github username/password interactively (hides password)")
    parser.add_argument('-u', '--username', dest="username",
        help="Github username")
    parser.add_argument('-p', '--password', dest="password",
        help="Github password")
    parser.add_argument('-f', '--outfile', dest="outfile",
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

    url_fmt = GITHUB_URL_FMT
    uname, pwd = None, None

    if args.auth:
        uname, pwd = get_creds_from_user()
    elif args.username and args.password:
        uname, pwd = args.username, args.password

    if uname and pwd:
        url_fmt += '&access_token=' + get_oauth(uname, pwd)

    # Get list of user/org repos through github API
    repolist = get_repos(url_fmt, args.name, args.org)

    default_dirname = 'github_%s_%s_%s' % (args.name, args.repotype, timestamp())

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
