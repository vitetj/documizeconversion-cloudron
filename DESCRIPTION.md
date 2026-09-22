### Overview

This app packages the **Documize conversion service** — the companion service that
[Documize Community](https://www.documize.com) calls to import Word documents and
to generate PDF exports.

Documize itself ships without these capabilities: when a user uploads a `.docx`
file or exports a document as PDF, the Documize server forwards the job to a
separate conversion endpoint. Documize's own hosted endpoint is a shared service,
so the vendor recommends running the
[documize/conversion](https://hub.docker.com/r/documize/conversion) container
yourself and pointing your instance at it. That is exactly what this app does,
with the service reachable over HTTPS on its own Cloudron domain.

### Features

* Word (`.docx`) and `.doc` import into Documize sections
* PDF export of Documize documents, rendered with headless Chromium
* PlantUML diagram rendering
* Ships the upstream TrueType font set so converted documents keep their layout
* Runs unprivileged, keeps its scratch space on the app's own data volume

### Usage

Once installed, open your Documize instance as an administrator and set the
conversion endpoint to this app's URL (Settings → Documents/Conversion, or
`ConversionEndpoint` in the organisation settings). No further configuration is
needed — there is no user interface to log into, the app only answers the
Documize server's API calls.

### Note

The conversion API is unauthenticated by design, because the Documize server
calls it machine-to-machine. Treat the app's domain as a public endpoint and read
the security section of the package README before exposing it.
