#!/usr/bin/perl -w

#validates each credit card number supplied
foreach $arg (@ARGV) {
	print validate($arg);
}

#validates a given credit card number
sub validate {
	my $number = $_[0];
	$number =~ s/\D//g; #ensures only digits are checked
	if (length($number) ne 16) {
		return "$_[0] is invalid - does not contain exactly 16 digits\n";
	} elsif (luhn_checksum($number) % 10 eq 0) {
		return "$_[0] is valid\n";
	} else {
		return "$_[0] is invaid\n";
	}
}

#computes the luhn checksum of a given credit card number
sub luhn_checksum {
	my $checksum = 0;
	my @digits = split //, $_[0];
	@digits = reverse(@digits);
	my $index = 0;

	#iterates through each digit
	for ($index..$#digits) {
		#applies formula to current digit
		my $multiplier = 1 + ($index % 2);
		my $d = int($digits[$index]) * $multiplier;

		$d -= 9 if ($d > 9); #wraps product if greater than 9
		$checksum += $d;
		$index++;
	}

	return $checksum;
}
