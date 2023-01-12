#!/bin/bash

set -exuo pipefail

cd "$(dirname "$0")"
cd ../

git switch master

# Merge translations before updating po/pot files to avoid merge conflicts.
# The workflow is based on https://github.com/WeblateOrg/weblate/issues/1847#issuecomment-415715912
# Ignore returncode if no changes need to be merged.
wlc lock
wlc commit
set +e
git fetch weblate && git merge --ff --squash weblate/master && git commit po/ -m "Update translations." && git push
set -e
wlc reset
wlc unlock

# Regenerate .pot file manually.
#    # Ignore returncode if no changes need to be committed.
#    ./dev/generate-pot.sh
#    set +e
#    git commit po/ -m "Update translation templates."
#    set -e
#    git push
