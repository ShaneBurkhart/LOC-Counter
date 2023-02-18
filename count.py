import datetime
import os

# this seems to be working, the only issues are it double counts if the changes are on two branches and not in master

USERNAME = "kelseyalderman@gmail.com"
REPOS = ["STIO", "GMI-PlanGrid", "MonoRepo", "AquaParks"]
DAYS = 10
IGNORE = ["package-lock.json"]
ACCOUNT_OVERRIDES = {
    "MonoRepo": "MonoRepoProject",
}

# Set up the date range for the last 7 days
today = datetime.datetime.now().date()
start_date = today - datetime.timedelta(days=DAYS)
dates = [start_date + datetime.timedelta(days=i) for i in range(DAYS)]
date_ranges = [(datetime.datetime.combine(d, datetime.time.min), datetime.datetime.combine(d, datetime.time.max)) for d in dates]

outputs = []

# mkdir repos if it doesn't exist
if not os.path.isdir("repos"):
  os.mkdir("repos")

os.chdir("repos")

# Loop over the repositories
for repo in REPOS:
    github_repo = None
    if repo in ACCOUNT_OVERRIDES:
        github_repo = f"{ACCOUNT_OVERRIDES[repo]}/{repo}"
    else:
        github_repo = f"ShaneBurkhart/{repo}"

    # Clone the repository if it doesn't exist
    if not os.path.isdir(repo) and not os.path.isdir("{repo}/.git"):
        os.system(f"git clone git@github.com:{github_repo}.git")

    os.chdir(repo)

    # Fetch all branches
    os.system("git fetch")

    os.chdir("..")


for repo in REPOS:
    os.chdir(repo)

    lines_changed = [0] * DAYS 
    # List only branches that have not been merged
    output = os.popen("git branch -r --format='%(refname:short)' | grep -v HEAD").read().strip()
    all_branches = output.strip().split('\n')

    seen_commits = set()
    commit_hash = None
    
    # Iterate over relevant branches and count lines changed
    index = 0
    for branch_name in all_branches:
        index += 1
        # print(f"Checking {branch_name}")
        print(f"\x1b[2K[{index}/{len(all_branches)}] {repo} checking {branch_name}...", end="\r", flush=True)
        for i, (start_of_day, end_of_day) in enumerate(date_ranges):
            cmd = f"git log --no-merges --author='{USERNAME}' --since='{start_of_day}' --until='{end_of_day}' --pretty=tformat:'%H' --numstat {branch_name}"
            # print(cmd)
            output = os.popen(cmd).read()
            if output:
                total = 0

                for line in output.split('\n'):
                    if not line:
                        continue

                    if len(line.split()) == 1:
                        # this is a commit hash
                        # add previous to seen commits
                        if commit_hash:
                            seen_commits.add(commit_hash)
                        commit_hash = line.strip()
                        # print(f"Commit hash: {commit_hash}")
                        continue

                    if any([ignore in line for ignore in IGNORE]):
                        continue
                    
                    if commit_hash and commit_hash in seen_commits:
                        # print(f"Skipping {line}")
                        continue

                    line_parts = line.split()
                    if len(line_parts) == 3:
                        added, deleted, _ = line_parts
                        try:
                            # any line added is counted, if we delete more than we add, we count the difference
                            # this is because line edits are counted as a delete and an add
                            total += int(added) + max(int(deleted) - int(added), 0)
                        except ValueError:
                            continue
                
                lines_changed[i] += total
                if total:
                    print(f"\x1b[2K{dates[i]}\t{total}\t{repo} => {branch_name}")

            # if lines_changed[i] > 0:
                # print(f"{repo} {branch_name} {dates[i]} {lines_changed[i]}")

    # Print the total number of lines changed by the user in each day for each repo
    outputs.append({"repo": repo, "lines_changed": lines_changed, "dates": dates})

    # cd back to the original directory
    os.chdir("..")


print('\x1b[2K\n')
print(f"Lines changed by {USERNAME} in the last {DAYS} days")

for output in outputs:
    # print a nice table with date as column
    repo = output["repo"]
    lines_changed = output["lines_changed"]
    dates = output["dates"]

    print(f"\nREPO: {repo}")
    for i, date in enumerate(dates):
        print(f"{date}\t{lines_changed[i]}")

