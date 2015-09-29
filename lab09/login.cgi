#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

#run application if script is being run from command line
authenticate_user_application() if !grep(/^HTTP/, `env`);

print header, start_html('Login');
warningsToBrowser(1);

#obtains input parameters
$username = param('username') || '';
$password = param('password') || '';

#authenticates user if both parameters are supplied
if ($username && $password) {

	#checks whether user exists
	if (! -e "../accounts/$username") {
		print "Unknown username!\n";
		exit 1;
	}

	#proceeds if password file is accessible
	if (-r "../accounts/$username/password") {
		open P, "../accounts/$username/password";
		@lines = <P>;
		close P;
		chomp $lines[0];

		#checks supplied password
		if ($lines[0] eq $password) {
			print "$username authenticated.\n";
			print end_html;
			exit 0;
		} else {
			print "Incorrect password!\n";
		}

	}

	print end_html;
	exit 1;
}

print start_form, "\n";

#requests unknown parameter(s) and passes known parameter as a hidden variable
if ($username) {
	print '<input type="hidden" name="username" value=', "$username>", "\n";
	print "Password:\n", textfield('password'), "\n";
} elsif ($password) {
	print '<input type="hidden" name="password" value=', "$password>", "\n";
	print "Username:\n", textfield('username'), "\n";
} else {
	print "Username:\n", textfield('username'), "\n";
	print "Password:\n", textfield('password'), "\n";
}

print submit(value => Login), "\n";
print end_form, "\n";
print end_html;
exit 0;

#authenticates user as command line application
sub authenticate_user_application {
	#reads in username and password
	print "username: ";
	my $user = <>;
	chomp $user;
	print "password: ";
	my $pass = <>;
	chomp $pass;

	#checks whether user exists
	if ($user eq "" || ! -e "../accounts/$user") {
		print "Unknown username!\n";
		exit 1;
	}

	#reads in password file
	open F, "../accounts/$user/password" or die $!;
	my @lines = <F>;
	close F;
	chomp $lines[0];

	#attempts to authenticate user
	if ($lines[0] eq $pass){
	        print "You are authenticated.\n";
		exit 0;
	} else {
	        print "Incorrect password!\n";
		exit 1;
	}

}
