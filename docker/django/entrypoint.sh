#!/usr/bin/env sh

set -o errexit
set -o nounset

readonly cmd="$*"

postgres_ready () {
  # Check that postgres is up and running on port `5432`:
  dockerize -wait 'tcp://db:5432' -timeout 5s
}

if [ -z ${SKIP_DB_CHECK+x} ]; then
    # We need this line to make sure that this container is started
  # after the one with postgres:
  until postgres_ready; do
    >&2 echo 'Postgres is unavailable - sleeping. Use env SKIP_DB_CHECK=1 for skip this stage.'
  done

  # It is also possible to wait for other services as well: redis, elastic, mongo
  >&2 echo 'Postgres is up - continuing...'
else
  echo "Skiping db available check";
fi

# Evaluating passed command (do not touch):
# shellcheck disable=SC2086
exec $cmd
