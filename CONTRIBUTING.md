# Contributing

Useful contributions are new compatibility reports, corrections to observed
behavior, small reviewed recipes and improvements to the native launcher.

For a new model, report its exact model/firmware, architecture/runtime, which
steps were exercised, what was checked after full boot and standby/wake, and
how restoration was verified. A successful preflight is not a successful
root session; a root session is not a validated launcher install.

Use a separate profile rather than widening the existing profile's model
gate. Preserve the owner-selected features and take fresh rollback state.
Include sanitized observations and the corresponding tests.

Do not attach serial numbers, MAC/IP addresses, device/account IDs, original
app assemblies, SDK binaries, database snapshots or raw session logs.
Review screenshots for viewing history, profile names and other personal
information before sharing them.

For local checks:

```sh
python3 -m unittest discover -s tests -v
python3 tools/build.py payloads
dotnet run --project tests/CatalogTests.csproj -- launcher/assets/apps.json
```

On Windows, use `python` in place of `python3`; see the
[PowerShell access setup](docs/02-access.md#windows-powershell-7). Shell-based
tests require a POSIX `sh` and, for script transport tests, `base64` on `PATH`
(for example from Git for Windows). Report skips alongside passes; a Windows
run that skips shell checks does not replace the Linux CI run.

Keep tracked `.sh` files as LF, as specified in `.gitattributes`. Generated
TV scripts and SQL must explicitly use UTF-8 and LF rather than host defaults.
When changing script transport, verify actual shell execution, literal
arguments and nonzero exit propagation. SQL generator changes need synthetic
apply/restore and concurrent-drift checks. Close SQLite connections explicitly
so temporary databases can be removed on Windows.

NUI changes also need a build against matching private references and a
clearly stated hardware-test status. Keep attribution/license files with
derived assets and code.
