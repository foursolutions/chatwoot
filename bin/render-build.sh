#!/usr/bin/env bash

# Fail fast on any error
set -e

# Install JS deps manually
yarn install --check-files

# Install Ruby gems without development & test groups
bundle install --without development test

# Precompile frontend assets
bundle exec rails assets:precompile
