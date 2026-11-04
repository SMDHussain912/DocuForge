# Development Guide

## Requirements

- Python 3.11 or newer
- pip
- Git
- LibreOffice for the eventual office-rendering integration (not required by the current foundation tests)

## Setup

    git clone https://github.com/SMDHussain912/DocuForge.git
    cd DocuForge
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -e ".[dev]"

## Run

    python -m docuforge

## Test

    pytest

## Current scope

The GUI is a placeholder shell, the data adapter is an interface, and filename helpers are independent utilities. No production document merge or PDF export pipeline is implemented yet.
