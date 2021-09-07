git-stats
===

Report some useful metrics from git repositories and plot them. Useful for reporting on projects.

## Metrics

- Commits per repository
- Average commits per day per repository
- Commits per calendar week
- Average days between tags per repository. Assumes tags are versions and monotonically increasing (e.g v1.0, v1.1).

## Usage

1. Create a configuration file named `repos.yml` based on the temmplate provided in `repos-template.yml`.
1. Add repository information in the `repositories` section. If a repository URL is specified, the repository will be
   cloned, otherwise the value of `path` will be used to locate a local repository. Only one of `path` or `url` is
   required.
1. Configure reporting options in the `config` section.
   - `reporting_period` is a relative time in days, specified as `last{N}days`. Specify an absolute reporting 
     period in the format `2021-08-01:2021-09-01`.
   - `plot` controls whether to generate plots from the metrics.
