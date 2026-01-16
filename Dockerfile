FROM docker.io/library/python:3.11-alpine
LABEL org.opencontainers.image.base.name="docker.io/library/python:3.11-alpine"
LABEL org.opencontainers.image.base.digest="sha256:d5e2fc72296647869f5eeb09e7741088a1841195059de842b05b94cb9d3771bb"
LABEL org.opencontainers.image.source="https://github.com/RDFLib/pySHACL"
LABEL org.opencontainers.image.version="0.31.0"
LABEL maintainer="ashleysommer@gmail.com"
RUN apk add --no-cache --update tini-static cython
RUN apk add --no-cache --update --virtual build-dependencies build-base libffi-dev python3-dev py3-cffi
# Update to latest setuptools and pip in /usr/local/lib to mitigate CVE-2024-6345
RUN pip3 install -U pip setuptools
WORKDIR /home/pyshacl
RUN addgroup -g 1000 -S pyshacl &&\
    adduser --disabled-password --gecos "" --home "$(pwd)" --ingroup "pyshacl" --no-create-home --uid 1000 pyshacl
WORKDIR /app
COPY . .
RUN chown -R pyshacl:pyshacl /home/pyshacl /app && chmod -R 775 /home/pyshacl /app
USER pyshacl
ENV PATH="/home/pyshacl/.local/bin:$PATH"
RUN pip3 install "poetry<3.0,>=2.1"
RUN poetry install --extras "js http"
RUN poetry run pip3 install -U "rdflib[orjson]<8" # add orjson support to rdflib
USER root
RUN apk del build-dependencies
USER pyshacl
ENTRYPOINT ["/sbin/tini-static", "--"]
CMD ["poetry", "run", "pyshacl"]
