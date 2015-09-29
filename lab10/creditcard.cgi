#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

print header, start_html("Credit Card Validation"), "\n";
warningsToBrowser(1);
my $credit_card = param("credit_card");
my $close = param("close");
print "<h2>Credit Card Validation</h2>\n";

#displays goodbye page if user selects close button
if (defined $close) {
	print "Thank you for using the Credit Card Validator.\n";
	print end_html;
	exit 0;
}

#prints welcome message
print "This page checks whether a potential credit card number satisfies the Luhn Formula.";
print "\n<p>\n<form>\n";

#checks whether user has selected submit button
if (defined $credit_card) {
	my $validity = validate($credit_card);

	#prints validity status
	if ($validity =~ /invalid/) {
		print '<b><span style="color:red">', $validity, "</span></b>\n<p>\n";
		print "Try again:", "\n";

		#reprints provided credit card number in input field
		if ($credit_card eq "") {
			print '<input name="credit_card" value="" type="text">', "\n";
		} else {
			$credit_card =~ s/\D//g;
			print '<input name="credit_card" value=', $credit_card, ' type="text">', "\n";
		}

	} else {
		#prompts for another credit card number if current is valid
		print $validity, "\n<p>\n";
		print "Another card number:", "\n";
		print '<input name="credit_card" value="" type="text">', "\n";
	}

} else {
	print "Enter credit card number:\n";
	print '<input name="credit_card" value="" type="text">', "\n";
}

#prints rest of input form
print '<input name="submit" value="Validate" type="submit">', "\n";
print '<input name="Reset" value="Reset" type="reset">', "\n";
print '<input name="close" value="Close" type="submit">', "\n";
print "</form>\n";

print end_html;
exit 0;

#validates a given credit card number
sub validate {
	my $number = $_[0];
	$number =~ s/\D//g; #ensures only digits are checked
	if (length($number) ne 16) {
		return "$number is invalid - does not contain exactly 16 digits";
	} elsif (luhn_checksum($number) % 10 eq 0) {
		return "$number is valid";
	} else {
		return "$number is invalid";
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
