# Fastfetch: only run in interactive shells attached to a terminal.
if [[ -o interactive && -t 1 ]]; then
    if command -v fastfetch >/dev/null; then
        fastfetch
    fi
fi

# Native Zsh setup: preserve inherited environment and existing PATH entries.
typeset -U path PATH
path=("$HOME/.local/npm/bin" "$HOME/.local/bin" "$HOME/bin" $path)
export PATH

# Persistent history and native completion; no framework required.
HISTFILE=${HISTFILE:-$HOME/.zsh_history}
HISTSIZE=${HISTSIZE:-10000}
SAVEHIST=${SAVEHIST:-10000}
setopt APPEND_HISTORY HIST_IGNORE_DUPS HIST_IGNORE_SPACE
autoload -Uz compinit
compinit
bindkey -e

# Starship renders the prompt (also suppress venv's duplicate prefix).
export VIRTUAL_ENV_DISABLE_PROMPT=1
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
fi
