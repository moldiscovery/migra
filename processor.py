from typing import Dict
import asyncio
import os


async def worker(repo_owner: str, q: asyncio.Queue):
    (repo_name, repo_url) = await q.get()
    print(f"Started processing {repo_name}")

    try:
        # Check if repository with same name already exists on GitHub
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"git ls-remote --exit-code {repo_url}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if proc.returncode == 0:
            raise Exception(
                f"Stopped processing {repo_name}: repo with same name already exists"
            )

        # Clones repo
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"git clone --mirror {repo_url}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        (_, stderr) = await proc.communicate()

        repo_folder: str = f"{repo_name}.git"

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
async def process(repo_owner: str, repos: Dict[str, str]):
    # Create a processing queue
    q = asyncio.Queue()
    for name, url in repos.items():
        q.put_nowait((name, url))

    # Creates a task for each repo
    tasks: List[asyncio.Task] = []
    for _ in repos:
        task = asyncio.create_task(worker(repo_owner, q))
        tasks.append(task)

    # Waits for the whole queue to finish processing
    await q.join()

    # Cancels all tasks
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks)
