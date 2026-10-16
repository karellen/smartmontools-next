# COPR smartmontools-next Repository

This is a COPR repository for the smartmontools trunk builds for Fedora.

The packages are built in the [karellen/smartmontools-next](https://copr.fedorainfracloud.org/coprs/karellen/smartmontools-next/)
COPR project from the [smartmontools](https://github.com/smartmontools/smartmontools) `main` branch for
Fedora, the EL8 to EL10 family (RHEL, EPEL, CentOS Stream, AlmaLinux) and Amazon Linux 2023.

## Installation

```
dnf copr enable karellen/smartmontools-next
dnf install smartmontools-next smartmontools-next-selinux --allowerasing
```

`smartmontools-next` conflicts with and provides `smartmontools`, so it replaces the distribution package.

## How It Works

* The `smartmontools` directory is a git submodule tracking upstream `main`.
* Every 6 hours the [update workflow](.github/workflows/update.yml) checks upstream for new commits. When there
  are any it bumps the submodule, regenerates `dist-version.sh` (the upstream `getversion.sh` output, so that the
  build knows the git revision without a git checkout), and runs `tito tag` followed by `git push --follow-tags`.
* COPR rebuilds the package from the pushed tag, producing the SRPM with tito.
* The package version is `<upstream release in configure.ac>.<commits since that release>`, e.g. `8.0.574`.

## Relationship to Fedora

The packaging (spec, SELinux policy module, `smartdnotify`, sysconfig, tmpfiles.d) is the Fedora
[smartmontools](https://src.fedoraproject.org/rpms/smartmontools) dist-git packaging, adapted to build from the
upstream trunk. This repository shares its git history with the Fedora dist-git repository and is periodically
synchronized with it by merging the Fedora branch.

The SELinux policy carries one local change: the `pidfs_t` rule is wrapped in an `optional_policy` block, because
the base policies of EL8, EL9 and Amazon Linux 2023 do not define `pidfs_t` and the module would otherwise fail
to install there.
