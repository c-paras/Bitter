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
			unlink $token_file or die "Cannot remove $token_file: $!";
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
    alert("Authentication failed. Please log in to continue.");
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
		my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
		my $details_filename = "$users_dir/$current_user[0]/details.txt";

		#checks that valid user is logged in
		if (!open USER, "<", $details_filename) {
			display_login_page();
			print_page_trailer();
			exit 0;
		}

		close USER;

		#navigates to appropriate page based on user's request
		if (defined param('home')) {
			display_page_banner();
			display_user_profile("$users_dir/".$current_user[0]);
		} elsif (defined param('settings')) {
			print "<font color=\"red\">This page is a placeholder.</font>\n";
		} elsif (defined param('search')) {
			display_page_banner(param('search_phrase'), param('search_type'));
			display_search_results(param('search_phrase'), param('search_type'));
		} elsif (defined param('bleat_to_send')) {
			add_bleat($current_user[0], param('bleat_to_send'), param('in_reply_to'));
			display_page_banner();
			display_user_profile("$users_dir/".$current_user[0]);
		} elsif (defined param('profile_to_view')) {
			display_page_banner();
			display_user_profile(param('profile_to_view'));
		} elsif (defined param('listen')) {
			listen_to_user(param('listen'), $current_user[0], param('previous_page'));
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
			open TOKEN, ">", $token_file or die "Cannot write $token_file: $!";
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
	print "<font color=\"red\">This page is a placeholder.</font>\n";
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
	open USER, "<", $details_filename or die "Cannot open $details_filename: $!";
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
  <font color="red">Incorrect username or password.</font>
</center>
<br>
eof
	display_login_page(-supress_heading => "true");
}

#prints html for the bitter navigation banner
sub display_page_banner {
	my $search_phrase = $_[0] || '';
	$search_phrase = encode_output($search_phrase);
	my $type = $_[1] || '';
	print <<eof;
<form method="GET" action="">
  <table>
    <tr>
      <td>
        <div class="bitter_subheading">Bitter |</div>
        <input type="submit" name="home" value="Home" class="bitter_button">
        <input type="submit" name="settings" value="Settings" class="bitter_button">
        <input type="text" name="search_phrase" value="$search_phrase" onkeypress="perform_search(event);">
        <select name="search_type" class="bitter_button">
eof

	#prints search options with default value == that which was selected
	print "<option value=\"users\" selected>Users</option>\n" if $type eq "users";
	print "<option value=\"users\">Users</option>\n" if $type ne "users";
	print "<option value=\"bleats\" selected>Bleats</option>\n" if $type eq "bleats";
	print "<option value=\"bleats\">Bleats</option>\n" if $type ne "bleats";
	print "<option value=\"all\" selected>All</option>\n" if $type eq "all";
	print "<option value=\"all\">All</option>\n" if $type ne "all";

	print <<eof;
        </select>
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

	#finds currently logged-in user
	my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
	$current_user[0] = param('username') if !$current_user[0];
	$user_to_show =~ s/$users_dir\///;

	print '<table cellpadding="8" align="left"><tr><td>', "\n";

	if ($user_to_show eq $current_user[0]) {
		#prints additional bleats if user_to_show == current_user
		print user_details($details_filename, $image_filename);
		print bleat_block(); #option to send a bleat
		print "</td></tr></table>\n<br>\n";
		print user_bleats($bleats_filename, -display_relevant => "true");
	} else {
		#prints listen/unlisten option if user_to_show != current_user
		print user_details($details_filename, $image_filename, $current_user[0]);
		print "</td></tr></table>\n<br>\n";
		print user_bleats($bleats_filename);
	}

}

#obtains a user's information and profile image
sub user_details {
	my ($details_filename, $image_filename) = ($_[0], $_[1]);
	my $listen_option = $_[2] || '';
	open DETAILS, "<", $details_filename or die "Cannot open $details_filename: $!";
	my $location = my $latitude = my $longitude = "Unkown";
	$listens = "None";

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
			$listens =~ s/\s{2,}/ /g; #condenses whitespace
			$listens = "None" if $listens eq " ";
		}
	}

	close DETAILS;
	my $details = <<eof;
<div class="bitter_block">
  <b><font size="10">$name</font></b>

<img src="$image_filename" alt="$user profile image" style="center: parent;">

<b>Username:</b> $user
<b>Suburb:</b> $location
<b>Home Latitude:</b> $latitude
<b>Home Longitude:</b> $longitude
<b>Listens:</b> $listens
eof

	$details .= listen_option($user, $listen_option, "profile")."</form>\n" if $listen_option ne "";

	$details .= "\n</div>\n";
	return $details;
}

#provides interface for sending new bleats
sub bleat_block {
	return <<eof;
</td><tr><td>
<div class="bleat_block">
<b>Send a new bleat:</b>
<form id="bleat_form" method="POST" action="">
  <textarea name="bleat_to_send" id="bleat_to_send" style="width: 100%; resize: none; height: 200px;">
</textarea>
  <input type="button" name="send_bleat" id="send_bleat" value="Send Bleat" onclick="create_bleat();" class="bitter_button">
  <input type="hidden" name="in_reply_to" id="in_reply_to">
</form>
</div>
<script type="text/javascript">
  function create_bleat() {
    var user_text = document.getElementById("bleat_to_send").value;
    if (user_text.match(/^\\s*\$/) === null) {
      document.getElementById("bleat_form").submit();
    }
  }
</script>
eof
}

#provides option for listening/unlistening user
sub listen_option {
	my ($user, $current_user, $current_page) = @_;
	my $user_profile = "$users_dir/$current_user/details.txt";
	my $listens = "";
	open USER, "<", "$user_profile" or die "Cannot open $user_profile: $!";

	#finds listens of current user
	while (<USER>) {
		if ($_ =~ /^listens: (.+)/) {
			$listens = $1;
			last;
		}
	}

	close USER;

	$type = "Unlisten" if grep(/$user/, $listens);
	$type = "Listen to" if !grep(/$user/, $listens);

	return <<eof;
<form method="POST" action="" style="margin-bottom: 0px;">
  <input type="submit" name="listen" value="$type $user" class="bitter_button">
  <input type="hidden" name="previous_page" value="$current_page">
eof
}

#appends bleat to collection of bleats for current user
sub add_bleat {
	my ($current_user, $bleat_to_send, $in_reply_to) = @_;
	$bleat_to_send = substr($bleat_to_send, 0, 142); #limits length of bleat
	$bleat_to_send =~ s/\n/ /g; #converts all newlines to spaces

	#finds greatest unique identifier and increments by 50
	my @bleats = reverse(sort(glob("$bleats_dir/*")));
	$bleats[0] =~ s/$bleats_dir\///;
	$bleats[0] += 50;

	#adds bleat identifier to user record
	my $user_bleats = "$users_dir/$current_user/bleats.txt";
	open USER, ">>", $user_bleats or die "Cannot write $user_bleats: $!";
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
	print BLEAT "in_reply_to: $in_reply_to\n" if $in_reply_to =~ /^\d{10,}$/;
	close BLEAT;
}

#obtains a user's bleats
sub user_bleats {
	my $bleats_filename = $_[0];
	my $show_relevant = $_[1] || '';

	#obtains list of user's bleats
	return if $bleats_filename =~ /None\/bleats.txt$/;
	open BLEATS, "<", $bleats_filename or die "Cannot open $bleats_filename: $!";
	push @user_bleats, <BLEATS>;
	close BLEATS;

	my @bleats = reverse(sort(glob("$bleats_dir/*")));

	#returns bleats of user listened to by logged in user
	if ($show_relevant eq "-supress_recursion") {
		foreach $bleat (@bleats) {
				push @bleats_of_listner, $bleat if grep(/^$bleat$/, @user_bleats);
		}
		return @bleats_of_listner;
	}

	$bleats_filename =~ s/$users_dir\/(.+)\/bleats.txt/$1/; #extracts user
	my $user = $bleats_filename;
	add_relevant_bleats($user, @bleats) if $show_relevant ne '';
	my $bleats_to_display = "";

	#examines all available bleats
	foreach $bleat (@bleats) {
		$bleat =~ s/\D//g;

		#adds only user's relevant bleats to string
		if (grep(/^$bleat$/, @user_bleats)) {
			my $bleat_file = "$bleats_dir/$bleat";
			open BLEAT, "<", $bleat_file or die "Cannot open $bleat_file: $!";
			$bleats_to_display .= "<div class=\"bleat_block\">\n";
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
				open BLEAT, "<", $bleat_file or die "Cannot open $bleat_file: $!";
				my $bleater = "";

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
			my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
			$current_user[0] = param('username') if !$current_user[0];
			if ($user eq $current_user[0] && $bleater ne $current_user[0]) {
				$bleats_to_display .= listen_option($bleater, $current_user[0], "home");
			}
			if ($bleater ne $current_user[0]) {
				$bleats_to_display .= '<form method="POST" action="">'."\n" if $user ne $current_user[0];
				$bleats_to_display .= reply_to_bleat($bleater, $bleat);
			}
			$bleats_to_display .= "\n</div>\n<p>\n";
		}

	}

	#appends javascript to allow the user to type a reply to a bleat using a prompt
	$bleats_to_display .= <<eof;
<script type="text/javascript">
  function reply_field(bleat_id) {
    var msg = prompt("Enter reply:");
    if (msg.match(/^\\s*\$/) === null) {
      document.getElementById("bleat_to_send").value = msg;
      document.getElementById("in_reply_to").value = bleat_id;
      document.getElementById("send_bleat").click();
    }
  }
</script>
eof

	return $bleats_to_display;
}

#appends and sorts bleats that mention user and bleats of users they listen to
sub add_relevant_bleats {
	my ($username, @bleats) = ($_[0], @_);

	#adds bleats which mention the user
	my @all_bleats = glob("$bleats_dir/*");
	foreach $bleat (@all_bleats) {
		$bleat =~ s/\D//g;
		my $bleat_to_check = "$bleats_dir/$bleat";
		open BLEAT, "<", $bleat_to_check or die "Cannot open $bleat_to_check: $!";

		#checks whether bleat mentions user
		my $mentioned = 0;
		while (<BLEAT>) {
			$mentioned = 1 if $_ =~ /^bleat:.*$username.*/;
		}

		push @user_bleats, $bleat if $mentioned;
		close BLEAT;
	}

	my @listens = split / /, $listens;

	#cycles through all listens and appends bleats by those users
	foreach $user (@listens) {
		next if $user eq "";
		my $listen = "$users_dir/$user/bleats.txt";
		push @bleats, user_bleats($listen, -supress_recursion => "true");
	}

}

#prints user form for replying to a bleat
sub reply_to_bleat {
	my ($bleater, $bleat_id) = ($_[0], $_[1]);
	return <<eof;
  <input type="button" name="reply" value="Reply to $bleater" onclick="reply_field($bleat_id);" class="bitter_button">
</form>
eof
}

#computes and displays search results
sub display_search_results {
	my ($search_term, $search_type) = ($_[0], $_[1]);
	$search_term =~ s/\s{2,}/ /g; #condenses whitespace
	$search_term =~ s/(\||\\|\.|\/)//g; #sanitises search phrase
	my $search = $search_term;
	$search_term = encode_output($search_term);

	#aborts if user did not enter a valid search phrase 
	if (length($search) == 0 || $search eq " ") {
		print "Please enter a valid search phrase.\n";
		return;
	}

	my @users = my @bleats = ();
	@users = glob("$users_dir/*") if $search_type ne "bleats";
	@bleats = glob("$bleats_dir/*") if $search_type ne "users";
	my $i = 0;

	#finds all users matching $search
	for $user (@users) {

		if (index(lc $user, lc $search) != -1) {
			#matches user with given username
			my $user_info = "$user/details.txt";
			open USER, "<", $user_info or die "Cannot open $user_info: $!";

			#obtains full name of user
			foreach $line (<USER>) {
				$full_name = $1 if ($line =~ /^full_name: (.+)/i);
			}

			close USER;
			$users{$user} = $full_name;
			$i++;
		} else {
			#matches user with given full name
			my $user_info = "$user/details.txt";
			open USER, "<", $user_info or die "Cannot open $user_info: $!";
			foreach $line (<USER>) {
				$users{$user} = $1 and $i++ if $line =~ /^full_name: (.*$search.*)/i;
			}
			close USER;
		}

	}

	#finds all bleats matching $search
	for $bleat (@bleats) {
		open BLEAT, $bleat or die "Cannot open $bleat: $!";

		#extracts username of bleater and bleat message
		while (<BLEAT>) {
			$username = $1 if $_ =~ /^username: (.+)/;
			$bleat_msg = $1 if $_ =~ /^bleat: (.+)/;
		}

		close BLEAT;
		$bleats{$username} .= "$bleat_msg<br>\n" and $i++ if index(lc $bleat_msg, lc $search) != -1;
	}

	#dispays results which matched $search or a message that no results were found
	if ($i eq 0) {
		print "No search results found for \"$search_term\"\n";
	} else {
		print "<b>Found $i search result for \"$search_term\":</b>\n" if $i == 1;
		print "<b>Found $i search results for \"$search_term\":</b>\n" if $i > 1;
		generate_search_results("Username", %users) if $search_type ne "bleats";
		generate_search_results("Bleated by", %bleats) if $search_type ne "users";
	}

}

#formats search results in human-readable form with links to relevant user page
sub generate_search_results {
	my ($type_of_match, %matches) = @_;
	print "<table>";

	#prints a form for each match, displaying match and link to profile
	foreach $key (sort(keys %matches)) {
		print <<eof;
<tr><td>
<i>$matches{$key}</i>
eof

		$key =~ s/$users_dir\///;
		print <<eof;
<form method="GET" action="">
  $type_of_match: <input type="submit" name="view_profile" value="$key" class="bitter_link">
  <input type="hidden" name="profile_to_view" value="$users_dir/$key">
</form>
<br>
</td></tr>
eof
	}

	print "</table>\n";
}

#toggles listening/unlistening to specified user
sub listen_to_user {
	my ($user, $current_user, $previous_page) = @_;
	my $user_profile = "$users_dir/$current_user/details.txt";
	display_page_banner();

	if ($user =~ /^Unlisten (.+)/) {
		my $unlisten_to = $1;
		open USER, "<", $user_profile or die "Cannot open $user_profile: $!";
		my $i = 0;

		#removes $unlisten_to user from the listen data
		while (<USER>) {
			$_ =~ s/$unlisten_to//;
			$_ =~ s/ $//;
			$lines[$i++] = $_;
		}

		close USER;

		#updates user detail file
		open USER, ">", $user_profile or die "Cannot write $user_profile: $!";
		print USER @lines;
		close USER;

		display_user_profile("$users_dir/$unlisten_to") if $previous_page eq "profile";
	} elsif ($user =~ /^Listen to (.+)/) {
		my $listen_to = $1;
		open USER, "<", $user_profile or die "Cannot open $user_profile: $!";
		my $i = 0;

		#appends $listen_to user to the listen data
		while (<USER>) {
			if ($_ =~ /^(listens: .+)/) {
				my $current_listens = $1;
				$current_listens .= " $listen_to\n";
				$lines[$i++] = $current_listens;
			} else {
				$lines[$i++] = $_;
			}
		}

		close USER;

		#updates user detail file
		open USER, ">", $user_profile or die "Cannot write $user_profile: $!";
		print USER @lines;
		close USER;
		display_user_profile("$users_dir/$listen_to") if $previous_page eq "profile";	
	}

	display_user_profile("$users_dir/$current_user") if $previous_page eq "home";
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
	warningsToBrowser(1) if $debug; #enables warnings as html comments
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
	$input =~ s/\&/&amp;/g;
	$input =~ s/\'/&apos;/g;
	$input =~ s/\"/&quot;/g;
	$input =~ s/\</&lt;/g;
	$input =~ s/\>/&gt;/g;
	return $input;
}
