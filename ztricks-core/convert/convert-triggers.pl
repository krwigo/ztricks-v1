#!/usr/bin/perl
unless(open(FILE, @ARGV[0])) { print "unable to open: $!\n";exit; }
while ($line=<FILE>) {
	$line =~ s/[\r\n]$//g;
	$line =~ s/\t\t/\t/g;
	@words=split(/\t/, $line);
	%out=();

	if (@words[0] eq "trig_sphere" || @words[0] eq "trig_sphere_sym") {
		$out{enabled}="True";
		$out{shape}="sphere";
		$out{id}=@words[1];
		$out{coord1}=@words[2];
		$out{radius}=@words[3];
		$out{height}=@words[4] if @words[4] ne "-";
		$out{wasdfr}=@words[5] if @words[5] ne "-";
		$out{name}=@words[6];
		$out{symetrical}="True" if @words[0] eq "trig_sphere_sym";
	}
	if (@words[0] eq "trigger" || @words[0] eq "trig_sym") {
		$out{enabled}="True";
		$out{shape}="box";
		$out{id}=@words[1];
		$out{coord1}=@words[2];
		$out{coord2}=@words[3];
		$out{wasdfr}=@words[4] if @words[4] ne "-";
		$out{name}=@words[5];
		$out{symetrical}="True" if @words[0] eq "trig_sym";
	}

	#print "LINE: $line\n";

	if (keys %out > 0) {
		print "[".$out{name}."]\n";
		foreach $key (keys %out) {
			next if $key eq "name";
			print "$key = ".$out{$key}."\n";
		}
		print "\n";
	}
}

