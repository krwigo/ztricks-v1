#!/usr/bin/perl
# 2021.04.13

chdir "/pub";
@cmd = ("git", "clone", "https://github.com/krwigo/ztricks-v1");
print "\$ @cmd\n";
system(@cmd) if !-d "/pub/ztricks-v1";

foreach $src (</pub/src/*>) {
	($_, $branch) = $src =~ /(.*)\/(.*)/;
	print "-------------------------------------------------------------------------------\n";
	print "found [$branch] at [$src]\n";

	chdir "/pub/ztricks-v1/";

	# branch reset
	@cmd = ("git", "checkout", "main");
	print "\$ @cmd\n";
	system(@cmd);
	system("ls -l");

	# branch create
	@cmd = ("git", "checkout", "-B", $branch);
	print "\$ @cmd\n";
	system(@cmd);
	system("ls -l");

	# copy
	opendir(D, $src);
	while ($obj = readdir(D)) {
		next if $obj eq "." or $obj eq "..";
		@cmd = ("cp", "-r", "$src/$obj", ".");
		print "\$ @cmd\n";
		system(@cmd);
	}
	closedir(D);

	# add
	@cmd = ("git", "add", "-A");
	print "\$ @cmd\n";
	system(@cmd);

	# status
	@cmd = ("git", "status");
	print "\$ @cmd\n";
	system(@cmd);

	# commit
	@cmd = ("git", "commit", "-m", $branch);
	print "\$ @cmd\n";
	system(@cmd);

	# cleanup
	opendir(D, $src);
	while ($obj = readdir(D)) {
		next if $obj eq "." or $obj eq "..";
		@cmd = ("rm", "-rf", "/pub/ztricks-v1/$obj");
		print "\$ @cmd\n";
		system(@cmd);
	}
	closedir(D);
}

# git checkout main
# git add .
# git commit -m "reason"
# git push

