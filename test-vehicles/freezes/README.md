# Freezes

Before-and-after snapshots for a migration: the `pip freeze`, the test run, the list of
failures — whatever the migration needs to prove it moved only what it meant to move.

- One folder per migration, named `<sprint-id>-<short-name>`, e.g. `9cf8b9-postgres-upgrade/`.
- The sprint that creates a folder deletes it once nothing reads it; its done-when says when.
- This README stays, so the next migration knows where its snapshots go.

They are committed rather than ignored because they have to survive a change of machine, and
whoever runs the comparison needs the same files. Nothing here is source and nothing here
ships: `test-vehicles/` is outside the Docker build.
