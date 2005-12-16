Summary:	Tools for monitoring SMART capable hard disks
Name:		smartmontools
Version:	5.33
Release: 	4
Epoch:		1
Group:		System Environment/Base
License:	GPL
URL:		http://smartmontools.sourceforge.net/
Source0:	http://dl.sourceforge.net/sourceforge/%{name}/%{name}-%{version}.tar.gz
Source1:	smartd.initd
Source2:	smartd-conf.py
BuildRoot:	%{_tmppath}/%{name}-%{version}-root
PreReq:		/sbin/chkconfig /sbin/service
Requires:	fileutils kudzu
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

%build
%configure
make CFLAGS="$RPM_OPT_FLAGS -fpie" LDFLAGS="-pie -Wl,-z,relro,-z,now"

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

rm -f $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/smartd.conf
rm -f examplescripts/Makefile*
install -D -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/smartd
install -D -m 755 %{SOURCE2} $RPM_BUILD_ROOT%{_sbindir}/smartd-conf.py

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

%preun
if [ "$1" = "0" ] ; then
 /sbin/service smartd stop
 /sbin/chkconfig --del smartd
fi

%post
/sbin/chkconfig --add smartd

%triggerpostun -- kernel-utils
/sbin/chkconfig --add smartd
exit 0


%changelog
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

