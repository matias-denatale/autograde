# autograde

`autograde` is a small Python CLI that verifies whether a repository meets the AUTOGRADE spec:

- the URL points to a git repository
- the repository has a `main` branch
- the repository has a remote `feature` branch
- the `main` branch contains `file1.txt`

## Usage

```bash
python -m autograde <repository-url>
```

Example:

```bash
autograde https://github.com/example/autograde.git
```

The command prints `true` and exits with status `0` when all conditions are met. Otherwise it prints `false` and exits with status `1`.
