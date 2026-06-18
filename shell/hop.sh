# hop shell wrapper: capture the chosen path from _hop and cd into it.
# Rename the function below if you want a different command name.
hop() {
  local out
  out="$(command _hop "$@")" || return
  [ -n "$out" ] && cd "$out"
}
