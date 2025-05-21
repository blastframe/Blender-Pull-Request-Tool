#!/usr/bin/env python3
"""
Manage Blender pull requests and prune local branches.

Usage:
  - Fetch and checkout a pull request:
      ./pr_tool.py 12345

  - Specify a different repository:
      ./pr_tool.py 12345 --repo blender-manual

  - Prune local branches:
      ./pr_tool.py --prune

Make the script executable:
  chmod +x pr_tool.py
"""

import argparse
import json
import subprocess
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError

def run_cmd(cmd, check=True, capture_output=False):
    result = subprocess.run(cmd, shell=True, check=check, text=True, capture_output=capture_output)
    return result.stdout.strip() if capture_output else None

def fetch_pr_json(owner, repo, pr_number):
    url = f"https://projects.blender.org/api/v1/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        req = Request(url, headers={'Accept': 'application/json'})
        with urlopen(req) as response:
            return json.load(response)
    except HTTPError as e:
        print(f"\033[91mError fetching PR data: {e}\033[0m")
        sys.exit(1)

def checkout_pr(pr_number, owner='blender', repo='blender'):
    pr_data = fetch_pr_json(owner, repo, pr_number)

    if pr_data.get('merged'):
        print(f"\033[92mPR #{pr_number} is already merged.\033[0m")
        print(f"Merged at: {pr_data.get('merged_at')}")
        print(f"Merged by: {pr_data.get('merged_by', {}).get('full_name')}")
        return

    if pr_data.get('state') == 'closed':
        print(f"\033[91mPR #{pr_number} is closed.\033[0m")
        return

    pr_repo = pr_data['head']['repo']['full_name']
    pr_author = pr_data['head']['repo']['owner']['username']
    pr_branch = pr_data['head']['ref']
    base_branch = pr_data['base']['ref']
    local_branch = f"PR/{pr_number}/{pr_author}-{pr_branch}"

    print(f"\033[95mPulling PR #{pr_number}: {pr_data['title']}\033[0m")
    print(f"\033[90mIncoming branch: {pr_repo}\033[0m")
    print(f"\033[90mBase branch   : {base_branch}\033[0m")
    print(f"\033[90mLocal branch  : {local_branch}\033[0m")

    current_branch = run_cmd("git branch --show-current", capture_output=True)
    if current_branch != base_branch:
        run_cmd(f"git checkout {base_branch}")

    existing_branches = run_cmd("git branch", capture_output=True).splitlines()
    existing_branches = [b.strip().lstrip('* ') for b in existing_branches]
    if local_branch in existing_branches:
        print(f"\033[95mBranch {local_branch} exists, refreshing it.\033[0m")
        run_cmd(f"git branch -D {local_branch}")
    else:
        print(f"\033[96mBranch {local_branch} does not exist.\033[0m")

    run_cmd(f"git checkout -b {local_branch} {base_branch}")
    run_cmd(f"git pull --no-rebase --ff --no-edit --commit https://projects.blender.org/{pr_repo} {pr_branch}")

    print(f"\033[95mBranch {local_branch} is ready for use.\033[0m")
    print(f"\033[94mPulled PR #{pr_number}: {pr_data['title']}\033[0m")

def prune_branches():
    print("\033[93mPruning local branches...\033[0m")
    # Delete local branches that have been merged
    merged_branches = run_cmd("git branch --merged", capture_output=True).splitlines()
    current_branch = run_cmd("git branch --show-current", capture_output=True)
    for branch in merged_branches:
        branch = branch.strip().lstrip('* ')
        if branch and branch != current_branch and branch != 'main' and branch != 'master':
            run_cmd(f"git branch -d {branch}")
            print(f"\033[92mDeleted merged branch: {branch}\033[0m")

    # Delete local branches whose remote counterparts have been deleted
    run_cmd("git fetch --prune")
    gone_branches = run_cmd("git branch -vv", capture_output=True).splitlines()
    for line in gone_branches:
        if '[gone]' in line:
            branch = line.split()[0]
            run_cmd(f"git branch -D {branch}")
            print(f"\033[92mDeleted stale branch: {branch}\033[0m")

def main():
    parser = argparse.ArgumentParser(
        description="Manage Blender pull requests and prune local branches.",
        epilog="""
Examples:
  - Fetch and checkout a pull request:
      ./pr_tool.py 12345

  - Specify a different repository:
      ./pr_tool.py 12345 --repo blender-manual

  - Prune local branches:
      ./pr_tool.py --prune
"""
    )
    parser.add_argument("pr_number", nargs='?', help="Pull request number to fetch and checkout.")
    parser.add_argument("--owner", "-o", default="blender", help="Repository owner (default: blender).")
    parser.add_argument("--repo", "-r", default="blender", help="Repository name (default: blender).")
    parser.add_argument("--prune", action="store_true", help="Prune local branches that have been merged or are stale.")

    args = parser.parse_args()

    if args.prune:
        prune_branches()
    elif args.pr_number:
        checkout_pr(args.pr_number, owner=args.owner, repo=args.repo)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()