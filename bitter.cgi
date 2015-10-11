#!/usr/bin/perl -w
#Written by Constantinos Paraskevopoulos in October 2015
#Provides a social media platform analogous to Twitter

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

print page_header();
warningsToBrowser(1);
$debug = 1;

#declares global variables relating to user data
$dataset_size = "medium";
$users_dir = "dataset-$dataset_size/users";
$bleats_dir = "dataset-$dataset_size/bleats";

$token = param('token');

#main bitter hierarchy logic
if (defined $token) {
	$token =~ s/[^\w\-]//g; #removes unexpected chars from token
	$token_file = "tokens/$token";

	#checks that token is valid and has been issued within the last day
	if (length($token) > 30 && -e $token_file && -M $token_file < 1) {

		#navigates to appropriate page based on user's request
		if (defined param('next')) {
			display_user_profile();
		} else {
			display_login_form();
		}

	}

} elsif (defined param('login')) {
		if (authenticate_user(param('username'), param('password'))) {
			#generates unique 64-bit uuid
			$token = `uuidgen`;
			chomp $token;

			#stores token in direcotry
			$token_file = "$token";
			open TOKEN, ">tokens/$token" or die "Unable to write tokens/$token: $!";
			close TOKEN;

			display_user_profile();
		} else {
			wrong_credentials();
		}
} elsif (defined param('reset')) {
	#allows user to reset password
	print "This page is a placeholder.\n";
} else {
	#authenticates user for first time
	display_login_form();
}

print page_trailer();
exit 0;

#validates user login credentials
sub authenticate_user {
	my ($username, $password) = @_;
	$username =~ s/\W\D//g; #sanitises user login
	return 0 if length($username) eq 0 || length($password) eq 0;
	my $details_filename = "$users_dir/$username/details.txt";
	return 0 if ! -e $details_filename; #checks whether user exists

	#opens user details and extracts stored password
	open USER, "$details_filename" or die "Cannot open $details_filename: $!";
	foreach (<USER>) {
		$expected_password = $1 if $_ =~ /^password: (.+)/;
	}

	close USER;
	return 1 if $password eq $expected_password; #checks validity of password
	return 0;
}

#produces a user login form
sub display_login_form {
	print <<eof;
<center>
<form method="POST" action="">
<table cellpadding="2">
  <tr><td>Username</td></tr>
  <tr><td><input type="text" name="username"></td></tr>
  <tr><td>Password</td></tr>
  <tr><td><input type="password" name="password"></td></tr>
</table>
<p>
<input type="submit" name="login" value="Login" class="bitter_button">
<input type="submit" name="reset" value="Reset password" class="bitter_button">
</form>
</center>
eof
}

#displays error message and prompts for re-authentication
sub wrong_credentials {
	print <<eof;
<center>
<font color='red'>Incorrect username or password.</font>
</center>
<br>
eof
	display_login_form();
}

#shows formatted details of a user's profile
sub display_user_profile {
	my $n = param('n') || 0;
	my @users = sort(glob("$users_dir/*"));

	#stores paths to user's profile entities
	my $user_to_show  = $users[$n % @users];
	my $details_filename = "$user_to_show/details.txt";
	my $image_filename = "profile_default.jpg"; #default profile image
	my $bleats_filename = "$user_to_show/bleats.txt";

	#updates profile image from default if a profile image is available
	my @profile_image = glob("$user_to_show/profile.*");
	$image_filename = $_ foreach (@profile_image);

	#obtains and prints the user's profile
	print user_details($details_filename, $image_filename);
	print user_bleats($bleats_filename);

	my $next_user = $n + 1;

	#prints form to move to next user
	print <<eof;
<form method="POST" action="">
  <input type="hidden" name="n" value="$next_user">
  <input type="hidden" name="token" value="$token">
  <input type="submit" name="next" value="Next user" class="bitter_button">
</form>
eof
}

#obtains a user's information and profile image
sub user_details {
	my ($details_filename, $image_filename) = @_;
	open DETAILS, "$details_filename" or die "Cannot open $details_filename: $!";
	my $location = my $latitude = my $longitude = "Unkown";
	my $litens = "None";

	#extracts non-sensitive user information
	foreach $line (<DETAILS>) {
		if ($line =~ /^full_name: (.+)/) {
			$name = $1;
		} elsif ($line =~ /^username: (.+)/) {
			$user = $1;
		} elsif ($line =~ /^home_suburb: (.+)/) {
			$location = $1;
		} elsif ($line =~ /^home_latitude: (.+)/) {
			$latitude = $1;
		} elsif ($line =~ /^home_longitude: (.+)/) {
			$longitude = $1;
		} elsif ($line =~ /^listens: (.+)/) {
			$listens = $1;
		}
	}

	close DETAILS;
	return <<eof;
<div class="bitter_block">
<table cellpadding="10">
  <tr>
    <td><img src="$image_filename" alt="$user profile image"></td>
    <td>
      <b><font size="10">$name</font></b>

<b>Username:</b> $user
<b>Suburb:</b> $location
<b>Latitude:</b> $latitude
<b>Longitude:</b> $longitude
<b>Listens:</b> $listens
    <td>
  </tr>
</table>
</div>
<p>
eof
}

#obtains a user's bleats
sub user_bleats {
	my $bleats_filename = $_[0];

	#obtains list of user's bleats
	open BLEATS, "$bleats_filename" or die "Cannot open $bleats_filename: $!";
	my @user_bleats = <BLEATS>;
	close BLEATS;

	my @bleats = reverse(sort(glob("$bleats_dir/*")));
	my $bleats_to_display = "";

	#examines all available bleats
	foreach $bleat (@bleats) {
		$bleat =~ s/\D//g;

		#adds only user's bleats to string
		if (grep(/^$bleat$/, @user_bleats)) {
			open BLEAT, "$bleats_dir/$bleat" or die "Cannot open $bleats_dir/$bleat: $!";
			$bleats_to_display .= "<div class='bitter_block'>\n";
			my ($reply, $time, $latitude, $longitude) = "";

			#extracts information about the bleat
			foreach $line (<BLEAT>) {
				$bleater = $1 if $line =~ /^username: (.+)/;
				$bleat_to_display = $1 if $line =~ /^bleat: (.+)/;
				$time = $1 if $line =~ /^time: (.+)/;
				$reply = $1 if $line =~ /^in_reply_to: (.+)/;
				$latitude = $1 if $line =~ /^latitude: (.+)/;
				$longitude = $1 if $line =~ /^longitude: (.+)/;
			}

			close BLEAT;
			encode_output($bleat_to_display);
			$bleats_to_display .= "<b>$bleater</b> bleated <i>$bleat_to_display</i>";

			#provides info about original bleat if applicable
			if ($reply ne "") {
				open BLEAT, "$bleats_dir/$reply" or die "Cannot open $bleats_dir/$reply: $!";

				#extracts information about the original bleat
				foreach $line (<BLEAT>) {
					$bleater = $1 if $line =~ /^username: (.+)/;
					$bleated = $1 if $line =~ /^bleat: (.+)/;
				}

				encode_output($bleated);
				$bleats_to_display .= " in response to a bleat by <b>$bleater</b>: <i>$bleated</i>";
				close BLEAT;
			}

			#appends rest of info about bleat to string
			$bleats_to_display .= "<br>\n";
			$bleats_to_display .= "<b>Posted:</b> ".scalar localtime($time)."\n" if $time;
			$bleats_to_display .= "<b>Latitude:</b> $latitude\n" if $latitude;
			$bleats_to_display .= "<b>Longitude:</b> $longitude\n" if $longitude;
			$bleats_to_display .= "\n</div>\n<p>\n";
		}

	}

	return $bleats_to_display;
}

#placed at the top of every page
sub page_header {
	return <<eof
Content-type: text/html

<!DOCTYPE html>
<head>
<title>Bitter</title>
<link href="bitter.css" rel="stylesheet">
</head>
<body bgcolor="#FEDCBA">
<div class="bitter_heading">Bitter</div>
eof
}

#placed at the bottom of every page
#provides debugging information if global variable $debug is set
sub page_trailer {
	my $footer = "";
	$footer .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
	$footer .= "</body>\n</html>";
	return $footer;
}

#sanitises a given output string by escaping html metacharacters
sub encode_output(\$) {
	$input = $_[0];
	$input =~ s/\"/&quot/g;
	$input =~ s/\&/&amp/g;
	$input =~ s/\</&lt/g;
	$input =~ s/\>/&gt/g;
}
