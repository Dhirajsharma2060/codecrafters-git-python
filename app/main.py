import os
import sys
import hashlib
import zlib
import time

def init():
    try:
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    except FileExistsError:
        print("Error: .git directory already exists")
    except OSError as e:
        print(f"Error creating .git directory: {e}")

def hash_object(content):
    content_bytes = content.encode("utf-8")
    header = f"blob {len(content_bytes)}\0"
    full_content = header.encode("utf-8") + content_bytes
    sha1_hash = hashlib.sha1(full_content).hexdigest()
    obj_dir = f".git/objects/{sha1_hash[:2]}"
    obj_path = f"{obj_dir}/{sha1_hash[2:]}"

    if not os.path.exists(obj_path):
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(full_content))
    return sha1_hash

def generate_tree_content(root_dir):
    tree_content = []

    for entry in os.listdir(root_dir):
        if entry == ".git":
            continue
        
        entry_path = os.path.join(root_dir, entry)
        
        if os.path.isdir(entry_path):
            mode = "40000"
            sha1 = write_tree_recursive(entry_path)
            tree_content.append((mode, sha1, entry))
        elif os.path.isfile(entry_path):
            mode = "100644"
            sha1 = create_blob(entry_path)
            tree_content.append((mode, sha1, entry))
    
    tree_content.sort(key=lambda entry: entry[2])  # Sort by name
    return tree_content

def write_tree_recursive(dir_path):
    tree_content = generate_tree_content(dir_path)
    tree_content_bytes = b""
    
    for mode, sha1, name in tree_content:
        entry = f"{mode} {name}\0".encode() + bytes.fromhex(sha1)
        tree_content_bytes += entry
    
    header = f"tree {len(tree_content_bytes)}\0".encode()
    full_content = header + tree_content_bytes
    sha1_hash = hashlib.sha1(full_content).hexdigest()
    obj_dir = f".git/objects/{sha1_hash[:2]}"
    obj_path = f"{obj_dir}/{sha1_hash[2:]}"
    
    if not os.path.exists(obj_path):
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(full_content))
    return sha1_hash

def create_blob(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    sha1_hash = hashlib.sha1(full_content).hexdigest()
    obj_dir = f".git/objects/{sha1_hash[:2]}"
    obj_path = f"{obj_dir}/{sha1_hash[2:]}"

    if not os.path.exists(obj_path):
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(full_content))
    return sha1_hash

def write_tree():
    try:
        tree_sha1 = write_tree_recursive(".")
        print(tree_sha1)
        return tree_sha1
    except Exception as e:
        print(f"Error writing tree object: {e}")
        return None

def create_commit(tree_sha1, parent_sha1, message):
    author = "Your Name <your.email@example.com>"
    timestamp = int(time.time())
    timezone = time.strftime("%z", time.gmtime())
    commit_content = f"tree {tree_sha1}\n"
    
    if parent_sha1:
        parent_path = f".git/objects/{parent_sha1[:2]}/{parent_sha1[2:]}"
        if os.path.exists(parent_path):
            commit_content += f"parent {parent_sha1}\n"
        else:
            print(f"Error: Parent commit {parent_sha1} not found")
            return None
    
    commit_content += f"author {author} {timestamp} {timezone}\n"
    commit_content += f"committer {author} {timestamp} {timezone}\n\n"
    commit_content += f"{message}\n"
    
    commit_sha1 = hash_object(commit_content)
    return commit_sha1

def main():
    if len(sys.argv) < 2:
        print("Usage: script.py <command> [<args>]")
        return

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "write-tree":
        write_tree()
    elif command == "commit-tree":
        if len(sys.argv) >= 7 and sys.argv[3] == "-p" and sys.argv[5] == "-m":
            tree_sha1 = sys.argv[2]
            parent_sha1 = sys.argv[4]
            message = sys.argv[6]
            commit_sha1 = create_commit(tree_sha1, parent_sha1, message)
            if commit_sha1:
                print(commit_sha1)
        else:
            print("Usage: script.py commit-tree <tree_sha> -p <parent_sha> -m <message>")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
