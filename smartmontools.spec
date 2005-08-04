Summary:        Tools for monitoring SMART capable hard disks.
Name:           smartmontools
Version:        5.33
Release: 	%(R="$Revision: 1.5 $"; RR="${R##: }"; echo ${RR%%?})
Epoch:		1
Group:          System Environment/Base
License:        GPL
Source0: 	smartmontools-5.33.tar.gz
Source1:	smartd.initd
Source2:	smartd-conf.py
Buildroot:      %{_tmppath}/%{name}-%{version}-root
Prereq:		/sbin/chkconfig /sbin/service
Requires:	fileutils kudzu
BuildPreReq: 	readline-devel ncurses-devel /usr/bin/aclocal /usr/bin/automake /usr/bin/autoconf util-linux groff gettext
Obsoletes:	kernel-utils
ExclusiveArch:	i386 x86_64 ia64 ppc ppc64

Patch1: smartmontools-smartd.patch

%description
smartctl - monitor the health of your disks


%prep
%setup -q -c -a 0
%patch1 -p0

%build
rm -rf $RPM_BUILD_ROOT

mkdir -p %{buildroot}/usr/sbin
mkdir -p %{buildroot}/usr/man
mkdir -p %{buildroot}/etc/rc.d/init.d
mkdir -p %{buildroot}/etc/sysconfig

cd smartmontools-5.33
%configure
make CFLAGS="$RPM_OPT_FLAGS -fpie -pie -Wl,-z,relro,-z,now" DESTDIR=$RPM_BUILD_ROOT smartd smartctl install

%install
mkdir -p %{buildroot}/usr/share/man/man{1,8}

cd smartmontools-5.33
rm -f %{buildroot}/etc/smartd.conf
rm -f %{buildroot}/etc/rc.d/init.d/smartd.conf
install %{SOURCE1} %{buildroot}/etc/rc.d/init.d/smartd
install %{SOURCE2} %{buildroot}/usr/sbin/smartd-conf.py

chmod -R a-s %{buildroot}

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;

%files
%defattr(-,root,root)
%attr(0644,root,root) %{_mandir}/*/*
/usr/sbin/smartd
/usr/sbin/smartctl
/usr/sbin/smartd-conf.py?
/etc/rc.d/init.d/smartd
%doc /usr/share/doc/smartmontools-5.33

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
* Thu Aug 04 2005 Karsten Hopp <karsten@redhat.de>
- package all python files

* Tue Mar  1 2005 Dave Jones <davej@redhat.com>
- Rebuild for gcc4

* Wed Feb  9 2005 Dave Jones <davej@redhat.com>
- Build on PPC32 too (#147090)

* Sat Dec 18 2004 Dave Jones <davej@redhat.com>
- Initial packaging, based upon kernel-utils.

