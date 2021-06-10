# Grab the docker python image
FROM ghcr.io/opensafely-core/python:latest as base-python

# local install
COPY ./ ./
RUN python -m pip install .

# labeling
LABEL org.opencontainers.image.title="matching" \
      org.opencontainers.image.description="Matching action for opensafely.org" \
      org.opencontainers.image.source="https://github.com/opensafely-core/matching" \
      org.opensafely.action="match"

# re-use entrypoint from base-docker image
ENV ACTION_EXEC=match