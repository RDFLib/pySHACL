FROM docker.io/library/python:3.11-alpine
LABEL org.opencontainers.image.base.name="docker.io/library/python:3.11-alpine"
LABEL org.opencontainers.image.base.digest="sha256:caafba876f841774905f73df0fcaf7fe3f55aaf9cb48a9e369a41077f860d4a7"
LABEL org.opencontainers.image.source="https://github.com/RDFLib/pySHACL"
LABEL maintainer="ashleysommer@gmail.com"
RUN apk add --no-cache --update tini-static cython
RUN apk add --no-cache --update --virtual build-dependencies build-base libffi-dev python3-dev py3-cffi
WORKDIR /home/pyshacl
RUN addgroup -g 1000 -S pyshacl &&\
    adduser --disabled-password --gecos "" --home "$(pwd)" --ingroup "pyshacl" --no-create-home --uid 1000 pyshacl
WORKDIR /app
LABEL org.opencontainers.image.version="0.23.0"
COPY . .
RUN chown -R pyshacl:pyshacl /home/pyshacl /app && chmod -R 775 /home/pyshacl /app
USER pyshacl
ENV PATH="/home/pyshacl/.local/bin:$PATH"
RUN pip3 install "poetry>=1.5.0,<2.0"
RUN poetry install --no-dev --extras "js http"
USER root
RUN apk del build-dependencies
USER pyshacl
ENTRYPOINT ["/sbin/tini-static", "--"]
CMD ["poetry", "run", "pyshacl"]
