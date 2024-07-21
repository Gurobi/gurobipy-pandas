# Run as a pre-build step on RTD. Use a fine-grained personal access token
# with no extra permissions (for public repos).
#
# Local test:
#
#   READTHEDOCS_GIT_COMMIT_HASH=$(git rev-parse HEAD) READTHEDOCS=True \
#     GH_API_TOKEN=<TOKEN> python artifacts.py

import os
import pathlib
import sys

import requests

docs_source = pathlib.Path(__file__).parent.parent.joinpath("docs/source").resolve()
target = docs_source.joinpath("artifact/gurobipy-pandas-examples.zip")


def download_executed_notebooks(runs_url, gh_token, head_sha):
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {gh_token}",
    }

    params = {"head_sha": head_sha}
    response = requests.get(runs_url, headers=headers, params=params)
    response.raise_for_status()
    runs_data = response.json()

    for run in runs_data["workflow_runs"]:
        print("Run id={id} event={event} status={status} path={path}".format(**run))

        if run["path"] != ".github/workflows/main.yml":
            continue
        if run["status"] != "completed":
            continue
        if run["conclusion"] != "success":
            continue

        artifacts_url = run["artifacts_url"]
        response = requests.get(artifacts_url, headers=headers)
        response.raise_for_status()
        artifacts_data = response.json()

        for artifact in artifacts_data["artifacts"]:
            print("Artifact id={id} name={name}".format(**artifact))

            if artifact["name"] != "notebook-examples":
                continue

            download_url = artifact["archive_download_url"]
            response = requests.get(download_url, headers=headers)
            response.raise_for_status()

            os.makedirs(target.parent, exist_ok=True)
            if target.exists():
                target.unlink()
            with target.open("wb") as outfile:
                outfile.write(response.content)

            print(f"Downloaded {target}")
            return True

    return False


if not os.environ.get("GH_API_TOKEN"):
    # Pull requests run in this configuration
    print("No API token, can't fetch artifacts. Continuing build with dummy file.")
    os.makedirs(target.parent, exist_ok=True)
    with target.open("wb") as outfile:
        outfile.write(b"")
    sys.exit(0)

success = download_executed_notebooks(
    runs_url="https://api.github.com/repos/Gurobi/gurobipy-pandas/actions/runs",
    gh_token=os.environ["GH_API_TOKEN"],
    head_sha=os.environ["READTHEDOCS_GIT_COMMIT_HASH"],
)

if success:
    # Success, RTD build can continue
    print("Artifact retrieval succeeded.")
    sys.exit(0)
else:
    # Cancels the RTD build (rely on a later trigger to rebuild)
    print("Aritfact not found. Cancelling build.")
    sys.exit(183)

# Any exception would be a build failure
