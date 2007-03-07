Summary:	Tools for monitoring SMART capable hard disks
Name:		smartmontools
Version:	5.37
Release: 	2%{?dist}
Epoch:		1
Group:		System Environment/Base
License:	GPL
URL:		http://smartmontools.sourceforge.net/
Source0:	http://prdownloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Source1:	smartd.initd
Source2:	smartd-conf.py
Source3:	smartmontools.sysconf
Patch1:		smartmontools-5.37-cloexec.patch

BuildRoot:	%{_tmppath}/%{name}-%{version}-root
PreReq:		/sbin/chkconfig /sbin/service
Requires:	fileutils hal >= 0.5.2 dbus-python >= 0.33
BuildRequires: 	readline-devel ncurses-devel /usr/bin/aclocal /usr/bin/automake /usr/bin/autoconf util-linux groff gettext
Obsoletes:	kernel-utils
ExclusiveArch:	i386 x86_64 ia64 ppc ppc64

%description
The smartmontools package contains two utility programs (smartctl
and smartd) to control and monitor storage systems using the Self-
Monitoring, Analysis and Reporting Technology System (SMART) built
into most modern ATA and SCSI hard disks. In many cases, these 
utilities will provide advanced warning of disk degradation and
failure.

%prep
%setup -q
%patch1 -p1 -b .cloexec

%build
%configure
make CFLAGS="$RPM_OPT_FLAGS -fpie" LDFLAGS="-fpie -Wl,-z,relro,-z,now"

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

rm -f $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/smartd.conf
rm -f examplescripts/Makefile*
install -D -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/smartd
install -D -m 755 %{SOURCE2} $RPM_BUILD_ROOT%{_sbindir}/smartd-conf.py
install -D -m 644 %{SOURCE3} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/smartmontools

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS CHANGELOG COPYING INSTALL NEWS README
%doc TODO WARNINGS examplescripts smartd.conf
%{_sbindir}/smartd
%{_sbindir}/smartctl
%{_sbindir}/smartd-conf.py*
%{_sysconfdir}/rc.d/init.d/smartd
%{_mandir}/man?/smart*.*
%ghost %verify(not md5 size mtime) %config(noreplace,missingok) %{_sysconfdir}/smartd.conf
%config(noreplace) %{_sysconfdir}/sysconfig/smartmontools

%preun
if [ "$1" = "0" ] ; then
 /sbin/service smartd stop >/dev/null 2>&1
 /sbin/chkconfig --del smartd
fi
exit 0

%post
/sbin/chkconfig --add smartd

%triggerpostun -- kernel-utils
/sbin/chkconfig --add smartd
exit 0


%changelog
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

