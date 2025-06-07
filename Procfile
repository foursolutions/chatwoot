release: POSTGRES_STATEMENT_TIMEOUT=600s bundle exec rails db:chatwoot_prepare && echo $SOURCE_VERSION > .git_sha
web: bundle exec rails s -b 0.0.0.0 -p $PORT
worker: bundle exec sidekiq -C config/sidekiq.yml