# hop

Jump to a predefined set of directories with single-letter shortcuts.

Run `hop`, see your saved directories (each with a fixed letter, a fixed color, and live git
status), press a letter, and you're there.

```
 [d]  ~/projects/dotfiles        ✅ main ≡
 [h]  ~/projects/hop             ❌ feat/colors ↑2
 [w]  ~/work/api                 ✅ release ↓1
 [z]  ~/notes                    —

hop to>
```

## Install

Requires [`uv`](https://docs.astral.sh/uv/) or [`pipx`](https://pipx.pypa.io/), plus bash or zsh.

```sh
git clone <repo-url> hop && cd hop && ./install.sh
source ~/.zshrc   # or ~/.bashrc, or restart your shell
```

The installer puts the `_hop` CLI on your PATH and adds a `hop` shell function (which does the
actual `cd`) to your shell rc. You can delete the clone afterward.

## Usage

| Command          | Action                                              |
| ---------------- | --------------------------------------------------- |
| `hop`            | List dirs + git status; press a letter to `cd`      |
| `hop add [path]` | Add the current dir (or `path`) to the list         |
| `hop remove`     | Pick a dir to remove (alias: `hop rm`)              |
| `hop list`       | Print the list without prompting                    |
| `hop -h`         | Help                                                |

Press `q` or `Esc` to cancel the picker without moving.

## How it works

A child process can't change its parent shell's directory, so `hop` is two pieces:

- `_hop` — a Python CLI that renders the picker (to stderr) and prints the chosen path to stdout.
- `hop()` — a shell function that captures that path and runs `cd`.

Letters are assigned from each directory's first letter (with graceful collision handling) and
**persisted** in the config, so they never change between runs. Each directory's color is
derived deterministically from its letter. Git status (clean ✅ / dirty ❌, branch, and
ahead/behind vs. upstream) is resolved for all repos in parallel, with a spinner that repaints
when results arrive.

## Config

JSON at `$HOP_CONFIG`, else `${XDG_CONFIG_HOME:-~/.config}/hop/config.json`:

```json
{
  "version": 1,
  "directories": [
    { "path": "/Users/you/projects/hop", "letter": "h" }
  ]
}
```

## Renaming the command

Edit the function name in `~/.local/share/hop/hop.sh` (it still calls `_hop` underneath).
