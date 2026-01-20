#!/bin/bash
set -e

# Функция ожидания порта
wait_for_port() {
    local host="$1"
    local port="$2"
    local timeout=15
    local start_time=$(date +%s)

    echo "Waiting for $host:$port..."
    # nc для проверки порта
    while ! nc -z "$host" "$port"; do
        sleep 1
        local current_time=$(date +%s)
        if (( current_time - start_time > timeout )); then
            echo "Timeout waiting for $host:$port"
            exit 1
        fi
    done
    echo "$host:$port is available"
}

#  Ждем БД
DB_HOST=${POSTGRES_SERVER:-db}
DB_PORT=${POSTGRES_PORT:-5432}

wait_for_port "$DB_HOST" "$DB_PORT"

# миграции
echo "Running migrations..."
alembic upgrade head

#Запуск команды, переданной в Docker
echo "Starting application..."
exec "$@"
