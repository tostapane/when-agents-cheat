#!/usr/bin/env bash
# Downloads HumanEval and HumanEval+ into data/ and verifies their checksums.
# Safe to re-run: files that already match are not downloaded again.
set -euo pipefail

cd "$(dirname "$0")/.."

sha256() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

fetch() {
  local path=$1 url=$2 expected=$3

  if [[ -f "$path" && "$(sha256 "$path")" == "$expected" ]]; then
    echo "OK (already present): $path"
    return
  fi

  mkdir -p "$(dirname "$path")"
  curl -fsSL -o "$path.tmp" "$url"

  if [[ "$(sha256 "$path.tmp")" != "$expected" ]]; then
    rm -f "$path.tmp"
    echo "ERROR: checksum mismatch for $path" >&2
    exit 1
  fi

  mv "$path.tmp" "$path"
  echo "OK (downloaded): $path"
}

# Visible tests: original HumanEval, from OpenAI's repo at a fixed commit.
fetch data/humaneval/HumanEval.jsonl.gz \
  https://raw.githubusercontent.com/openai/human-eval/b9453e8f1865df0a0057a1383767caa400acfbcf/data/HumanEval.jsonl.gz \
  b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef

# Full test suite: HumanEval+ v0.1.10, from the EvalPlus release.
fetch data/humanevalplus/HumanEvalPlus-OriginFmt.jsonl.gz \
  https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus-OriginFmt.jsonl.gz \
  daa7661c8189924068069b0872a440b491edb60f8bdf431d5957adc88d18bae5
