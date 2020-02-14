from typing import Dict
import asyncio
import os


async def worker(repo_owner: str, submodule_from: str, q: asyncio.Queue):
    """
    Clones repository locally, if necessary updates submodules urls to new
    remote, creates new remote repository and pushes to it, when done deletes
    local repository.
    """
    (repo_name, repo_url) = await q.get()
    print(f"Started processing {repo_name}")

    try:
        # Check if repository with same name already exists on GitHub
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"hub api repos/{repo_owner}/{repo_name}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        if proc.returncode == 0:
            raise Exception(
                f"Stopped processing {repo_name}: repo with same name already exists for this owner on GitHub"
            )

        # If we don't need to update submodules we mirror the repository so it's faster
        mirror: str = "--mirror" if not submodule_from else ""

        # Clones repo
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            f"git clone {mirror} {repo_url}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        repo_folder: str = f"{repo_name}.git" if mirror else repo_name

        # No need to update submodules so skip the whole step
        if not mirror:
            proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
                "git branch -r",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=repo_folder,
            )
            (stdout, _) = await proc.communicate()

            # Get all remote branches of current repo
            branches = set()
            for line in stdout.decode().splitlines():
                if "origin/HEAD" in line:
                    line: str = line.split("->")[1]
                branch = line.replace("origin/", "").strip()
                branches.add(branch)

            for branch in branches:
                # Checkout branch
                proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
                    f"git checkout {branch}",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    cwd=repo_folder,
                )
                await proc.wait()

                # No submodules in this branch
                if not os.path.exists(f"{repo_folder}/.gitmodules"):
                    continue

                # Replaces submodules URLs
                with open(f"{repo_folder}/.gitmodules", "r+") as f:
                    text = f.read()
                    # Nothing to replace here, skip this branch
                    if submodule_from not in text:
                        continue
                    text = text.replace(submodule_from, f"github.com:{repo_owner}")
                    f.seek(0)
                    f.write(text)
                    f.truncate()

                # Commit change
                proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
                    "git commit -a -m '[Migra] Updated submodules'",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    cwd=repo_folder,
                )
                await proc.wait()

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
async def process(repo_owner: str, repos: Dict[str, str], submodule_from: str):
    # Create a processing queue
    q = asyncio.Queue()
    for name, url in repos.items():
        q.put_nowait((name, url))

    # Creates a task for each repo
    tasks: List[asyncio.Task] = []
    for _ in repos:
        task = asyncio.create_task(worker(repo_owner, submodule_from, q))
        tasks.append(task)

    # Waits for the whole queue to finish processing
    await q.join()

    # Cancels all tasks
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks)
