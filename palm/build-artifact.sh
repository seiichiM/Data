#!/bin/sh
# Emit the artifact-hosted variant of index.html.
#
# The published page is wrapped in a skeleton that already supplies
# <!doctype>, <head> and <body>, so this strips the standalone
# wrapper between the ARTIFACT markers and leaves the page content.
#
#   ./build-artifact.sh > /tmp/palm-artifact.html
set -e
cd "$(dirname "$0")"
sed -n '/<!--ARTIFACT:BEGIN-->/,/<!--ARTIFACT:END-->/p' index.html \
  | sed -e '/<!--ARTIFACT:BEGIN-->/d' \
        -e '/<!--ARTIFACT:END-->/d' \
        -e '/<!--ARTIFACT:HEADEND-->/d' \
        -e '/^<\/head>$/d' \
        -e '/^<body>$/d'
