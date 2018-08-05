import argparse
import requests
import datetime
import zipfile
import time
import json
import os

GITHUB_URL_FMT = "https://api.github.com/users/%s/repos?per_page=100\&page=%d"

REPO_FORK = 'fork'
REPO_SOURCE = 'source'
REPO_ALL = 'all'

repotypes = [REPO_SOURCE, REPO_FORK, REPO_ALL]

def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M')

def zipdir(path, zipname):
    with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zh:
    	for root, dirs, files in os.walk(path):
            for filename in files:
                zh.write(os.path.join(root, filename))

def clone(repo_url, dirname):
    code = os.system('git clone %s %s' % (repo_url, dirname))
    if code != 0:
        raise OSError("Can't clone %s, status %d" % (repo_url, code))

def should_clone(repotype, is_fork):
    if repotype == REPO_ALL:
        return True

    if repotype == REPO_FORK:
        return is_fork

    return not is_fork

def main():
    parser = argparse.ArgumentParser(description='Clone all repositories from a'
        ' user account')

    parser.add_argument('user', type=str, help="Github user name")
    parser.add_argument('-o', '--outfile', dest="outfile",
        help="Name of .zip archive to write")
    parser.add_argument('-t', '--type', default="source",
        dest="repotype", help="Select repo type to download. Valid values are "
        "%s." % repotypes)

    args = parser.parse_args()

    if args.repotype not in repotypes:
        raise ValueError("Invalid repo type '%s': valid values are %s"
            % (args.repotype, repotypes))

    # Get list of users repos through github API
    response = requests.get(GITHUB_URL_FMT % (args.user, 2))

    dirname = 'github_%s_%s_%s' % (args.user, args.repotype, timestamp())
    os.mkdir(dirname)

    for repo in json.loads(response.content):
        if should_clone(args.repotype, repo['fork']):
            clone(repo['clone_url'], os.path.join(dirname, repo['name']))

    if args.outfile:
        zipfile = os.path.splitext(args.outfile)[0]
    else:
        zipfile = dirname

    zipdir(dirname, zipfile + '.zip')

if __name__ == "__main__":
    main()
