open(F, "ztricks3.cfg-bad");
while ($line = <F>) {
        $line =~ s/[\r\n]$//g;
	@args = $line =~ /^(\w+) (.*) (\w+) (\S+)$/;
	print join("\t", @args)."\r\n";
}

