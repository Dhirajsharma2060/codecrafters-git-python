from operator import itemgetter
import sys
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
def main():
    match sys.argv[1:]:
        case ["init"]:
            Path(".git/").mkdir(parents=True)
            Path(".git/objects").mkdir(parents=True)
            Path(".git/refs").mkdir(parents=True)
            Path(".git/HEAD").write_text("ref: refs/heads/main\n")
            print("Initialized git directory")
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
            contents = b"".join(
                [
                    b"tree %b\n" % tree_sha.encode(),
                    b"parent %b\n" % commit_sha.encode(),
                    b"author ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n",
                    b"committer ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n\n",
                    message.encode(),
                    b"\n",
                ]
            )
            hash = write_object(Path("."), "commit", contents)
            print(hash)
if __name__ == "__main__":
    main()