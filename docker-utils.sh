#!/bin/bash

# Docker utility script for Surfer API

function show_help {
    echo "Surfer API Docker Utilities"
    echo ""
    echo "Usage: ./docker-utils.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - Show logs from all services"
    echo "  build       - Rebuild all services"
    echo "  db-shell    - Open a PostgreSQL shell"
    echo "  redis-shell - Open a Redis shell"
    echo "  api-shell   - Open a shell in the API container"
    echo "  status      - Show status of all services"
    echo "  clean       - Remove all containers and volumes"
    echo "  help        - Show this help message"
    echo ""
}

function start_services {
    echo "Starting all services..."
    docker-compose up -d
    echo "Services started. API available at http://localhost:8000"
}

function stop_services {
    echo "Stopping all services..."
    docker-compose down
    echo "Services stopped."
}

function restart_services {
    echo "Restarting all services..."
    docker-compose restart
    echo "Services restarted."
}

function show_logs {
    echo "Showing logs (press Ctrl+C to exit)..."
    docker-compose logs -f
}

function build_services {
    echo "Rebuilding all services..."
    docker-compose up -d --build
    echo "Services rebuilt and started."
}

function db_shell {
    echo "Opening PostgreSQL shell..."
    docker-compose exec db psql -U postgres -d surfer
}

function redis_shell {
    echo "Opening Redis shell..."
    docker-compose exec redis redis-cli
}

function api_shell {
    echo "Opening shell in API container..."
    docker-compose exec api bash
}

function show_status {
    echo "Service status:"
    docker-compose ps
}

function clean_all {
    echo "Removing all containers and volumes..."
    docker-compose down -v
    echo "Cleanup complete."
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    build)
        build_services
        ;;
    db-shell)
        db_shell
        ;;
    redis-shell)
        redis_shell
        ;;
    api-shell)
        api_shell
        ;;
    status)
        show_status
        ;;
    clean)
        clean_all
        ;;
    help|*)
        show_help
        ;;
esac 