#!/usr/bin/env bash
set -o errexit

# 1. Install JS dependencies and build assets
yarn install --frozen-lockfile
yarn build:production

# 2. Optionally remove server-related files if present (safety)
rm -rf node_modules/.cache
