# The upstream conversion service is distributed only as a Docker image (no source
# release), so its artifacts are lifted out of it and re-assembled on the Cloudron
# base image: /documize/api-linux (Go HTTP API), java/ (Aspose + PlantUML),
# puppet.js + node_modules (headless Chrome PDF export) and the bundled TrueType
# fonts used when rendering documents.
FROM documize/conversion:3.4.0 AS upstream

FROM cloudron/base:5.1.0@sha256:1c0666c9abe9e2090d33686826d4e97769b799124573118d41e0d7485135748e

# openjdk 11 -> the Aspose jars shipped by upstream target Java 11
# graphviz    -> used by the PlantUML diagram endpoint
# lib*        -> shared libraries required by the Chromium build that puppeteer bundles
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-11-jre-headless \
        fontconfig \
        fonts-liberation \
        graphviz \
        libasound2t64 \
        libatk-bridge2.0-0t64 \
        libatk1.0-0t64 \
        libatspi2.0-0t64 \
        libcairo2 \
        libcups2t64 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0t64 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxshmfence1 \
        xdg-utils && \
    rm -rf /var/cache/apt /var/lib/apt/lists

ENV PATH="/usr/local/node-24.19.0/bin:${PATH}"

RUN mkdir -p /app/code/documize
WORKDIR /app/code/documize

COPY --from=upstream /documize/api-linux    /app/code/documize/api-linux
COPY --from=upstream /documize/java         /app/code/documize/java
COPY --from=upstream /documize/puppet.js    /app/code/documize/puppet.js
COPY --from=upstream /documize/package.json /app/code/documize/package.json
COPY --from=upstream /documize/node_modules /app/code/documize/node_modules

# Fonts shipped by upstream: without them Word -> PDF rendering falls back to
# substitutes and the layout of converted documents drifts. They account for
# ~370MB of the image; drop this COPY and the fc-cache below for a slimmer image
# that only carries the Liberation fonts.
COPY --from=upstream /usr/local/share/fonts/truetype /usr/local/share/fonts/truetype
RUN fc-cache -f

COPY start.sh /app/code/start.sh
RUN chmod +x /app/code/start.sh

CMD [ "/app/code/start.sh" ]
