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
            print(f"{sha1_hash}")
        else:
            print(f"Object with SHA-1 hash {sha1_hash} already exists")
    except Exception as e:
        print(f"Error hashing object: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: script.py <command> [<args>]")
        return

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "cat-file":
        if len(sys.argv) == 4 and sys.argv[2] == "-p":  # Check for option "-p" for cat-file
            cat_file(sys.argv[3])  # Pass SHA-1 hash to cat_file function
        else:
            print("Usage: script.py cat-file -p <sha1>")
    elif command == "hash-object":
        if len(sys.argv) == 4 and sys.argv[2] == "-w":  # Check for option "-w" for hash-object
            filename = sys.argv[3]  # Get filename from command line argument
            if os.path.isfile(filename):  # Check if file exists
                with open(filename, "r") as file:  # Open file for reading
                    content = file.read()  # Read content from file
                    hash_object(content)  # Pass content to hash_object function
            else:
                print(f"Error: File '{filename}' not found")
        else:
            print("Usage: script.py hash-object -w <filename>")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
