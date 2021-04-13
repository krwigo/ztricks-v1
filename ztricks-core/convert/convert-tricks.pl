#!/usr/bin/perl
unless(open(FILE, @ARGV[0])) { print "unable to open: $!\n";exit; }
$newid=1000;
while ($line=<FILE>) {
	$line =~ s/[\r\n]$//g;
	@words=split(/\t+/, $line);
	%out=();

	if (@words[0] eq "trickv2") {
		$out{path}=@words[1];
		$out{pass}=@words[2] if @words[2] ne "-";
		$out{points}=@words[3];
		$out{name}=@words[4];
		$out{id}=$newid++;
	} else {
		next;
	}

#	print "LINE: $line\n";

	if (keys %out > 0) {
		print "[".$out{name}."]\r\n";
		foreach $key (keys %out) {
			next if $key eq "name";
			print "$key = ".$out{$key}."\r\n";
		}
		print "\r\n";
	}
}

