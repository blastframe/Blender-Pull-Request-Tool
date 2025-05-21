# Blender Pull Request Tool

Manage Blender pull requests and prune local branches.

## Credit

This tool is based on code by dr. Sybren A. Stüvel.  
For more details, visit: [dr. Sybren A. Stüvel's post](https://stuvel.eu/post/2023-02-17-gitea-pull-requests-and-fish/)

## Usage

Fetch and checkout a pull request:
```bash
./pr_tool.py 12345
```

Specify a different repository:
```bash
./pr_tool.py 12345 --repo blender-manual
```

Prune local branches:
```bash
./pr_tool.py --prune
```
