#!/usr/bin/perl -w
#Written by Constantinos Paraskevopoulos in October 2015
#Provides a social media platform analogous to Twitter
#http://www.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);

$debug = 1;

#declares global variables relating to user data
$dataset_size = "medium";
$users_dir = "dataset-$dataset_size/users";
$bleats_dir = "dataset-$dataset_size/bleats";

#obtains session id token if it exists
if (defined $ENV{HTTP_COOKIE} && $ENV{HTTP_COOKIE} =~ /\btoken=([\w\-]{30,})/) {
	$token = $1;
	my $token_file = "tokens/$token";

	#securely logs user out if requested
	if (defined param('logout')) {

		#revokes token for previous session if user logged out
		if (-e $token_file) {
			unlink $token_file or die "Unable to remove $token_file: $!";
		}

		#displays landing page and exits
		print_page_header();
		display_login_page();
		print_page_trailer();
		exit 0;
	} else {

		#checks whether cookie is valid and has been issued recently
		if (length($token) > 30 && -e $token_file && -M $token_file < 1) {

			#only sets cookie if user is not attempting to login
			if (!defined param('login')) {
				print_page_header($token, $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/);
			} else {
				print_page_header();
				print <<eof;
<script type="text/javascript">
  window.onload = function() {
    alert("Please log in again.");
  }
</script>
eof
			}

		} else {
			print_page_header();
		}

	}

}

#main bitter hierarchy logic
if (defined $token) {
	$token =~ s/[^\w\-]//g; #removes unexpected chars from token
	$token_file = "tokens/$token";

	#checks that token is valid and has been issued within the last day
	if (length($token) > 30 && -e $token_file && -M $token_file < 1) {

		#navigates to appropriate page based on user's request
		if (defined param('home') && $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/) {
			my $user = $1;
			display_page_banner();
			display_user_profile("$users_dir/$user");
		} elsif (defined param('settings')) {
			print "<font color='red'>This page is a placeholder.</font>\n";
		} elsif (defined param('search')) {
			my $search_phrase = param('search_phrase');
			display_page_banner();
			display_search_results($search_phrase);
		} elsif (defined param('send_bleat')) {
			my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
			add_bleat($current_user[0], param('bleat_to_send'));
			display_page_banner();
			display_user_profile("$users_dir/".$current_user[0]);
		} elsif (defined param('profile_to_view')) {
			my $user_profile = param('profile_to_view');
			display_page_banner();
			display_user_profile($user_profile);
		} else {
			display_login_page();
		}

	} else {
		#requests re-authentication if invalid token or session expired
		print <<eof;
<div class="bitter_heading">Welcome to Bitter</div>
<center>
  <font color="red">Your session has expired.</font>
  <p>
</center>
eof
		display_login_page(-supress_heading => "true");
	}

} elsif (defined param('login')) {
		if (authenticate_user(param('username'), param('password'))) {
			#generates unique 64-bit uuid
			$token = `uuidgen`;
			chomp $token;

			#stores token in direcotry
			$token_file = "tokens/$token";
			mkdir "tokens" or die "Cannot create tokens: $!" if ! -e "tokens";
			open TOKEN, ">", "$token_file" or die "Unable to write $token_file: $!";
			close TOKEN;

			print_page_header($token, param('username'));
			display_page_banner();
			display_user_profile("$users_dir/".param('username'));
		} else {
			print_page_header();
			wrong_credentials_page();
		}
} elsif (defined param('reset')) {
	#allows user to reset password
	print_page_header();
	print "<font color='red'>This page is a placeholder.</font>\n";
} else {
	#authenticates user for first time
	print_page_header();
	display_login_page();
}

print_page_trailer();
exit 0;

#validates user login credentials
sub authenticate_user {
	my ($username, $password) = @_;
	$username =~ s/\W\D//g; #sanitises user login
	return 0 if length($username) eq 0 || length($password) eq 0;
	my $details_filename = "$users_dir/$username/details.txt";
	return 0 if ! -e $details_filename; #checks whether user exists

	#opens user details and extracts stored password
	open USER, "<", "$details_filename" or die "Cannot open $details_filename: $!";
	foreach (<USER>) {
		$expected_password = $1 if $_ =~ /^password: (.+)/;
	}

	close USER;
	return 1 if $password eq $expected_password; #checks validity of password
	return 0;
}

#produces a user login form
sub display_login_page {
	#omits heading if function is called with a parameter
	my %supress_heading = @_;
	if (!%supress_heading) {
		print '<div class="bitter_heading">Welcome to Bitter</div>';
	}

	print <<eof;
<center>
  <form method="POST" action="">
    <table cellpadding="2">
      <tr><td>Username</td></tr>
      <tr><td><input type="text" name="username" class="bitter_textfield"></td></tr>
      <tr><td>Password</td></tr>
      <tr><td><input type="password" name="password" class="bitter_textfield"></td></tr>
    </table>
    <p>
    <input type="submit" name="login" value="Login" class="bitter_button">
    <input type="submit" name="reset" value="Reset password" class="bitter_button">
  </form>
</center>
eof
}

#displays error message and prompts for re-authentication
sub wrong_credentials_page {
	print <<eof;
<div class="bitter_heading">Welcome to Bitter</div>
<center>
  <font color='red'>Incorrect username or password.</font>
</center>
<br>
eof
	display_login_page(-supress_heading => "true");
}

#prints html for the bitter navigation banner
sub display_page_banner {
	print <<eof;
<form method="GET" action="">
  <table>
    <tr>
      <td>
        <div class="bitter_subheading">Bitter |</div>
        <input type="submit" name="home" value="My Profile" class="bitter_button">
        <input type="submit" name="settings" value="Settings" class="bitter_button">
        <input type="text" name="search_phrase" onkeypress="perform_search(event)">
        <input type="submit" name="search" id="search" value="Search" class="bitter_button">
        <input type="submit" name="logout" value="Logout" class="bitter_button">
      </td>
    </tr>
  </table>
  <script type="text/javascript">
    function perform_search(e) {
        if (e.keyCode === 13) {
          document.getElementById("search").click();
        }
    }
  </script>
</form>
<p>
eof
}

#shows formatted details of a user's profile
sub display_user_profile {
	#displays user profile specified as argument
	my $user_to_show = $_[0];
	
	my $details_filename = "$user_to_show/details.txt";
	my $image_filename = "profile_default.jpg"; #default profile image
	my $bleats_filename = "$user_to_show/bleats.txt";

	#updates profile image from default if a profile image is available
	my @profile_image = glob("$user_to_show/profile.*");
	$image_filename = $_ foreach (@profile_image);

	#obtains and prints the user's profile
	print user_details($details_filename, $image_filename);
	my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
	$current_user[0] = param('username') if $current_user[0] eq "";
	$user_to_show =~ s/$users_dir\///;
	print bleat_block() if $user_to_show eq $current_user[0];
	print user_bleats($bleats_filename);
}

#obtains a user's information and profile image
sub user_details {
	my ($details_filename, $image_filename) = @_;
	open DETAILS, "<", "$details_filename" or die "Cannot open $details_filename: $!";
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
<b>Home Latitude:</b> $latitude
<b>Home Longitude:</b> $longitude
<b>Listens:</b> $listens
    <td>
  </tr>
</table>
</div>
<p>
eof
}

#provides interface for sending new bleats
sub bleat_block {
	return <<eof;
<div class="bitter_block">
<form method="GET" action="">
  <textarea style="width: 100% resize: vertical" rows="10" name="bleat_to_send">
  </textarea>
  <input type="submit" name="send_bleat" value="Send Bleat" class="bitter_button">
</form>
</div>
<p>
eof
}

#appends bleat to collection of bleats for current user
sub add_bleat {
	my ($current_user, $bleat_to_send) = @_;
	$bleat_to_send = substr($bleat_to_send, 0, 142);

	#finds greatest unique identifier and increments by 50
	my @bleats = reverse(sort(glob("$bleats_dir/*")));
	$bleats[0] =~ s/$bleats_dir\///;
	$bleats[0] += 50;

	#adds bleat identifier to user record
	my $user_bleats = "$users_dir/$current_user/bleats.txt";
	open USER, ">>", "$user_bleats" or die "Cannot write $user_bleats: $!";
	print USER "$bleats[0]\n";
	close USER;

	#adds bleat to bleats collection
	my $unix_time = time();
	my $bleat_file = "$bleats_dir/$bleats[0]";
	open BLEAT, ">", "$bleat_file" or die "Cannot write $bleat_file: $!";
	print BLEAT <<eof;
username: $current_user
bleat: $bleat_to_send
time: $unix_time
eof
	close BLEAT;
}

#obtains a user's bleats
sub user_bleats {
	my $bleats_filename = $_[0];

	#obtains list of user's bleats
	open BLEATS, "<", "$bleats_filename" or die "Cannot open $bleats_filename: $!";
	my @user_bleats = <BLEATS>;
	close BLEATS;

	my @bleats = reverse(sort(glob("$bleats_dir/*")));
	my $bleats_to_display = "";

	#examines all available bleats
	foreach $bleat (@bleats) {
		$bleat =~ s/\D//g;

		#adds only user's bleats to string
		if (grep(/^$bleat$/, @user_bleats)) {
			my $bleat_file = "$bleats_dir/$bleat";
			open BLEAT, "<", "$bleat_file" or die "Cannot open $bleat_file: $!";
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
			$bleat_to_display = encode_output($bleat_to_display);
			$bleats_to_display .= "<b>$bleater</b> bleated <i>$bleat_to_display</i>";

			#provides info about original bleat if applicable
			if ($reply ne "") {
				my $bleat_file = "$bleats_dir/$reply";
				open BLEAT, "<", "$bleat_file" or die "Cannot open $bleat_file: $!";

				#extracts information about the original bleat
				foreach $line (<BLEAT>) {
					$bleater = $1 if $line =~ /^username: (.+)/;
					$bleated = $1 if $line =~ /^bleat: (.+)/;
				}

				$bleated = encode_output($bleated);
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

#computes and displays search results
sub display_search_results {
	my $search_term = $_[0];

	#aborts if user did not enter a search phrase 
	if (length($search_term) == 0) {
		print "Please enter a search phrase first.\n";
		return;
	}

	my $search = $search_term;
	$search =~ s/\.\.//g; #sanitises search phrase
	$search =~ s/\ \ / /g; #condenses whitespace
	my @users = glob("$users_dir/*");
	my $i = 0;

	#checks whether requested user exists
	for $user (@users) {

		if ($user =~ /$search/i) {
			#matches user with given username
			my $user_info = "$user/details.txt";
			open USER, "<", $user_info or die "Cannot access $user_info: $!";

			#obtains full name of user
			foreach $line (<USER>) {
				$full_name = $1 if ($line =~ /^full_name: (.+)/i);
			}

			close USER;
			$matches{$user} = $full_name;
			$i++;
		} else {
			#matches user with given full name
			my $user_info = "$user/details.txt";
			open USER, "<", $user_info or die "Cannot access $user_info: $!";
			foreach $line (<USER>) {
				if ($line =~ /^full_name: (.*$search.*)/i) {
					$matches{$user} = $1;
					$i++;
				}
			}
			close USER;
		}

	}

	$search_term = encode_output($search_term);

	#dispays username and full name of matches or message that no results were found
	if ($i eq 0) {
		print "No search results found for \"$search_term\"\n";
	} else {
		print "<b>Found $i search results for \"$search_term\":</b>\n<p>\n";

		#prints a form for each match, displaying usernames and full names
		foreach $key (sort(keys %matches)) {
			print "<i>$matches{$key}</i>\n<br>\n";
			$key =~ s/$users_dir\///;
			print <<eof;
<form method="GET" action="">
  Username: <input type="submit" name="view_profile" value="$key" class="bitter_link">
  <input type="hidden" name="profile_to_view" value="$users_dir/$key">
</form>
<p>
<br>
eof
		}

	}

}

#placed at the top of every page
sub print_page_header {
	my $token = $_[0] || ''; #obtains session id from passing argument if it exists
	my $user = $_[1] || ''; #obtains username from passing argument if it exists
	print <<eof;
Content-type: text/html
Set-cookie: token=$token; HttpOnly
Set-cookie: user=$user; HttpOnly

<!DOCTYPE html>
<head>
  <title>Bitter</title>
  <link href="bitter.css" rel="stylesheet">
</head>
<body>
eof
	warningsToBrowser(1); #enables warnings as html comments
}

#placed at the bottom of every page
sub print_page_trailer {

	#provides debugging information if global variable $debug is set
	if ($debug) {
		print "<!-- ";

		#prints param='value' for each parameter
		foreach $param (param()) {
			my $value = param($param);
			$input = encode_output($input);
			print "$param='$value' ";
		}

		print "-->\n";
	}

	print <<eof;
</body>
</html>
eof
}

#sanitises a given output string by escaping html metacharacters
sub encode_output {
	$input = $_[0] || '';
	$input =~ s/\&/&amp/g;
	$input =~ s/\</&lt/g;
	$input =~ s/\>/&gt/g;
	return $input;
}
