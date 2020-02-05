import subprocess
from typing import List
import re
import asyncio

import click

from processor import process


GIT_URL_REGEX = re.compile(
    "((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?"
)


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
@click.argument("urls", nargs=-1)
def migra(owner: str, file: click.File, urls: List[str]):

    if not check_if_installed("git") or not check_if_installed("hub"):
        return

    # Filter out invalid URLs and join file and args URLs
    urls = list(filter(validate_git_url, urls))
    urls += list(filter(validate_git_url, file.read().splitlines()))
    # Removes duplicates
    urls = list(set(urls))

    # Starts processing repositories
    asyncio.run(process(owner, urls))


if __name__ == "__main__":
    migra()
