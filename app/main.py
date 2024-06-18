import sys
import os
import zlib
import hashlib

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
        tree_content = generate_tree_content(".")  # Pass the root directory
        tree_content_str = ""
        
        for mode, sha1, name in tree_content:
            entry = f"{mode} {name}\0".encode() + bytes.fromhex(sha1)
            tree_content_str += entry

        header = f"tree {len(tree_content_str)}\0".encode()
        full_content = header + tree_content_str
        sha1_hash = hashlib.sha1(tree_content_str).hexdigest()
        obj_dir = f".git/objects/{sha1_hash[:2]}"
        obj_path = f"{obj_dir}/{sha1_hash[2:]}"
        
        if not os.path.exists(obj_path):
            os.makedirs(obj_dir, exist_ok=True)
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(tree_content_str))
            print(sha1_hash)
        else:
            print(f"Tree object with SHA-1 hash {sha1_hash} already exists")

    except Exception as e:
        print(f"Error writing tree object: {e}")
def generate_tree_content(root_dir):
    tree_content = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]  # Ignore .git directory
        for file in files:
            if not file.startswith("."):  # Ignore hidden files
                file_path = os.path.relpath(os.path.join(root, file), start=root_dir)
                mode = "100644"  # Default mode for files
                sha1 = hash_file(file_path)
                tree_content.append((mode, sha1, file_path))
        
        for dir in dirs:
            dir_path = os.path.relpath(os.path.join(root, dir), start=root_dir)
            mode = "40000"  # Mode for directories
            sha1 = generate_tree_content(os.path.join(root, dir))
            tree_content.append((mode, sha1, dir_path))
    
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

def hash_file(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
        sha1_hash = hashlib.sha1(content).hexdigest()
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
    elif command == "write-tree":  # Handle the write-tree command
        write_tree()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
