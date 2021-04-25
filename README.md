This is a horribly inefficient script for fetching a tree from a git repository
using the GitLab Repositories API. It is only useful if normal git access is
somehow broken.

See https://sholland.org/2021/git-clone-piece-by-piece/

Example usage:
```
$ mkdir my_repo
$ git -C my_repo init
$ python -m gitlab_fetch https://gitlab.example.com/api/v4/projects/12345/repository my_repo
INFO:root:af4ebd3233e5 .gitignore
INFO:root:6f5922c1d323 LICENSE.md
INFO:root:04823e70e2ca Makefile
INFO:root:ded0d3081976 README.md
INFO:root:bcd6e8b5186a /
$ git -C my_repo read-tree bcd6e8b5186a
$ git -C my_repo checkout-index -a
```
