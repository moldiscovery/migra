import subprocess
from typing import List, Dict
import re
import asyncio

import click

from processor import process


GIT_URL_REGEX = re.compile(
    "((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?"
)
REPO_NAME_REGEX = re.compile("/(.*)\.git/?$")


def check_if_installed(executable: str) -> bool:
    proc: subprocess.CompletedProcess = subprocess.run(
        ["which", executable], capture_output=True
    )
    if proc.returncode != 0:
        click.echo(f"{executable} is not installed or in PATH", err=True)
        return False
    return True


def validate_git_url(url: str) -> bool:
    return GIT_URL_REGEX.fullmatch(url)


@click.command()
@click.option("-o", "--owner", "owner", required=True, type=str)
@click.option("-f", "--file", "file", required=False, type=click.File("r"))
@click.option("-s", "--submodule-from", "submodule_from", required=False, type=str)
@click.argument("urls", nargs=-1)
def migra(
    owner: str, file: click.File, urls: List[str], submodule_from: str,
):

    if not check_if_installed("git") or not check_if_installed("hub"):
        return

    # Filter out invalid URLs and join file and args URLs
    urls = list(filter(validate_git_url, urls))
    urls += list(filter(validate_git_url, file.read().splitlines()))
    # Removes duplicates
    urls = list(set(urls))

    names: Dict[str, List[str]] = {}
    # Assumes a match is always found
    for url in urls:
        match = REPO_NAME_REGEX.search(url)
        name = match.group(1)
        if name in names:
            names[name].append(url)
        else:
            names[name] = [url]

    # Removes repositories with same name
    duplicates: Dict[str, List[str]] = {k: v for k, v in names.items() if len(v) > 1}
    repos: Dict[str, str] = {k: v[0] for k, v in names.items() if len(v) == 1}

    # Warn users that duplicates won't be processed
    if len(duplicates) > 0:
        print("Skipping repositories with same name:")
        for name, repo_urls in duplicates.items():
            print(f"{name}")
            for url in repo_urls:
                print(f"    {url}")

    # Starts processing repositories
    asyncio.run(process(owner, repos, submodule_from))


if __name__ == "__main__":
    migra()
