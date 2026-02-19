from pathlib import Path

STRUCTURE = {
    "bryck-platform": {
        "backend": {
            "app": {
                "api": {
                    "v1": {
                        "__init__.py": None,
                        "router.py": None,
                        "endpoints": {
                            "__init__.py": None,
                            "machines.py": None,
                            "health.py": None,
                        },
                    }
                },
                "core": {
                    "__init__.py": None,
                    "config.py": None,
                    "database.py": None,
                    "exceptions.py": None,
                },
                "models": {
                    "__init__.py": None,
                    "machine.py": None,
                },
                "schemas": {
                    "__init__.py": None,
                    "machine.py": None,
                },
                "services": {
                    "__init__.py": None,
                    "machine_service.py": None,
                    "bryckapi_client.py": None,
                },
                "repositories": {
                    "__init__.py": None,
                    "machine_repository.py": None,
                },
                "main.py": None,
            },
            "alembic": {
                "versions": {},
                "env.py": None,
                "script.py.mako": None,
            },
            "tests": {
                "__init__.py": None,
                "conftest.py": None,
                "test_machines.py": None,
            },
            "alembic.ini": None,
            "Dockerfile": None,
            "requirements.txt": None,
            ".env.example": None,
        },
        "frontend": {
            "index.html": None,
            "css": {
                "styles.css": None,
            },
            "js": {
                "api.js": None,
                "store.js": None,
                "renderer.js": None,
                "events.js": None,
                "app.js": None,
            },
        },
        "docker-compose.yml": None,
        "nginx": {
            "nginx.conf": None,
        },
        "README.md": None,
    }
}


def create_structure(base: Path, tree: dict):
    for name, content in tree.items():
        path = base / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)


if __name__ == "__main__":
    create_structure(Path.cwd(), STRUCTURE)
    print("✅ bryck-platform folder structure created successfully")
