This app has no web interface — it only answers API calls from your Documize
server. A browser visiting it is redirected to documize.com; that is expected.

To start using it, sign in to your Documize instance as an administrator and set
the conversion service endpoint to `$CLOUDRON-APP-ORIGIN`.

You can check that the service is up with
`curl $CLOUDRON-APP-ORIGIN/api/version`, which returns the upstream version
number.

The conversion API is not password protected, since Documize calls it without
credentials. Anyone who knows this address can submit documents for conversion,
so restrict access at the firewall if the endpoint does not need to be public.
