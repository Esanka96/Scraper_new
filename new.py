import subprocess
import os

# Folder and branch details
repo_path = r"D:\INNODATA\ISM\ZZZZ\ISM_Script"
folder_name = "Ref_5303"
branch_name = f"ref-5303"
commit_message = f"Add {folder_name} folder"

# Change directory to the repo
os.chdir(repo_path)

try:
    # 1. Create and switch to a new branch
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # 2. Add the folder
    subprocess.run(["git", "add", folder_name], check=True)

    # 3. Commit changes
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # 4. Push the branch to remote
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    print(f"✅ Folder '{folder_name}' pushed successfully to branch '{branch_name}'.")

except subprocess.CalledProcessError as e:
    print(f"❌ Error occurred: {e}")
