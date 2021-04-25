#!/usr/bin/python3
#
# Copyright © 2020-2021 Samuel Holland <samuel@sholland.org>
# SPDX-License-Identifier: BSD-3-Clause
#

import logging
import requests
import sys

from argparse   import ArgumentParser
from hashlib    import sha1
from pathlib    import Path
from zlib       import compress

logger = logging.getLogger()


def write_object(repo_path, obj_kind, obj_id, obj_path, content):
    content = f'{obj_kind} {len(content)}\0'.encode('ascii') + content
    digest = sha1()
    digest.update(content)
    actual_id = digest.hexdigest()
    if not obj_id:
        obj_id = actual_id
    elif obj_id != actual_id:
        error = f'Bad digest for object {obj_path}: {obj_id} != {actual_id}'
        logger.error(error)
        raise ValueError(error)
    obj_file = repo_path / '.git' / 'objects' / obj_id[:2] / obj_id[2:]
    if obj_file.exists():
        return obj_id
    obj_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = obj_file.with_suffix('.tmp')
    with open(tmp_file, 'wb') as f:
        f.write(compress(content))
    tmp_file.rename(obj_file)
    return obj_id


def fetch(repo_path, api_url, ref, tree_hex=None, tree_path='/'):
    children = {}
    page = '1'

    while page:
        resp = requests.get(f'{api_url}/tree?path={tree_path}&ref={ref}&page={page}&per_page=100',
                            timeout=15.0)
        page = resp.headers['X-Next-Page']
        for entry in resp.json():
            mode = int(entry['mode'], base=8)
            id_h = entry['id']
            id_b = bytes.fromhex(id_h)
            name = entry['name']
            path = entry['path']

            logger.info('%s %s', id_h[:12], path)

            sort_key = name + '/' * (mode == 0o40000)
            tree_line = f'{mode:o} {name}\0'.encode('ascii') + id_b
            children[sort_key] = tree_line

            if entry['type'] == 'blob':
                blob = requests.get(f'{api_url}/blobs/{id_h}/raw', timeout=60.0).content
                write_object(repo_path, 'blob', id_h, path, blob)
            else:
                fetch(repo_path, api_url, ref, id_h, path)

    tree = b''.join(line for key, line in sorted(children.items()))
    id_h = write_object(repo_path, 'tree', tree_hex, tree_path, tree)

    if tree_hex is None:
        logger.info('%s %s', id_h[:12], tree_path)


def main(argv):
    parser = ArgumentParser()
    parser.add_argument('url', help='URL for GitLab Repositories API')
    parser.add_argument('repo', type=Path, help='Path to existing local git repository')
    parser.add_argument('ref', nargs='?', default='HEAD', help='git reference')
    args = parser.parse_args()
    fetch(args.repo, args.url, args.ref)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv)
