
import os
from github import Github, Auth, GithubException
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("REPO_OWNER")
repo_name = os.getenv("REPO_NAME")
base_branch = os.getenv("BASE_BRANCH", "main")
repair_branch = os.getenv("REPAIR_BRANCH", "ai-repair-week3")

github = Github(auth=Auth.Token(token))

try:
    repo = github.get_repo(f"{owner}/{repo_name}")

    # Get the latest commit from main
    main = repo.get_branch(base_branch)

    # Check whether the repair branch already exists
    try:
        repo.get_branch(repair_branch)
        print("Repair branch already exists:", repair_branch)

    except GithubException as error:
        if error.status != 404:
            raise

        # Create the new branch from main
        repo.create_git_ref(
            ref=f"refs/heads/{repair_branch}",
            sha=main.commit.sha
        )

        print("Repair branch created successfully!")

    print("Repository:", repo.full_name)
    print("Branch:", repair_branch)

finally:
    github.close()
