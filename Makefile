.PHONY: help build up down restart logs api web clean rebuild test health

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Hiển thị trợ giúp
	@echo "$(GREEN)EleGANt Makeup Transfer - Docker Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build tất cả Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

build-no-cache: ## Build lại từ đầu (no cache)
	@echo "$(GREEN)Building Docker images (no cache)...$(NC)"
	docker-compose build --no-cache

up: ## Chạy tất cả services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Web UI: http://localhost:8501"

down: ## Dừng tất cả services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart tất cả services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart

logs: ## Xem logs của tất cả services
	docker-compose logs -f

logs-api: ## Xem logs của API service
	docker-compose logs -f elegant-api

logs-web: ## Xem logs của Web UI service
	docker-compose logs -f elegant-web

api: ## Chỉ chạy API service
	@echo "$(GREEN)Starting API service...$(NC)"
	docker-compose up -d elegant-api
	@echo "$(GREEN)API started at http://localhost:8000$(NC)"

web: ## Chỉ chạy Web UI service
	@echo "$(GREEN)Starting Web UI service...$(NC)"
	docker-compose up -d elegant-web
	@echo "$(GREEN)Web UI started at http://localhost:8501$(NC)"

stop-api: ## Dừng API service
	docker-compose stop elegant-api

stop-web: ## Dừng Web UI service
	docker-compose stop elegant-web

clean: ## Xóa containers và networks
	@echo "$(RED)Cleaning up containers and networks...$(NC)"
	docker-compose down
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: ## Xóa containers, networks, và volumes
	@echo "$(RED)WARNING: This will delete all data in volumes!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)Full cleanup complete!$(NC)"; \
	fi

rebuild: down build-no-cache up ## Rebuild và restart tất cả

ps: ## Liệt kê các containers đang chạy
	docker-compose ps

health: ## Kiểm tra health của services
	@echo "$(GREEN)Checking health status...$(NC)"
	@echo "\nAPI Health:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)API not responding$(NC)"
	@echo "\nWeb UI Health:"
	@curl -s http://localhost:8501/_stcore/health || echo "$(RED)Web UI not responding$(NC)"

test-api: ## Test API endpoints
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	@echo "\nGET /:"
	@curl -s http://localhost:8000/ | python -m json.tool
	@echo "\nGET /presets:"
	@curl -s http://localhost:8000/presets | python -m json.tool

shell-api: ## Vào shell của API container
	docker-compose exec elegant-api bash

shell-web: ## Vào shell của Web UI container
	docker-compose exec elegant-web bash

stats: ## Xem resource usage
	docker stats elegant-makeup-api elegant-makeup-web

top: ## Xem processes trong containers
	docker-compose top

pull: ## Pull latest images từ Docker Hub
	@echo "$(GREEN)Pulling images from Docker Hub...$(NC)"
	docker-compose pull

push: ## Push images lên Docker Hub
	@echo "$(YELLOW)Pushing images to Docker Hub...$(NC)"
	@echo "API Image: oliver9889/elegant-makeup:api-latest"
	@echo "Web Image: oliver9889/elegant-makeup:web-latest"
	docker-compose push
	@echo "$(GREEN)Push complete!$(NC)"

login: ## Login vào Docker Hub
	@echo "$(YELLOW)Logging in to Docker Hub...$(NC)"
	docker login

tag: ## Tag images với version cụ thể (VERSION=x.x.x)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Error: Please specify version: make tag VERSION=1.0.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Tagging images with version $(VERSION)...$(NC)"
	docker tag oliver9889/elegant-makeup:api-latest oliver9889/elegant-makeup:api-$(VERSION)
	docker tag oliver9889/elegant-makeup:web-latest oliver9889/elegant-makeup:web-$(VERSION)
	@echo "$(GREEN)Tagging complete!$(NC)"

push-version: tag ## Push images với version tag (VERSION=x.x.x)
	@echo "$(YELLOW)Pushing versioned images...$(NC)"
	docker push oliver9889/elegant-makeup:api-$(VERSION)
	docker push oliver9889/elegant-makeup:web-$(VERSION)
	@echo "$(GREEN)Push complete!$(NC)"

build-push: build push ## Build và push lên Docker Hub

dev: ## Chạy ở development mode
	docker-compose up

prod: up ## Chạy ở production mode (detached)

backup-presets: ## Backup presets folder
	@echo "$(GREEN)Backing up presets...$(NC)"
	tar -czf presets-backup-$$(date +%Y%m%d-%H%M%S).tar.gz presets/
	@echo "$(GREEN)Backup complete!$(NC)"

restore-presets: ## Restore presets từ backup (chỉ định file bằng FILE=...)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify backup file: make restore-presets FILE=backup.tar.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring presets from $(FILE)...$(NC)"
	tar -xzf $(FILE)
	@echo "$(GREEN)Restore complete!$(NC)"

info: ## Hiển thị thông tin về services
	@echo "$(GREEN)Service Information:$(NC)"
	@echo "\n$(YELLOW)API Service:$(NC)"
	@echo "  Container: elegant-makeup-api"
	@echo "  Port: 8000"
	@echo "  URL: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "\n$(YELLOW)Web UI Service:$(NC)"
	@echo "  Container: elegant-makeup-web"
	@echo "  Port: 8501"
	@echo "  URL: http://localhost:8501"
	@echo "\n$(YELLOW)Volumes:$(NC)"
	@echo "  ./result -> /app/result"
	@echo "  ./ckpts -> /app/ckpts"
	@echo "  ./presets -> /app/presets"
	@echo "  ./assets -> /app/assets"

install: ## Cài đặt dependencies (cho local development)
	pip install -r requirements.txt

check-deps: ## Kiểm tra dependencies
	@which docker > /dev/null || (echo "$(RED)Docker not found! Please install Docker$(NC)" && exit 1)
	@which docker-compose > /dev/null || (echo "$(RED)Docker Compose not found! Please install Docker Compose$(NC)" && exit 1)
	@echo "$(GREEN)All dependencies are installed!$(NC)"

# Default target
.DEFAULT_GOAL := help
