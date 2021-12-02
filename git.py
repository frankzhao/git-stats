import json
import logging
import os
import shutil
import subprocess
import tempfile
from json import JSONDecodeError
from typing import List, Union

from commit import Commit

logger = logging.getLogger('git')


def setup_git(config) -> dict:
    temp_dir = tempfile.mkdtemp(prefix='git_stats_')
    git_config = dict(temp_dir=temp_dir, repositories={})
    logger.info('Cloning into temp directory: %s', temp_dir)
    repo_config = dict()

    try:
        repos = config['repositories']
        for repo in repos:
            config: dict = dict()

            # Custom branch handling.
            if 'branch' in repo:
                config['branch'] = repo['branch']
            else:
                config['branch'] = 'master'

            if 'url' in repo:
                logger.info('Cloning: %s', repo['url'])
                cmd = ['git', 'clone', '--branch', config['branch'], repo['url'], os.path.join(temp_dir, repo['name'])]
                result = subprocess.run(cmd)
                if result.returncode > 0:
                    logger.error("Could not clone repository: %s, repo=%s", result.stderr, repo['url'])
                    cleanup_git(git_config)
                    exit(1)
                cmd = ['git', 'fetch']
                result = subprocess.run(cmd, cwd=os.path.join(temp_dir, repo['name']))
                if result.returncode > 0:
                    logger.error("Could not fetch repository: %s, repo=%s", result.stderr, repo['url'])
                    cleanup_git(git_config)
                    exit(1)
                config['path'] = os.path.join(temp_dir, repo['name'])
            else:
                config['path'] = repo['path']

            repo_config[repo['name']] = config

        git_config['repositories'] = repo_config
        return git_config
    except Exception as e:
        cleanup_git(git_config)
        raise e


def cleanup_git(git_config):
    logger.info("Cleaning up temp files.")
    shutil.rmtree(git_config['temp_dir'])


def list_git_tags(repo_path) -> List[str]:
    cmd = ['git', '--no-pager', 'tag']

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    if result.returncode > 0:
        logger.error("Error listing git tags: %s", result.stderr)
        return []

    return str(result.stdout).split()


def list_git_tags_per_repository(repo_path: str) -> dict:
    git_tags = {}
    for tag in filter(lambda t: t.startswith('v'), list_git_tags(repo_path)):
        git_tag = get_git_tag(repo_path, tag)
        git_tags[tag] = dict(commit=git_tag, date=git_tag.committer.date)
    return git_tags


def get_git_tag(repo_path, tag) -> Union[Commit, None]:
    print_format = '{%n  "commit": "%H",%n  "abbreviated_commit": "%h",%n  "tree": "%T",%n  "abbreviated_tree": "%t",%n  ' \
                   '"parent": "%P",%n  "abbreviated_parent": "%p",%n  "refs": "%D",%n  "encoding": "%e",%n  "subject": ' \
                   '"%s",%n  "sanitized_subject_line": "%f",%n  "body": "%b",%n  "commit_notes": "%N",%n  ' \
                   '"verification_flag": "%G?",%n  "signer": "%GS",%n  "signer_key": "%GK",%n  ' \
                   '"author": {%n    "name": "%aN",%n    "email": "%aE",%n    "date": "%aD"%n  },%n  ' \
                   '"committer": {%n    "name": "%cN",%n    "email": "%cE",%n    "date": "%cD"%n  }%n},'

    cmd = ['git', '--no-pager', 'show', '-q', tag, '--pretty=format:\'' + print_format + '\'']

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    if result.returncode > 0:
        logger.error("Error getting git tag: %s", result.stderr)
        return None

    # Hack to discard tag message before commit.
    start_idx = 0
    while str(result.stdout)[start_idx] != '{':
        start_idx += 1
    commit_str = str(result.stdout)[start_idx:-2]
    git_json = commit_str.replace('\'', '').replace('\n', '').replace('\t', ' ')
    logger.debug("Got git tag: %s", git_json)
    try:
        git_tag = json.loads(git_json)
    except JSONDecodeError as e:
        logger.error("Error parsing json: %s, got: %s", e, git_json)
        return None
    git_commit = Commit(**git_tag)
    logger.debug("Tag: %s at %s", tag, git_commit.committer.date)
    return git_commit


def get_git_log(repo_path, branch='master') -> List[Commit]:
    print_format = '{%n  "commit": "%H",%n  "abbreviated_commit": "%h",%n  "tree": "%T",%n  "abbreviated_tree": "%t",%n  ' \
                   '"parent": "%P",%n  "abbreviated_parent": "%p",%n  "refs": "%D",%n  "encoding": "%e",%n  ' \
                   '"sanitized_subject_line": "%f",%n  "body": "%b",%n  "commit_notes": "%N",%n  ' \
                   '"verification_flag": "%G?",%n  "signer": "%GS",%n  "signer_key": "%GK",%n  ' \
                   '"author": {%n    "name": "%aN",%n    "email": "%aE",%n    "date": "%aD"%n  },%n  ' \
                   '"committer": {%n    "name": "%cN",%n    "email": "%cE",%n    "date": "%cD"%n  }%n},'
    cmd = ['git', '--no-pager', 'log', branch, '--pretty=format:\'' + print_format + '\'']

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    if result.returncode > 0:
        logger.error("Error getting git reflog: %s", result.stderr)
        return []

    git_json = '[' + str(result.stdout[:-2]).replace('\'', '').replace('\n', '').replace('\t', ' ') + ']'
    logger.debug("Got git reflog: %s", git_json)
    try:
        git_log = json.loads(git_json)
    except JSONDecodeError as e:
        logger.error(e)
        logger.error(git_json)
        return []

    logger.info("Found %s commits in branch '%s'", len(git_log), branch)
    git_commits = []
    for e in git_log:
        git_commits.append(Commit(**e))

    return git_commits
