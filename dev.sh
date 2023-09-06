#!/bin/bash
set -e

mypy geotag_photos.py
black geotag_photos.py