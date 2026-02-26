#!/bin/bash

# clean.sh - Utility to clear cache and temporary files for ai-analyst project

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}AI-Analyst Cache Cleaner${NC}"
echo "--------------------------"

clean_quick() {
    echo -e "${YELLOW}Running Quick Clean...${NC}"
    
    # Frontend build cache
    if [ -d "frontend/.next" ]; then
        echo "Removing frontend/.next..."
        rm -rf frontend/.next
    fi
    
    # Python cache
    echo "Removing Python __pycache__ files..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    
    # UV cache
    if [ -d ".uv" ]; then
        echo "Removing .uv cache..."
        rm -rf .uv
    fi

    # Logs
    echo "Removing log files..."
    rm -f backend/*.log
    rm -f nohup.out

    echo -e "${GREEN}Quick clean complete!${NC}"
}

clean_deep() {
    echo -e "${YELLOW}Running Deep Clean...${NC}"
    
    # ML Models cache
    if [ -d "backend/models/fastembed_cache" ]; then
        echo "Removing backend/models/fastembed_cache (1.5GB+)..."
        rm -rf backend/models/fastembed_cache
    fi
    
    echo -e "${GREEN}Deep clean complete! Models will be re-downloaded on next run.${NC}"
}

reset_db() {
    echo -e "${RED}WARNING: This will delete all chat history and vector data!${NC}"
    read -p "Are you sure? (y/N) " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "Resetting databases..."
        rm -rf backend/qdrant_db
        rm -rf backend/vector_store
        rm -f backend/chat_memory.db
        echo -e "${GREEN}Databases reset successfully.${NC}"
    else
        echo "Database reset cancelled."
    fi
}

show_help() {
    echo "Usage: ./clean.sh [option]"
    echo ""
    echo "Options:"
    echo "  quick    Remove build caches and temporary files (default)"
    echo "  deep     Remove large ML model caches"
    echo "  db       Reset databases and chat history"
    echo "  all      Run both quick and deep clean"
    echo "  help     Show this help message"
}

case "$1" in
    quick|"")
        clean_quick
        ;;
    deep)
        clean_deep
        ;;
    db)
        reset_db
        ;;
    all)
        clean_quick
        clean_deep
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac
