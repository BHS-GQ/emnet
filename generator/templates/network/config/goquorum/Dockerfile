ARG QUORUM_VERSION=latest

FROM --platform=linux/amd64 wowells/quorumbhs:0.0.0

RUN apk add --no-cache curl

COPY docker-entrypoint.sh /usr/local/bin/
COPY data data

RUN mkdir -p /data /permissions /var/log/quorum \
    && addgroup -g 1000 quorum \
    && adduser -u 1000 -G quorum -s /bin/sh -D quorum \
    && chown -R quorum:quorum /data /permissions /var/log/quorum 
USER quorum

ENTRYPOINT ["docker-entrypoint.sh"]
