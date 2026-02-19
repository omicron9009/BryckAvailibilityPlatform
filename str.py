from pathlib import Path

STRUCTURE = {
    "bryck": {
        "backend": {
            "main.py": None,
            "models.py": None,
            "schemas.py": None,
            "database.py": None,
            "requirements.txt": None,
            ".env": None,
        },
        "frontend": {
            "index.html": None,
            "style.css": None,
            "app.js": None,
        },
        "docker-compose.yml": None,
    }
}


def create_tree(base: Path, tree: dict):
    for name, content in tree.items():
        path = base / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_tree(path, content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)


if __name__ == "__main__":
    create_tree(Path.cwd(), STRUCTURE)
    print("✅ bryck project structure created")
