import asyncio
import re
import os

REPO_FOLDER_REGEX = re.compile("'(.*)'")


async def worker(repo_owner: str, q: asyncio.Queue):
    repo_url: str = await q.get()
    print(f"Started processing {repo_url}")

    try:
        # Clones repo
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"git clone --mirror {repo_url}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        (_, stderr) = await proc.communicate()

        match: re.Match = REPO_FOLDER_REGEX.search(stderr.decode())
        if match is None:
            raise Exception("Couldn't parse repo folder")

        repo_folder: str = match.group(1)
        repo_name: str = repo_folder[:-4]

        # Removes existing remote
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            "git remote remove origin",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=repo_folder,
        )
        await proc.wait()

        # Creates repository on GitHub
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"hub create -p {repo_owner}/{repo_name}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=repo_folder,
        )
        await proc.wait()

        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            "git push --mirror",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=repo_folder,
        )
        await proc.wait()

        # Removes local repository
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"rm -rf {repo_folder}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        print(f"{repo_name} migrated")

    except Exception as e:
        print(e)
    finally:
        q.task_done()


# Sets up and starts processing of git repositories
async def process(repo_owner: str, urls: str):
    # Create a processing queue
    q = asyncio.Queue()
    for url in urls:
        q.put_nowait(url)

    # Creates a task for each repo
    tasks: List[asyncio.Task] = []
    for _ in urls:
        task = asyncio.create_task(worker(repo_owner, q))
        tasks.append(task)

    # Waits for the whole queue to finish processing
    await q.join()

    # Cancels all tasks
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks)
