#!/usr/bin/env bash

# Install missing JS deps manually
yarn install --check-files

# Ensure Ruby gems are installed
bundle install --without development test

# Compile assets
bundle exec rails assets:precompile
