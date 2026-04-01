.PHONY: bump release package

TYPE ?= patch

bump:
	cd cli && npm run build && npm run bump -- $(TYPE)
	cd cli && npm run build
	git add -A
	git commit -m "chore: bump version to $$(cd cli && node -p "require('./package.json').version")"

release: bump
	$(eval VERSION := $(shell cd cli && node -p "require('./package.json').version"))
	git push
	gh release create v$(VERSION) --title "v$(VERSION)" --generate-notes

package:
	cd cli && npm run build && npm run package
