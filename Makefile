.PHONY: requirements package-plugin build release bump help sync-cli build-cli

VERSION := $(shell grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')
PLUGIN_ZIP := dist/claude-finance-kit-plugin-v$(VERSION).zip
TAG := v$(VERSION)

help:
	@echo "make requirements    - Export requirements.txt from pyproject.toml"
	@echo "make package-plugin  - Package plugin files into zip"
	@echo "make build           - Build Python wheel + sdist"
	@echo "make build-cli       - Build CLI TypeScript"
	@echo "make sync-cli        - Sync src/plugin/ assets to cli/assets/"
	@echo "make bump TYPE=patch - Bump version (patch|minor|major)"
	@echo "make release         - Create git tag + GitHub release with plugin zip + wheel"

bump:
	@TYPE=$${TYPE:-patch}; \
	IFS='.' read -r MAJOR MINOR PATCH <<< "$(VERSION)"; \
	case "$$TYPE" in \
		major) MAJOR=$$((MAJOR + 1)); MINOR=0; PATCH=0 ;; \
		minor) MINOR=$$((MINOR + 1)); PATCH=0 ;; \
		patch) PATCH=$$((PATCH + 1)) ;; \
		*) echo "Error: TYPE must be patch|minor|major"; exit 1 ;; \
	esac; \
	NEW="$$MAJOR.$$MINOR.$$PATCH"; \
	sed -i '' "s/^version = \"$(VERSION)\"/version = \"$$NEW\"/" pyproject.toml; \
	sed -i '' "s/__version__ = \"$(VERSION)\"/__version__ = \"$$NEW\"/" src/claude_finance_kit/__init__.py; \
	sed -i '' "s/\"version\": \"$(VERSION)\"/\"version\": \"$$NEW\"/" .claude-plugin/plugin.json; \
	sed -i '' "s/\"version\": \"$(VERSION)\"/\"version\": \"$$NEW\"/" .claude-plugin/marketplace.json; \
	sed -i '' "s/\"version\": \"$(VERSION)\"/\"version\": \"$$NEW\"/" cli/package.json; \
	echo "$(VERSION) -> $$NEW"

requirements:
	@bash scripts/export-requirements.sh > requirements.txt
	@echo "Exported requirements.txt"

sync-cli:
	@rm -rf cli/assets/skills cli/assets/references cli/assets/agents cli/assets/hooks cli/assets/commands cli/assets/templates
	@mkdir -p cli/assets/templates/platforms
	@cp -rL src/plugin/skills cli/assets/skills
	@cp -rL src/plugin/references cli/assets/references
	@cp -rL src/plugin/agents cli/assets/agents
	@cp -rL src/plugin/hooks cli/assets/hooks
	@cp -rL src/plugin/commands cli/assets/commands
	@cp -r src/plugin/templates/platforms/*.json cli/assets/templates/platforms/
	@echo "Synced src/plugin/ -> cli/assets/"

build-cli: sync-cli
	@cd cli && npm run build
	@echo "Built CLI in cli/dist/"

package-plugin:
	@bash scripts/package-plugin.sh

build:
	@python -m build --wheel --sdist
	@echo "Built wheel + sdist in dist/"

release: package-plugin build
	@if git rev-parse "$(TAG)" >/dev/null 2>&1; then \
		echo "Error: tag $(TAG) already exists. Bump version in pyproject.toml first."; \
		exit 1; \
	fi
	@sed -i '' 's/REF="v[0-9]*\.[0-9]*\.[0-9]*"/REF="$(TAG)"/' CLAUDE.md
	@if git diff --quiet CLAUDE.md; then :; else \
		git add CLAUDE.md; \
		git commit -m "fix: update REF to $(TAG) in CLAUDE.md"; \
	fi
	git tag -a "$(TAG)" -m "Release $(TAG)"
	git push origin "$(TAG)"
	gh release create "$(TAG)" \
		"$(PLUGIN_ZIP)" \
		dist/claude_finance_kit-$(VERSION)-py3-none-any.whl \
		dist/claude_finance_kit-$(VERSION).tar.gz \
		--title "$(TAG)" \
		--notes "claude-finance-kit $(TAG)" \
		--latest
	@echo ""
	@echo "Released: $(TAG)"
	@echo "Assets: $(PLUGIN_ZIP) + wheel + sdist"
