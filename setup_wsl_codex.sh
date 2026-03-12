#!/usr/bin/env bash
set -euo pipefail

# Idempotent WSL setup for Codex + Velox project.
# Usage:
#   bash setup_wsl_codex.sh
#   bash setup_wsl_codex.sh /path/to/project

PROJECT_DIR="${1:-$(pwd)}"
DEFAULT_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_CONFIG_PATH="${HOME}/.codex/config.toml"
SHELL_HELPERS_PATH="${HOME}/.codex/codex_shell_helpers.sh"
BASHRC_PATH="${HOME}/.bashrc"

readonly PROJECT_DIR DEFAULT_MODEL CODEX_CONFIG_PATH SHELL_HELPERS_PATH BASHRC_PATH

log() {
  printf '[setup_wsl_codex] %s\n' "$1"
}

append_if_missing() {
  local line="$1"
  local file="$2"
  if [[ ! -f "$file" ]]; then
    touch "$file"
  fi
  if ! grep -Fqx "$line" "$file"; then
    printf '%s\n' "$line" >> "$file"
  fi
}

ensure_apt_packages() {
  log "Installing required apt packages..."
  sudo apt update
  sudo apt install -y \
    build-essential \
    git \
    curl \
    ca-certificates \
    unzip \
    zip \
    jq \
    ripgrep \
    python3 \
    python3-venv \
    python3-pip
}

load_nvm() {
  export NVM_DIR="${HOME}/.nvm"
  # shellcheck disable=SC1090
  [[ -s "${NVM_DIR}/nvm.sh" ]] && source "${NVM_DIR}/nvm.sh"
}

ensure_nvm_and_node() {
  log "Installing nvm + Node 22..."
  if [[ ! -s "${HOME}/.nvm/nvm.sh" ]]; then
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  fi

  load_nvm

  nvm install 22
  nvm alias default 22

  append_if_missing 'export NVM_DIR="$HOME/.nvm"' "$BASHRC_PATH"
  append_if_missing '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' "$BASHRC_PATH"
}

ensure_codex_cli() {
  log "Installing @openai/codex globally..."
  npm install -g @openai/codex
}

ensure_codex_config() {
  log "Updating ${CODEX_CONFIG_PATH} profiles..."
  mkdir -p "${HOME}/.codex"

  if [[ ! -f "${CODEX_CONFIG_PATH}" ]]; then
    touch "${CODEX_CONFIG_PATH}"
  fi

  if ! grep -Fq '[profiles.safe]' "${CODEX_CONFIG_PATH}"; then
    cat >> "${CODEX_CONFIG_PATH}" <<'TOML'

[profiles.safe]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.safe.sandbox_workspace_write]
network_access = true

[profiles.autonomous]
approval_policy = "never"
sandbox_mode = "workspace-write"

[profiles.autonomous.sandbox_workspace_write]
network_access = true

[profiles.full_access]
approval_policy = "never"
sandbox_mode = "danger-full-access"
TOML
  fi

  local project_block
  project_block="[projects.\"${PROJECT_DIR}\"]"
  if ! grep -Fq "${project_block}" "${CODEX_CONFIG_PATH}"; then
    cat >> "${CODEX_CONFIG_PATH}" <<TOML

${project_block}
trust_level = "trusted"
TOML
  fi
}

ensure_python_env() {
  log "Preparing Python virtualenv in ${PROJECT_DIR}..."
  cd "${PROJECT_DIR}"

  if [[ ! -d ".venv-wsl" ]]; then
    python3 -m venv .venv-wsl
  fi

  # shellcheck disable=SC1091
  source ".venv-wsl/bin/activate"
  pip install --upgrade pip
  pip install -e ".[dev]"
}

ensure_env_file() {
  cd "${PROJECT_DIR}"
  if [[ ! -f ".env" && -f ".env.example" ]]; then
    log "Creating .env from .env.example..."
    cp .env.example .env
  fi
}

ensure_shell_helpers() {
  log "Adding start_codex helper + aliases..."
  mkdir -p "${HOME}/.codex"
  cat > "${SHELL_HELPERS_PATH}" <<EOF
#!/usr/bin/env bash

start_codex() {
  local profile="\${1:-full_access}"
  local model="\${2:-${DEFAULT_MODEL}}"
  local project="\${3:-${PROJECT_DIR}}"

  if ! command -v codex >/dev/null 2>&1; then
    echo "codex command not found. Re-open terminal or run: source ~/.bashrc"
    return 1
  fi

  cd "\${project}" || return 1

  if [[ -f ".venv-wsl/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source ".venv-wsl/bin/activate"
  fi

  codex -p "\${profile}" -m "\${model}"
}

alias start-codex='start_codex'
alias scx='start_codex'
alias scxsafe='start_codex safe'
alias scxauto='start_codex autonomous'
alias scxfull='start_codex full_access'
EOF
  chmod +x "${SHELL_HELPERS_PATH}"

  append_if_missing '' "$BASHRC_PATH"
  append_if_missing '# Codex helpers' "$BASHRC_PATH"
  append_if_missing "[ -f \"${SHELL_HELPERS_PATH}\" ] && source \"${SHELL_HELPERS_PATH}\"" "$BASHRC_PATH"
}

print_next_steps() {
  cat <<EOF

Setup completed.

Next steps:
1) Reload shell:
   source ~/.bashrc
2) Login once (if needed):
   codex login
3) Start Codex quickly:
   start-codex

Examples:
- start-codex safe
- start-codex autonomous
- start-codex full_access
EOF
}

main() {
  ensure_apt_packages
  ensure_nvm_and_node
  ensure_codex_cli
  ensure_codex_config
  ensure_python_env
  ensure_env_file
  ensure_shell_helpers
  print_next_steps
}

main "$@"
