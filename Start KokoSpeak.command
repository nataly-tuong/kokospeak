#!/usr/bin/env bash
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$ROOT/install.sh" "$@"
RESULT=$?
if [[ "$RESULT" != 0 ]]; then
  echo
  echo "Setup stopped. Check the error above; rerunning this file will retry setup."
  read -r -p "Press Enter to close this window. "
fi
exit "$RESULT"
