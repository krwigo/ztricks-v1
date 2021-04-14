print "INFO version 1\r\n";
print "INFO date ".time()."\r\n";

foreach $f ("triggers.conf2", "tricks.conf2") {
	open(F, $f);

	($master) = $f =~ /^(.*)\.conf2/;
	$section='unknown';

	while ($line = <F>) {
		$line =~ s/[\r\n]$//g;
		if ($line =~ /^\[(.*)\]$/) { $section = $1;next; }

		if ($line =~ /^(.*?)=(.*)$/) {
			($name, $value) = ($1, $2);
			print "$master\t$section\t$name\t$value\r\n";
		}
	}

	close(F);
}
