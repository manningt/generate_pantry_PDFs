#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "google-api-python-client",
#   "google-auth-httplib2",
#   "google-auth-oauthlib"
# ]
# ///

from upload_folder_to_gdrive import authenticate_drive

if __name__ == "__main__":
    authenticate_drive()
