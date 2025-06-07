#!/usr/bin/env bash

echo "ruby-3.2.2" > .ruby-version

rm -f yarn.lock

yarn install --check-files || yarn install

bundle install --without development test

bundle exec rails assets:precompile
