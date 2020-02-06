# Migra

Python script to migrate git repositories to GitHub.

## Requirements

These two MUST be installed to run the script.

* git
* [hub](hub)

## Installation

Run `pipenv install` to install requirements.

## Usage

After installing the requirements enter the virtual env with `pipenv shell`.

Before running the script make sure you configured `hub` with your GitHub credentials by setting `GITHUB_USER` and `GITHUB_PASSWORD` environment variables, otherwise you'll get prompted for them.

See [hub configuration](hub_config) for more info.

To run the script:

```
python migra.py --owner <user_or_organization> <git_urls>
```

`--owner`, or `-o`, is mandatory.

`user_or_organization` must be the name of an existing user or organization you have rights to create new repositories.

`git_urls` must be a list of urls of existing public git repositories, or private ones you have rights to read.

You can also pass a file that contains a list of git urls:

```
python migra.py --owner <user_or_organization> --file <path_to_file>
```

The file must contain one url per line, for example:

```
git@bitbucket.org:my_org/repo1.git
git@bitbucket.org:my_org/repo2.git
git@bitbucket.org:my_org/repo3.git
git@bitbucket.org:another_org/another_repo1.git
git@bitbucket.org:another_org/another_repo2.git
```

The newly created repositories on GitHub will all be **private**.

## WARNING

All repositories **MUST** have different names, we don't know what happens in case there are two or more repositories with equal name.

Existing repositories on GitHub might be **OVERWRITTEN** if they have identical names to repositories being migrated.


[hub]: https://github.com/github/hub
[hub_config]: https://hub.github.com/hub.1.html#configuration
