PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
LOCAL_BIN ?= $(HOME)/.local/bin
LOCAL_APPS ?= $(HOME)/.local/share/applications
WRAPPER := $(LOCAL_BIN)/darktable-launcher
DESKTOP_FILE := $(LOCAL_APPS)/darktable-launcher.desktop
LAUNCHER_BIN := $(abspath $(BIN))/darktable-launcher
ICON_FILE := $(abspath assets/darktable-launcher-icon.ico)

.PHONY: venv install run clean desktop-launcher

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: venv
	$(PIP) install .
	mkdir -p $(LOCAL_BIN)
	printf '#!/usr/bin/env sh\n"%s" "$$@"\n' $(LAUNCHER_BIN) > $(WRAPPER)
	chmod +x $(WRAPPER)

desktop-launcher: install
	mkdir -p $(LOCAL_APPS)
	printf '[Desktop Entry]\nType=Application\nName=darktable-launcher\nComment=Launch Darktable catalogues\nExec=%s\nIcon=%s\nTerminal=false\nCategories=Graphics;\n' $(WRAPPER) $(ICON_FILE) > $(DESKTOP_FILE)
	if command -v update-desktop-database >/dev/null 2>&1; then \
		update-desktop-database $(LOCAL_APPS); \
	fi

run: install
	$(BIN)/darktable-launcher

clean:
	rm -rf $(VENV)
