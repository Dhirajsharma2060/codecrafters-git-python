import sys
import os
import zlib
import hashlib
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

def cat_file(blob_sha):
    try:
        path = f".git/objects/{blob_sha[:2]}/{blob_sha[2:]}"
        with open(path, "rb") as f:
            raw = zlib.decompress(f.read())
            header, content = raw.split(b"\0", maxsplit=1)
            print(content.decode("utf-8"), end="")
    except FileNotFoundError:
        print(f"Error: Object {blob_sha} not found")
    except zlib.error:
        print(f"Error: Failed to decompress object {blob_sha}")

def hash_object(content):
    try:
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
        print(sha1_hash)
    except Exception as e:
        print(f"Error hashing object: {e}")

def ls_tree(tree_sha, name_only=False):
    try:
        path = f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}"
        with open(path, "rb") as f:
            raw = zlib.decompress(f.read())
            header, content = raw.split(b"\0", maxsplit=1)
            
            if not header.startswith(b"tree"):
                print(f"Error: Object {tree_sha} is not a tree")
                return
            
            i = 0
            entries = []
            while i < len(content):
                mode_end = content.find(b' ', i)
                mode = content[i:mode_end].decode('utf-8')
                i = mode_end + 1
                
                name_end = content.find(b'\0', i)
                name = content[i:name_end].decode('utf-8')
                i = name_end + 1
                
                sha1 = content[i:i + 20].hex()
                i += 20
                
                entries.append((mode, sha1, name))
            
            entries.sort(key=lambda entry: entry[2])  # Sort by name
            
            for mode, sha1, name in entries:
                if name_only:
                    print(name)
                else:
                    obj_type = "tree" if mode == "40000" else "blob"
                    print(f"{mode} {obj_type} {sha1}    {name}")
                
    except FileNotFoundError:
        print(f"Error: Object {tree_sha} not found")
    except zlib.error:
        print(f"Error: Failed to decompress object {tree_sha}")

def write_tree():
    try:
        tree_content = generate_tree_content(".")
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
        print(sha1_hash)
    except Exception as e:
        print(f"Error writing tree object: {e}")

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
    try:
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
    except Exception as e:
        print(f"Error creating blob object: {e}")
        return None
def read_head():
    try:
        with open(".git/HEAD", "r") as f:
            ref = f.readline().strip().split(": ")[1]
        return ref
    except FileNotFoundError:
        print("Error: .git/HEAD file not found")
        return None   
def create_commit(tree_sha1, message):
    ref = read_head()
    if not ref:
        return
    
    ref_path = f".git/{ref}"
    parent_commit = None
    
    if os.path.exists(ref_path):
        with open(ref_path, "r") as f:
            parent_commit = f.read().strip()
    
    author = "Your Name <your.email@example.com>"
    timestamp = int(time.time())
    timezone = time.strftime("%z", time.gmtime())
    commit_content = f"tree {tree_sha1}\n"
    
    if parent_commit:
        commit_content += f"parent {parent_commit}\n"
    
    commit_content += f"author {author} {timestamp} {timezone}\n"
    commit_content += f"committer {author} {timestamp} {timezone}\n\n"
    commit_content += f"{message}\n"
    
    commit_sha1 = hash_object(commit_content)
    with open(ref_path, "w") as f:
        f.write(commit_sha1)
    
    print(commit_sha1)    

def main():
    if len(sys.argv) < 2:
        print("Usage: script.py <command> [<args>]")
        return

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "cat-file":
        if len(sys.argv) == 4 and sys.argv[2] == "-p":
            cat_file(sys.argv[3])
        else:
            print("Usage: script.py cat-file -p <sha1>")
    elif command == "hash-object":
        if len(sys.argv) == 4 and sys.argv[2] == "-w":
            filename = sys.argv[3]
            if os.path.isfile(filename):
                with open(filename, "r") as file:
                    content = file.read()
                    hash_object(content)
            else:
                print(f"Error: File '{filename}' not found")
        else:
            print("Usage: script.py hash-object -w <filename>")
    elif command == "ls-tree":
        if len(sys.argv) == 4 and sys.argv[2] == "--name-only":
            ls_tree(sys.argv[3], name_only=True)
        elif len(sys.argv) == 3:
            ls_tree(sys.argv[2])
        else:
            print("Usage: script.py ls-tree [--name-only] <sha1>")
    elif command == "write-tree":
        write_tree()
    elif command == "commit":
        if len(sys.argv) >= 3:
            message = sys.argv[2]
            tree_sha1 = write_tree()
            create_commit(tree_sha1, message)
        else:
            print("Usage: script.py commit <message>")    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
