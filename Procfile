release: bundle exec rails db:chatwoot_prepare
web: bundle exec rails ip_lookup:setup && exec bundle exec puma -C config/puma.rb
worker: bundle exec sidekiq -C config/sidekiq.yml
