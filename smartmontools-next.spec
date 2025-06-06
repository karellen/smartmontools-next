# defining macros needed by SELinux
%global with_selinux 1
%global selinuxtype targeted
%global moduletype contrib
%global modulename smartmon
%global packagename smartmontools

Summary:	Tools for monitoring SMART capable hard disks
Name:		%{packagename}-next
Version:	7.6.1
Release:	1
Epoch:		1
License:	GPL-2.0-or-later
URL:		https://github.com/karellen/smartmontools-next
Source0:	%{name}-%{version}.tar.gz
Source2:	smartmontools.sysconf
Source4:	smartdnotify
Source6:	%{modulename}.te
Source7:	%{modulename}.if
Source8:	%{modulename}.fc
Source9:	%{modulename}.te.f33

Vendor: Karellen, Inc.
Packager: Karellen, Inc. <supervisor@karellen.co>

#fedora/rhel specific
Patch1:		smartmontools-5.38-defaultconf.patch

Conflicts: %{packagename}
Provides: %{packagename}
BuildRequires: make
BuildRequires:	gcc-c++ readline-devel ncurses-devel automake util-linux groff gettext
BuildRequires:	libselinux-devel libcap-ng-devel
BuildRequires:	systemd systemd-devel
%if 0%{?with_selinux}
# This ensures that the *-selinux package and all it’s dependencies are not pulled
# into containers and other systems that do not use SELinux
Requires:	(%{name}-selinux if selinux-policy-%{selinuxtype})
%endif

%description
This smartmontools spin from Karellen provides a curated trunk
version builds to enable testing latest features.

The smartmontools package contains two utility programs (smartctl
and smartd) to control and monitor storage systems using the Self-
Monitoring, Analysis and Reporting Technology System (SMART) built
into most modern ATA and SCSI hard disks. In many cases, these
utilities will provide advanced warning of disk degradation and
failure.

%if 0%{?with_selinux}
%package selinux
Summary:	SELinux policies for smartmontools
BuildArch:	noarch
Requires:	selinux-policy-%{selinuxtype}
Requires(post):	selinux-policy-%{selinuxtype}
BuildRequires:	selinux-policy-devel
Conflicts: %{packagename}-selinux
%{?selinux_requires}

%description selinux
Custom SELinux policy module for smartmontools
%endif

%prep
%setup -q 
pushd smartmontools/smartmontools
%patch -P1 -p1 -b .defaultconf
%if 0%{?with_selinux}
mkdir selinux
cp -p  %{SOURCE7} %{SOURCE8} selinux/
%if %{?fedora}0 > 330
cp -p %{SOURCE6} selinux/
%else
cp -p %{SOURCE9} selinux/smartmon.te
%endif

%endif
popd

%build
pushd smartmontools/smartmontools
autoreconf -i
%configure --with-selinux --with-libcap-ng=yes --with-libsystemd --with-systemdsystemunitdir=%{_unitdir} --sysconfdir=%{_sysconfdir}/%{packagename}/ --with-systemdenvfile=%{_sysconfdir}/sysconfig/%{packagename}

# update SOURCE5 on maintainer's machine prior commiting, there's no internet connection on builders
%make_build update-smart-drivedb
./update-smart-drivedb -s - -u sf drivedb.h ||:
cp drivedb.h ../../drivedb.h ||:

%make_build CXXFLAGS="$RPM_OPT_FLAGS -fpie" LDFLAGS="-pie -Wl,-z,relro,-z,now"

%if 0%{?with_selinux}
make -f %{_datadir}/selinux/devel/Makefile %{modulename}.pp
bzip2 -9 %{modulename}.pp
%endif

popd

%install
pushd smartmontools/smartmontools
%make_install

rm -f examplescripts/Makefile*
chmod a-x -R examplescripts/*
install -D -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/smartmontools
install -D -p -m 755 %{SOURCE4} $RPM_BUILD_ROOT/%{_libexecdir}/%{packagename}/smartdnotify
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/%{packagename}/smartd_warning.d
rm -rf $RPM_BUILD_ROOT/etc/{rc.d,init.d}
rm -rf $RPM_BUILD_ROOT%{_docdir}/%{packagename}
mkdir -p $RPM_BUILD_ROOT%{_sharedstatedir}/%{packagename}
mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{packagename}
for f in AUTHORS ChangeLog INSTALL NEWS README TODO examplescripts smartd.conf; do
  cp -r $f $RPM_BUILD_ROOT%{_docdir}/%{packagename}
done

%if 0%{?with_selinux}
install -D -m 0644 %{modulename}.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2
%endif
popd

%if 0%{?with_selinux}
# SELinux contexts are saved so that only affected files can be
# relabeled after the policy module installation
%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2
%selinux_relabel_post -s %{selinuxtype}

if [ "$1" -le "1" ]; then # First install
   # the daemon needs to be restarted for the custom label to be applied
   %systemd_postun_with_restart smartd.service
fi

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{modulename}
    %selinux_relabel_post -s %{selinuxtype}
    # the daemon needs to be restarted for the custom label to be removed
    %systemd_postun_with_restart smartd.service
fi
%endif

%preun
%systemd_preun smartd.service

%post
%systemd_post smartd.service

%postun
%systemd_postun_with_restart smartd.service

%files
%docdir %{_docdir}/%{packagename}
%{_docdir}/%{packagename}
%license smartmontools/smartmontools/COPYING
%dir %{_sysconfdir}/%{packagename}
%dir %{_sysconfdir}/%{packagename}/smartd_warning.d
%config(noreplace) %{_sysconfdir}/%{packagename}/smartd.conf
%config(noreplace) %{_sysconfdir}/%{packagename}/smartd_warning.sh
%config(noreplace) %{_sysconfdir}/sysconfig/smartmontools
%{_unitdir}/smartd.service
%{_sbindir}/smartd
%{_sbindir}/update-smart-drivedb
%{_sbindir}/smartctl
%{_mandir}/man?/smart*.*
%{_mandir}/man?/update-smart*.*
%{_libexecdir}/%{packagename}
%{_datadir}/%{packagename}
%{_sharedstatedir}/%{packagename}

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.*
%ghost %attr(0700,-,-) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{modulename}

%changelog
* Sat May 31 2025 Karellen Supervisor <supervisor@karellen.co> 7.6.1-1
- Update 2025-05-31T12:02:57Z (supervisor@karellen.co)

* Wed Apr 30 2025 Karellen Supervisor <supervisor@karellen.co> 7.6.0-1
- Update 2025-04-30T12:03:22Z (supervisor@karellen.co)

* Tue Apr 29 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.167-1
- Update 2025-04-29T18:02:39Z (supervisor@karellen.co)

* Tue Apr 29 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.165-1
- Update 2025-04-29T12:03:31Z (supervisor@karellen.co)

* Sun Apr 27 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.161-1
- Update 2025-04-27T18:02:17Z (supervisor@karellen.co)

* Sat Apr 26 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.160-1
- Update 2025-04-26T12:02:59Z (supervisor@karellen.co)

* Fri Apr 25 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.158-1
- Update 2025-04-25T18:02:27Z (supervisor@karellen.co)

* Tue Apr 22 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.154-1
- Update 2025-04-22T18:02:36Z (supervisor@karellen.co)

* Mon Apr 21 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.149-1
- Update 2025-04-21T18:02:29Z (supervisor@karellen.co)

* Sat Apr 19 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.144-1
- Update 2025-04-19T18:02:08Z (supervisor@karellen.co)

* Tue Apr 15 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.142-1
- Update 2025-04-15T18:02:25Z (supervisor@karellen.co)

* Mon Apr 14 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.141-1
- Update 2025-04-14T18:02:41Z (supervisor@karellen.co)

* Sun Apr 13 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.139-1
- Update 2025-04-13T18:02:24Z (supervisor@karellen.co)

* Thu Mar 27 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.137-1
- Update 2025-03-27T12:03:17Z (supervisor@karellen.co)

* Thu Mar 20 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.134-1
- Update 2025-03-20T18:02:33Z (supervisor@karellen.co)

* Mon Mar 17 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.129-1
- Update 2025-03-17T12:03:15Z (supervisor@karellen.co)

* Fri Mar 14 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.124-1
- Update 2025-03-14T18:02:23Z (supervisor@karellen.co)

* Mon Feb 24 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.122-1
- Update 2025-02-24T18:02:38Z (supervisor@karellen.co)

* Sat Feb 15 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.120-1
- Update 2025-02-15T18:02:08Z (supervisor@karellen.co)

* Wed Feb 05 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.119-1
- Update 2025-02-05T18:02:33Z (supervisor@karellen.co)

* Mon Feb 03 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.118-1
- Update 2025-02-03T00:07:33Z (supervisor@karellen.co)

* Sun Feb 02 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.117-1
- Update 2025-02-02T18:02:13Z (supervisor@karellen.co)

* Sun Jan 26 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.113-1
- Update 2025-01-26T18:02:20Z (supervisor@karellen.co)

* Fri Jan 24 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.111-1
- Update 2025-01-24T18:02:24Z (supervisor@karellen.co)

* Wed Jan 15 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.109-1
- Update 2025-01-15T12:03:09Z (supervisor@karellen.co)

* Thu Jan 02 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.108-1
- Update 2025-01-02T18:02:35Z (supervisor@karellen.co)

* Thu Jan 02 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.106-1
- Update 2025-01-02T12:03:06Z (supervisor@karellen.co)

* Wed Jan 01 2025 Karellen Supervisor <supervisor@karellen.co> 7.5.105-1
- Update 2025-01-01T12:03:06Z (supervisor@karellen.co)

* Tue Dec 10 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.104-1
- Update 2024-12-10T18:02:38Z (supervisor@karellen.co)

* Fri Dec 06 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.102-1
- Update 2024-12-06T12:03:13Z (supervisor@karellen.co)

* Mon Dec 02 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.101-1
- Update 2024-12-02T00:08:38Z (supervisor@karellen.co)

* Sat Nov 30 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.100-1
- Update 2024-11-30T18:02:24Z (supervisor@karellen.co)

* Wed Nov 20 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.99-1
- Update 2024-11-20T18:02:35Z (supervisor@karellen.co)

* Wed Nov 20 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.97-1
- Update 2024-11-20T12:03:22Z (supervisor@karellen.co)

* Mon Nov 18 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.96-1
- Update 2024-11-18T18:02:34Z (supervisor@karellen.co)

* Sun Nov 17 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.95-1
- Update 2024-11-17T18:02:11Z (supervisor@karellen.co)

* Sat Nov 16 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.94-1
- Update 2024-11-16T06:02:29Z (supervisor@karellen.co)

* Wed Nov 13 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.93-1
- Update 2024-11-13T12:03:13Z (supervisor@karellen.co)

* Tue Nov 12 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.92-1
- Update 2024-11-12T18:02:26Z (supervisor@karellen.co)

* Sat Oct 26 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.91-1
- Update 2024-10-26T12:03:25Z (supervisor@karellen.co)

* Wed Oct 23 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.89-1
- Update 2024-10-23T18:02:39Z (supervisor@karellen.co)

* Wed Oct 16 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.85-1
- Update 2024-10-16T22:27:23Z (supervisor@karellen.co)

* Wed Oct 16 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.83-1
- Update 2024-10-16T12:03:03Z (supervisor@karellen.co)

* Tue Oct 15 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.82-1
- Update 2024-10-15T18:02:23Z (supervisor@karellen.co)

* Tue Oct 15 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.81-1
- Update 2024-10-15T12:03:04Z (supervisor@karellen.co)

* Sat Oct 05 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.79-1
- Update 2024-10-05T12:02:50Z (supervisor@karellen.co)

* Sun Sep 29 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.78-1
- Update 2024-09-29T18:02:06Z (supervisor@karellen.co)

* Mon Sep 23 2024 Karellen Supervisor <supervisor@karellen.co> 7.5.77-1
- Update 2024-09-23T18:02:19Z (supervisor@karellen.co)
- Fix regex (arcadiy@ivanov.biz)
- Update actions based on karellen-sysbox (arcadiy@ivanov.biz)
- Add branch following (arcadiy@ivanov.biz)
- Add auto-updater (arcadiy@ivanov.biz)

* Sat May 11 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.75-1
- Update 2024-05-11 (arcadiy@ivanov.biz)

* Sat May 04 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.74-1
- Update 2024-05-04 (arcadiy@ivanov.biz)

* Sat Apr 20 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.73-1
- Update 20240420 (arcadiy@ivanov.biz)

* Wed Mar 27 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.63-1
- Update 2024-03-27 (arcadiy@ivanov.biz)

* Fri Jan 26 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.62-1
- Update 20240126 (arcadiy@ivanov.biz)

* Sun Jan 07 2024 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.41-1
- Update 20240107 (arcadiy@ivanov.biz)

* Fri Dec 29 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.36-1
- Update 20231229 (arcadiy@ivanov.biz)

* Sat Dec 16 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.29-1
- Update 2023-12-16 (arcadiy@ivanov.biz)

* Mon Oct 16 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.23-1
- Update 2023-10-16 (arcadiy@ivanov.biz)

* Tue Sep 12 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.16-1
- Update 2023-09-12 (arcadiy@ivanov.biz)

* Thu Aug 24 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.5.5-1
- Use AC_INIT in configure.ac to detect the version (arcadiy@ivanov.biz)
- Update 20230824 Add Vendor information (arcadiy@ivanov.biz)
- Update 20230801 (arcadiy@ivanov.biz)

* Mon Jul 31 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.177-1
- Update 20230731 (arcadiy@ivanov.biz)

* Mon Jul 31 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.176-1
- Update 20230730 (arcadiy@ivanov.biz)

* Sat Jul 29 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.175-1
- Update 20230729 (arcadiy@ivanov.biz)

* Thu Jul 27 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.173-1
- Update 20230727 (arcadiy@ivanov.biz)

* Fri Jul 21 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.155-2
- Add Provides for packages dependent on smartmontools (arcadiy@ivanov.biz)

* Fri Jul 21 2023 Arcadiy Ivanov <arcadiy@ivanov.biz>
- Add Provides for packages dependent on smartmontools (arcadiy@ivanov.biz)

* Mon Jul 17 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.155-1
- Update 2023-07-17 (arcadiy@ivanov.biz)

* Sat Jul 01 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.139-2
- SubmoduleAwareBuilder has been fixed in tito 0.6.23 (arcadiy@ivanov.biz)

* Sat Jul 01 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.139-1
- Update to latest 2023-07-01 (arcadiy@ivanov.biz)

* Sat Jul 01 2023 Arcadiy Ivanov <arcadiy@ivanov.biz> 7.4.138-1
- new package built with tito

* Wed Apr 05 2023 Michal Hlavinka <mhlavink@redhat.com> - 1:7.3-6
- update license tag format (SPDX migration) for https://fedoraproject.org/wiki/Changes/SPDX_Licenses_Phase_1

* Sat Jan 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Jan 04 2023 Michal Hlavinka <mhlavink@redhat.com> - 1:7.3-4
- fix selinux directory permissions

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Wed Mar 09 2022 Michal Hlavinka <mhlavink@redhat.com> - 1:7.3-2
- use --capabilities=mail for exim mail notification (#2060526)

* Tue Mar 01 2022 Michal Hlavinka <mhlavink@redhat.com> - 1:7.3-1
- updated to 7.3

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.2-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Tue Nov 02 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-11
- fix /dev/megaraid_sas_ioctl_node mknode permissions (#1936824)

* Mon Aug 23 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-10
- more selinux fixes

* Mon Aug 16 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-9
- selinux should allow access to nvme devices (#1990463)

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jun 16 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-7
- make notification work with capabilities (#1954015)

* Wed Apr 28 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-6
- simplify selinux policy path for ci tests

* Mon Apr 19 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-5
- add selinux sub-package

* Tue Mar 02 2021 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 1:7.2-4
- Rebuilt for updated systemd-rpm-macros
  See https://pagure.io/fesco/issue/2583.

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 25 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-2
- make sure correct version of drivedb.h is used (#1918946)

* Mon Jan 18 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.2-1
- smartmontools updated to 7.2

* Mon Jan 18 2021 Michal Hlavinka <mhlavink@redhat.com> - 1:7.1-10
- use capabilites by default

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.1-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Jan 06 2020 Michal Hlavinka <mhlavink@redhat.com> - 1:7.1-7
- smartmontools updated to 7.1

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Apr 12 2019 Daniel Axelrod <daxelrod@datto.com> - 1:7.0-6
- Remove unused patches
- Drop pre script for migrating from unsupported Fedora versions
- Replace sed with configure switch

* Wed Apr 03 2019 Michal Hlavinka <mhlavink@redhat.com> - 1:7.0-5
- revert smartd_warning related changes

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:7.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Jan 03 2019 Michal Hlavinka <mhlavink@redhat.com> - 1:7.0-3
- update default config

* Thu Jan 03 2019 Michal Hlavinka <mhlavink@redhat.com> - 1:7.0-2
- use smartd_warning plugin to notify users (bug #1647534)
- spec cleanup

* Thu Jan 03 2019 Michal Hlavinka <mhlavink@redhat.com> - 1:7.0-1
- smartmontools updated to 7.0

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Mar 07 2018 Michal Hlavinka <mhlavink@redhat.com> - 1:6.6-4
- add gcc-c++ buildrequire

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Nov 07 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1:6.6-2
- Remove old crufty coreutils requires

* Mon Nov 06 2017 Michal Hlavinka <mhlavink@redhat.com> - 1:6.6-1
- smartmontools updated to 6.6

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Nov 11 2016 Michal Hlavinka <mhlavink@redhat.com> - 1:6.5-2
- enable location for persistence data(#1291928)

* Mon May 09 2016 Michal Hlavinka <mhlavink@redhat.com> - 1:6.5-1
- smartmontools updated to 6.5

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jun 23 2015 Michal Hlavinka <mhlavink@redhat.com> - 1:6.4-3
- it is no longer necessary to do utf-8 conversion of the AUTHORS and ChangeLog (#1228825)

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:6.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Jun 05 2015 Michal Hlavinka <mhlavink@redhat.com> - 1:6.4-1
- smartmontools updated to 6.4

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1:6.3-4
- Rebuilt for GCC 5 C++11 ABI change

* Wed Jan 14 2015 Michal Hlavinka <mhlavink@redhat.com> - 1:6.3-3
- do not require sendmail

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:6.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Mon Aug 04 2014 Michal Hlavinka <mhlavink@redhat.com> - 1:6.3-1
- smartmontools updated to 6.3

* Thu Jul 17 2014 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-7
- update drivedb database (#954162)

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:6.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Apr 17 2014 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-5
- require /usr/sbin/sendmail as MTA is not provided by all packages (#1048618)

* Tue Apr 15 2014 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-4
- use MTA instead of sendmail as a requirement (#1048614)

* Thu Apr 10 2014 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-3
- add mail requires (#1048614)

* Mon Sep 16 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-2
- smartd service file wrong path to environment file (#998225)

* Tue Jul 30 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-1
- smartmontools updated to 6.2

* Mon Jul 22 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.1-2
- spec cleanup

* Wed Mar 20 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.1-1
- smartmontools updated to 6.1

* Fri Feb 15 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Oct 11 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:6.0-1
- smartmontools updated to 6.0

* Tue Aug 21 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:5.43-3
- use new systemd rpm macros (#850316)

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.43-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 02 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:5.43-1
- smartmontools updated to 5.43

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.42-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Dec 02 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.42-2
- enable smartd after installation

* Fri Oct 21 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.42-1
- smartmontools updated to 5.42

* Mon Jun 13 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.41-2
- make F-14 (sysv init) -> F-15 (systemd) transition more robust

* Fri Jun 10 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.41-1
- updated to 5.41

* Mon May 16 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-10
- fix path to notify script (#675778)

* Fri Mar 11 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-9
- fix typos in man page

* Fri Mar 04 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-8
- don't call chkconfig add, we use systemd now
 
* Thu Mar 03 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-7
- own %%{_datadir}/%%{name} and %%{_libexecdir}/%%{name} dirs

* Thu Feb 17 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-6
- notify users when disk is failing

* Wed Feb 09 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-5
- move to systemd

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.40-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Nov 15 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-3
- megaraid: Fix segfault on non-data commands (#577935)

* Tue Nov 09 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-2
- don't forget to restart smartd service after update (#651211)

* Mon Oct 18 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-1
- updated to 5.40 final

* Mon Sep 27 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39.1-2.r3169
- updated to r3169
- ddds riverdb support for new devices (#637171)

* Fri Jan 29 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39.1-1
- updated to 5.39.1
- Fix spin-up of SATA drive if '-n standby' is used.

* Wed Jan 20 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-2
- fix DEVICESCAN -d sat
- fix directive '-l selftest'
- fix option '-q, --quietmode'

* Thu Dec 10 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-1
- update to 5.39

* Wed Dec 02 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-0.1.rc1
- update to 5.39-rc1

* Wed Nov 25 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-25.20091119svn
- spec cleanup

* Mon Nov 23 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-24.20091119svn
- move powermode option from sysconfig to smartd.conf (#539760)

* Thu Nov 19 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-23.20091119svn
- update to svn snapshot 2009-11-19
- remove upstreamed patches

* Mon Nov 02 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-22
- spec cleanup

* Mon Oct 12 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-21 
- warn about disabled mail only if capabilities are enabled

* Fri Oct 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-20
- fix init script for case when no action was specified

* Fri Oct 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-19
- make init script lsb compliant (#528016)

* Mon Oct 05 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-18
- bump release for rebuild

* Mon Oct 05 2009 Michal Hlaivnka <mhlavink@redhat.com> - 1:5.38-17
- make capabilities optional
- fix capabilities for 3ware contollers (#526626)

* Wed Aug 26 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-16
- extend capability scanning devices

* Wed Aug 26 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-15
- updated patch for lower capabilities (#517728)
- added buildrequires libcap-ng-devel

* Fri Aug 21 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-14
- drop all unnecessary capabilities (#517728)

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.38-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jun 11 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-12
- drop autogen call 

* Sat Apr 11 2009 Dennis Gilmore <dennis@ausil.us> - 1:5.38-11
- remove ExclusiveArch use -fPIE on sparc64  
- tested builds on sparcv9 sparc64 and s390x

* Mon Mar 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-10
- cleanup for merge review

* Fri Feb 27 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 1:5.38-9
- fix ExclusiveArch

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.38-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Aug 11 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-7
- fix #458549 - obsolete smartmontools-config
- change the default configuration file

* Fri Aug 08 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-6
- correct CXXFLAGS so the PIE code is produced

* Mon May 12 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-5
- remove config subpackage

* Mon May 05 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-4.1
- add libselinux-devel to BR

* Mon May 05 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-4
- fix #232218 character devices /dev/twa* for 3ware 9000 series RAID
  controllers are not created

* Thu Mar 27 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-3
- don't attempt to query DELL PERC controllers -- they'd go offline

* Tue Mar 18 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-2
- fix FD_CLOEXEC on SCSI device file descriptors not being set

* Mon Mar 10 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-1
- new upstream version

* Tue Feb 12 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.5
- rebuild (gcc-4.3)

* Tue Jan 15 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.4
- change '-d ata' to '-d sat' in the config script for SATA drives

* Wed Dec 12 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.3
- fix #375791 - parameter warning for smartd in logwatch output

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.2
- rebuild (one more error in autogen.sh)

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.1
- fix build with new automake

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8
- fix #359561 - typo in smartd-conf.py causes smartd to skip all disks

* Mon Oct 15 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-7.1
- improved patch for getaddrinfo

* Fri Oct 12 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-7
- replace gethostbyname with getaddrinfo

* Tue Sep 04 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-6
- fix #271741 - smartd-conf.py should allow customization of parameters
- fix #253753 - service starting by default, perhaps shouldn't
- update initscript (related #247058 - initscript review)

* Mon Aug 20 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-5
- add support for 24 disks on 3ware RAID controllers (related #252055)
- fix #245442 - add %%{arm} to smartmontools's set of build archs
- update license tag

* Thu Jun 21 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-4
- fix #241389 - smartd-conf.py pulls in a big dependency chain, so
  build a separate config package
  
* Tue Jun 05 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-3
- fix #241385 - smartmontools missing dependency on mailx
- fix #241388 - unneeded smartd-conf.py[co] installed in /usr/sbin

* Wed Mar  7 2007 Vitezslav Crhonek <vcrhonek@redhat.com> - 1:5.37-2
- re-add cloexec patch
- re-add one erased changelog entry
- compile with -fpie (instead of -fpic)

* Tue Feb 27 2007 Vitezslav Crhonek <vcrhonek@redhat.com> - 1:5.37-1
- new upstream version

* Thu Feb 22 2007 Tomas Mraz <tmraz@redhat.com> - 1:5.36-8
- enable SMART on disks when smartd-conf.py runs (fix
  by Calvin Ostrum) (#214502)

* Mon Feb 12 2007 Tomas Mraz <tmraz@redhat.com> - 1:5.36-7
- redirect service script output to null (#224566)

* Sun Feb 11 2007 Florian La Roche <laroche@redhat.com> - 1:5.36-6
- make sure the preun script does not fail

* Tue Nov  7 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-5
- set cloexec on device descriptor so it doesn't leak to sendmail (#214182)
- fixed minor bug in initscript (#213683)
- backported SATA disk detection from upstream

* Fri Aug 18 2006 Jesse Keating <jkeating@redhat.com> - 1:5.36-3
- rebuilt with latest binutils to pick up 64K -z commonpagesize on ppc*
  (#203001)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 1:5.36-2.1
- rebuild

* Tue Jun 27 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-2
- kudzu is deprecated, replace it with HAL (#195752)
- moved later in the boot process so haldaemon is already running
  when drives are being detected

* Thu May 11 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-1
- new upstream version
- included patch with support for cciss controllers (#191288)

* Tue May  2 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-8
- regenerate smartd.conf on every startup if the config file
  is autogenerated (#190065)

* Fri Mar 24 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-7
- add missing quotes to /etc/sysconfig/smartmontools

* Wed Mar 22 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-6
- test SATA drives correctly

* Wed Mar 22 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-5
- add default /etc/sysconfig/smartmontools file
- ignore errors on startup (#186130)
- test drive for SMART support before adding it to smartd.conf

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 1:5.33-4.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 1:5.33-4.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Fri Dec 16 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-4
- mail should be sent to root not root@localhost (#174252)

* Fri Nov 25 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-3
- add libata disks with -d ata if the libata version
  is new enough otherwise do not add them (#145859, #174095)

* Thu Nov  3 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-2
- Spec file cleanup by Robert Scheck <redhat@linuxnetz.de> (#170959)
- manual release numbering
- remove bogus patch of non-installed file
- only non-removable drives should be added to smartd.conf
- smartd.conf should be owned (#171498)

* Tue Oct 25 2005 Dave Jones <davej@redhat.com>
- Add comments to generated smartd.conf (#135397)

* Thu Aug 04 2005 Karsten Hopp <karsten@redhat.de>
- package all python files

* Tue Mar  1 2005 Dave Jones <davej@redhat.com>
- Rebuild for gcc4

* Wed Feb  9 2005 Dave Jones <davej@redhat.com>
- Build on PPC32 too (#147090)

* Sat Dec 18 2004 Dave Jones <davej@redhat.com>
- Initial packaging, based upon kernel-utils.

