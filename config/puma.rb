# Puma can serve each request in a thread from an internal thread pool.
max_threads_count = ENV.fetch('RAILS_MAX_THREADS', 5)
min_threads_count = ENV.fetch('RAILS_MIN_THREADS', max_threads_count)
threads min_threads_count, max_threads_count

# Bind Puma to the correct port for Render
port ENV.fetch('PORT') { 3000 }

# Environment setting
environment ENV.fetch('RAILS_ENV') { 'development' }

# PID file location
pidfile ENV.fetch('PIDFILE') { 'tmp/pids/server.pid' }

# Workers for clustered mode
workers ENV.fetch('WEB_CONCURRENCY') { 2 }

# Preload for performance
preload_app!

# Allow Puma to be restarted by `rails restart`
plugin :tmp_restart
