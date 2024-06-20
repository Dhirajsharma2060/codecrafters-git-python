from operator import itemgetter
import sys
import os
import time
import zlib
import hashlib
from pathlib import Path
from typing import Tuple, List

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

def init():
    try:
        Path(".git/").mkdir(parents=True)
        Path(".git/objects").mkdir(parents=True)
        Path(".git/refs").mkdir(parents=True)
        Path(".git/HEAD").write_text("ref: refs/heads/main\n")
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
        commit_content += f"parent {parent_sha1}\n"
    
    commit_content += f"author {author} {timestamp} {timezone}\n"
    commit_content += f"committer {author} {timestamp} {timezone}\n\n"
    commit_content += f"{message}\n"
    
    full_content = f"commit {len(commit_content)}\0{commit_content}"
    sha1_hash = hashlib.sha1(full_content.encode("utf-8")).hexdigest()
    obj_dir = f".git/objects/{sha1_hash[:2]}"
    obj_path = f"{obj_dir}/{sha1_hash[2:]}"

    if not os.path.exists(obj_path):
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(full_content.encode("utf-8")))
    return sha1_hash

def read_tree(tree_sha1):
    obj_dir = f".git/objects/{tree_sha1[:2]}"
    obj_path = f"{obj_dir}/{tree_sha1[2:]}"
    
    try:
        with open(obj_path, "rb") as f:
            compressed_content = f.read()
        full_content = zlib.decompress(compressed_content)
        _, tree_content = full_content.split(b'\0', 1)
        
        entries = []
        i = 0
        while i < len(tree_content):
            space_index = tree_content.find(b' ', i)
            null_index = tree_content.find(b'\0', space_index)
            mode = tree_content[i:space_index].decode()
            name = tree_content[space_index + 1:null_index].decode()
            sha = tree_content[null_index + 1:null_index + 21].hex()
            entries.append((mode, name, sha))
            i = null_index + 21
        
        return entries
    except FileNotFoundError:
        print("Error: Tree object not found")
        return None
    except Exception as e:
        print(f"Error reading tree object: {e}")
        return None

def ls_tree(tree_sha1, name_only=False):
    entries = read_tree(tree_sha1)
    if not entries:
        return

    for mode, name, sha in entries:
        if name_only:
            print(name)
        else:
            print(f"{mode} {sha} {name}")

def hash_object_command(file_path, write):
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        header = f"blob {len(content)}\0".encode()
        full_content = header + content
        sha1_hash = hashlib.sha1(full_content).hexdigest()
        
        if write:
            obj_dir = f".git/objects/{sha1_hash[:2]}"
            obj_path = f"{obj_dir}/{sha1_hash[2:]}"
            if not os.path.exists(obj_path):
                os.makedirs(obj_dir, exist_ok=True)
                with open(obj_path, "wb") as f:
                    f.write(zlib.compress(full_content))
        
        print(sha1_hash)
    except FileNotFoundError:
        print(f"Error: file '{file_path}' not found")
    except Exception as e:
        print(f"Error hashing object: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: script.py <command> [<args>]")
        return

    command = sys.argv[1]

    match sys.argv[1:]:
        case ["init"]:
            init()
        case ["cat-file", "-p", blob_sha]:
            sys.stdout.buffer.write(read_object(Path("."), blob_sha))
        case ["hash-object", "-w", path]:
            hash = write_object(Path("."), "blob", Path(path).read_bytes())
            print(hash)
        case ["ls-tree", "--name-only", tree_sha]:
            items = []
            contents = read_object(Path("."), tree_sha)
            while contents:
                mode, contents = contents.split(b" ", 1)
                name, contents = contents.split(b"\0", 1)
                sha = contents[:20]
                contents = contents[20:]
                items.append((mode.decode(), name.decode(), sha.hex()))
            for _, name, _ in items:
                print(name)
        case ["write-tree"]:
            parent = Path(".")
            def toEntry(p: Path, exclude_git: bool = False) -> Tuple[str, str, str]:
                mode = "40000" if p.is_dir() else "100644"
                if p.is_dir():
                    entries: List[Tuple[str, str, str]] = []
                    for child in p.iterdir():
                        if exclude_git and child.name == ".git":
                            continue
                        entries.append(toEntry(child))
                    s_entries = sorted(entries, key=itemgetter(1))
                    b_entries = b"".join(
                        m.encode() + b" " + n.encode() + b"\0" + bytes.fromhex(h)
                        for (m, n, h) in s_entries
                    )
                    hash = write_object(parent, "tree", b_entries)
                    return (mode, p.name, hash)
                else:
                    hash = write_object(parent, "blob", p.read_bytes())
                    return (mode, p.name, hash)
            (_, _, hash) = toEntry(Path(".").absolute(), True)
            print(hash)
        case ["commit-tree", tree_sha, "-p", commit_sha, "-m", message]:
            import time
            author_info = "Your Name <your.email@example.com>"
            timestamp = int(time.time())
            timezone = "+0000"
            commit_contents = f"tree {tree_sha}\n"
            commit_contents += f"parent {commit_sha}\n"
            commit_contents += f"author {author_info} {timestamp} {timezone}\n"
            commit_contents += f"committer {author_info} {timestamp} {timezone}\n\n"
            commit_contents += f"{message}\n"

            contents = b"commit " + str(len(commit_contents)).encode() + b"\0" + commit_contents.encode()
            hash = write_object(Path("."), "commit", contents)
            print(hash)
        case _:
            print("Unknown command")

if __name__ == "__main__":
    main()
