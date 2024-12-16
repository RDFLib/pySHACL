FROM docker.io/library/python:3.11-alpine
LABEL org.opencontainers.image.base.name="docker.io/library/python:3.11-alpine"
LABEL org.opencontainers.image.base.digest="sha256:004b4029670f2964bb102d076571c9d750c2a43b51c13c768e443c95a71aa9f3"
LABEL org.opencontainers.image.source="https://github.com/RDFLib/pySHACL"
LABEL maintainer="ashleysommer@gmail.com"
RUN apk add --no-cache --update tini-static cython
RUN apk add --no-cache --update --virtual build-dependencies build-base libffi-dev python3-dev py3-cffi
# Update to latest setuptools and pip in /usr/local/lib to mitigate CVE-2024-6345
RUN pip3 install -U pip setuptools
WORKDIR /home/pyshacl
RUN addgroup -g 1000 -S pyshacl &&\
    adduser --disabled-password --gecos "" --home "$(pwd)" --ingroup "pyshacl" --no-create-home --uid 1000 pyshacl
WORKDIR /app
LABEL org.opencontainers.image.version="0.29.1"
COPY . .
RUN chown -R pyshacl:pyshacl /home/pyshacl /app && chmod -R 775 /home/pyshacl /app
USER pyshacl
ENV PATH="/home/pyshacl/.local/bin:$PATH"
RUN pip3 install "poetry>=1.8.4,<2.0"
RUN poetry install --no-dev --extras "js http"
USER root
RUN apk del build-dependencies
USER pyshacl
ENTRYPOINT ["/sbin/tini-static", "--"]
CMD ["poetry", "run", "pyshacl"]
