from operator import itemgetter
import sys
import zlib
import hashlib
from pathlib import Path
from typing import Tuple, List
import json
import os 
import urllib.request
import shutil

def read_object(parent: Path, sha: str) -> bytes:
    pre = sha[:2]
    post = sha[2:]
    p = parent / ".git" / "objects" / pre / post
    bs = p.read_bytes()
    _, content = zlib.decompress(bs).split(b"\0", maxsplit=1)
    return content

def write_object(parent: Path, ty: str, content: bytes) -> str:
    content = ty.encode() + b" " + f"{len(content)}".encode() + b"\0" + content
    hash = hashlib.sha1(content, usedforsecurity=False).hexdigest()
    compressed_content = zlib.compress(content)
    pre = hash[:2]
    post = hash[2:]
    p = parent / ".git" / "objects" / pre / post
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(compressed_content)
    return hash

# Clone repo feature 
def clone_repository(repo_url: str, destination_dir: str):
    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Fetch repository data from the URL using urllib
    response = urllib.request.urlopen(repo_url)
    if response.getcode() == 200:
        repo_data = json.loads(response.read().decode('utf-8'))  # Assuming the repository data is in JSON format

        # Extract objects, references, and other necessary information from repo_data
        objects = repo_data['objects']
        references = repo_data['references']

        # Create directories and files to replicate repository structure
        local_repo_path = Path(destination_dir) / ".git"
        local_repo_path.mkdir(parents=True, exist_ok=True)

        for obj_sha, obj_content in objects.items():
            write_object(local_repo_path, obj_content['type'], obj_content['content'])

        for ref_name, ref_sha in references.items():
            ref_file = local_repo_path / ref_name
            ref_file.write_text(ref_sha)

        init_git_repo(destination_dir)
    else:
        print("Failed to clone repository")

def init_git_repo(directory):
    # Create necessary Git directories and files
    os.makedirs(os.path.join(directory, '.git', 'objects'))
    os.makedirs(os.path.join(directory, '.git', 'refs', 'heads'))
    open(os.path.join(directory, '.git', 'HEAD'), 'w').write('ref: refs/heads/main\n')
    # Other initialization steps as needed

def main():
    if len(sys.argv) != 4 or sys.argv[1] != "clone":
        print("Usage: python your_git_clone.py clone <repository_url> <destination_directory>")
        sys.exit(1)

    repository_url = sys.argv[2]
    destination_directory = sys.argv[3]
    
    # Call the clone_repository function with the extracted arguments
    clone_repository(repository_url, destination_directory)

if __name__ == "__main__":
    main()
