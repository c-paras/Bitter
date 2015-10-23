#!/usr/bin/perl -w
#Written by Constantinos Paraskevopoulos in October 2015
#Provides a social media platform analogous to Twitter
#http://www.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw(:all);
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Digest::MD5 qw(md5_hex);

$debug = 1;

#declares global variables relating to user data
$dataset_size = "medium";
$users_dir = "dataset-$dataset_size/users";
$bleats_dir = "dataset-$dataset_size/bleats";

#obtains session id token if it exists
if (defined $ENV{HTTP_COOKIE} && $ENV{HTTP_COOKIE} =~ /\btoken=([\w]{30,})/) {
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
	$token =~ s/[^\w]//g; #removes unexpected chars from token
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
		} elsif (defined param('search') || defined param('more')) {
			display_page_banner(param('search_phrase'), param('search_type'));
			display_search_results(param('search_phrase'), param('search_type'));
		} elsif (defined param('bleat_to_send')) {
			add_bleat($current_user[0], param('bleat_to_send'));
			display_page_banner();
			display_user_profile("$users_dir/".$current_user[0]);
		} elsif (defined param('reply_bleat') || defined param('bleat_to_delete')) {

			#replies to or deletes specified bleat
			if (defined param('bleat_to_delete')) {
				delete_bleat(param('bleat_to_delete'), $current_user[0]);
			} else {
				add_bleat($current_user[0], param('reply_bleat'), param('in_reply_to'));
			}

			#navigates to relevant profile page or to search results page
			if (defined param('profile_in_view')) {
				display_page_banner();
				display_user_profile(param('profile_in_view'));
			} else {
				display_page_banner(param('search_phrase'), param('search_type'));
				display_search_results(param('search_phrase'), param('search_type'));
			}

		} elsif (defined param('profile_to_view')) {
			display_page_banner();
			display_user_profile(param('profile_to_view'));
		} elsif (defined param('listen')) {
			listen_to_user(param('listen'), $current_user[0], param('previous_page'));
		} elsif (defined param('next')) {
			display_page_banner();
			display_user_profile(param('profile_in_view'));
		} elsif (defined param('update')) {
			display_page_banner();
			update_details($current_user[0]);
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
			#generates unique session id
			$token = md5_hex(time() + $$);
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
} elsif (defined param('email')) {
	#allows user to reset password
	print_page_header();
	reset_password(param('email'));
} elsif (defined param('reset_password')) {
	print_page_header();
	reset_password_form(param('reset_password'), param('username'));
} elsif (defined param('change_password')) {
	#changes user's password
	print_page_header();
	change_password(param('new_password'), param('confirm_password'), param('username'), param('password_rnd'));
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
		print '<div class="bitter_heading">Welcome to Bitter</div>', "\n";
	}

	#andrewt's valid email regex with double escaping
	my $valid_email_chars = "\\w\\.\\@\\-\\!\\#\\\$\\%\\&\\'\\*\\+\\-\\/\\=\\?\\^_\\`\\{\\|\\}\\~";

	print <<eof;
<center>
  <form id="login_form" method="POST" action="">
    <table cellpadding="2">
      <tr><td>Username:</td></tr>
      <tr><td><input type="text" name="username" class="bitter_textfield"></td></tr>
      <tr><td></td></tr>
      <tr><td></td></tr>
      <tr><td>Password:</td></tr>
      <tr><td><input type="password" name="password" class="bitter_textfield"></td></tr>
    </table>
    <p>
    <input type="submit" name="login" value="Login" class="bitter_button">
    <input type="button" name="reset" value="Reset password" onclick="reset_password();" class="bitter_button">
    <input type="hidden" name="email" id="email">
  </form>
</center>

<script type="text/javascript">
  function reset_password() {
    var result = prompt("Enter your email:");
    if (result.match(/^\\s*\$/) === null && result.match(/@/)) {
      result = result.replace(/[^$valid_email_chars]/g, '');
      document.getElementById("email").value = result;
      alert("If the email you provided is linked to an account, you will recieve an email with instructions shortly.");
      document.getElementById("login_form").submit();
    } else {
      alert("Please enter a valid email.");
    }
  }
</script>

eof
}

#allows a user to reset a forgotten or compromised password
sub reset_password {
	my $email = $_[0];
	chomp $email;
	$email = substr($email, 0, 256);

	my @users = glob("$users_dir/*/details.txt");
	my $user_exists = 0;

	foreach $user (@users) {
		open USER, "<", $user or die "Cannot open $user: $!";
		while (<USER>) {
			$user_exists = 1 if $_ =~ /^email: \Q$email\E/;
			$username = $1 if $_ =~ /^username: (.+)/;
		}
		close USER;
		if ($user_exists) {
			my $unique_rnd = md5_hex(time() + $$);
			chomp $unique_rnd;

			#stores token in direcotry
			$token_file = "tokens/$unique_rnd-$username";
			mkdir "tokens" or die "Cannot create tokens: $!" if ! -e "tokens";
			open TOKEN, ">", $token_file or die "Cannot write $token_file: $!";
			close TOKEN;

			open MAIL, "|-", "mail -s 'Reset Bitter Password' \Q$email\E" or die "Cannot run mail: $!";
			print MAIL "Copy and paste this link into your browser to reset your password: $ENV{SCRIPT_URI}?reset_password=$unique_rnd&username=$username";
			close MAIL;
			last;
		}

	}

	display_login_page();
}

#provides form for resetting a password
sub reset_password_form {
	my ($token, $user) = @_;

	#ensures that only a valid user with access to provided email can reset password
	if (! -e "tokens/$token-$user" || ! -e "$users_dir/$user") {
		display_login_page();
	} elsif (length($token) < 30 || length($user) < 5 || -M "tokens/$token-$user" > 1) {
		display_login_page();
	} else {
		print <<eof;
<div class="bitter_heading">Welcome to Bitter</div>
<center>
  <div class="bitter_subheading">Reset Bitter Password</div>
  <p>
  <form method="POST" action="">
    <table cellpadding="2">
      <tr><td>New password:</td><tr>
      <tr><td><input type="text" name="new_password" class="bitter_textfield"></td></tr>
      <tr><td></td><tr>
      <tr><td></td><tr>
      <tr><td>Confirm password:</td><tr>
      <tr><td><input type="text" name="confirm_password" class="bitter_textfield"></td></tr>
    </table>
    <p>
    <input type="submit" name="change_password" value="Reset password" class="bitter_button">
    <input type="hidden" name="username" value="$user">
    <inpit type="hidden" name="password_rnd" value="$token">
  </form>
</center>
eof
	}
}

#changes a user's password
sub change_password {
	my ($new_password, $confirm_password, $username, $unique_id) = @_;

	if ($new_password ne $confirm_password) {
		print "Passwords do not match.\n"; #red wrting....
		reset_password_form($unique_id, $username);
	} elsif (length($new_password) < 8) { #more conditions and secutiry percautins...
		print "New password must contain at least 8 characters.\n";
		reset_password_form($unique_id, $username);
	} else {
		my $user_file = "$users_dir/$username/details.txt";
		open USER, "<", $user_file or die "Cannot open $user_file: $!";
		while (<USER>) {
			push @user_data, $_ if $_ !~ /^password:/;
		}
		close USER;
		push @user_data, "password: $new_password";
		unlink "tokens/$token" or die "Cannot remove tokens/$token: $!";
	}

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
	encode_output($search_phrase);
	my $type = $_[1] || '';
	print <<eof;
<form method="POST" action="">
  <table>
    <tr>
      <td>
        <div class="bitter_subheading">Bitter |</div>
        <input type="submit" name="home" value="Home" class="bitter_button">
        <input type="submit" name="settings" value="Settings" class="bitter_button">
        <input type="text" name="search_phrase" value="$search_phrase" onkeypress="perform_search(event);">
        <select name="search_type" class="bitter_button">
eof

	#prints search options with default value == that which was last selected
	print "<option value=\"users\" selected>Users</option>\n" if $type eq "users";
	print "<option value=\"users\">Users</option>\n" if $type ne "users";
	print "<option value=\"bleats\" selected>Bleats</option>\n" if $type eq "bleats";
	print "<option value=\"bleats\">Bleats</option>\n" if $type ne "bleats";

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
	my $location = my $latitude = my $longitude = my $about = "Unknown";

	#extracts non-sensitive user information
	foreach $line (<DETAILS>) {
		$name = $1 if $line =~ /^full_name: (.+)/;
		$user = $1 if $line =~ /^username: (.+)/;
		$location = $1 if $line =~ /^home_suburb: (.+)/;	
		$latitude = $1 if $line =~ /^home_latitude: (.+)/;
		$longitude = $1 if $line =~ /^home_longitude: (.+)/;

		#captures listens of user if they exist
		if ($line =~ /^listens:/) {
			$listens = "";
			$listens = $1 if $line =~ /^listens: (.+)/;
			$listens =~ s/\s{2,}/ /g; #condenses whitespace
			$listens = "None" if $listens =~ /^\s*$/;
			$listens_to_display = $listens;
			$listens_to_display =~ s/ /\n/g; #displays listens as vertical list
		}

		$about = $1 if $line =~ /^about_me: (.+)/;
	}

	close DETAILS;
	encode_profile_text($about) if $about ne "Unknown";

	#appends user details to profile box
	my $details = <<eof;
<div class="bitter_block">
  <b><font size="10">$name</font></b>

<img src="$image_filename" alt="$user profile image" style="center: parent;">

<b>Username:</b> $user
<b>Suburb:</b> $location
<b>Home Latitude:</b> $latitude
<b>Home Longitude:</b> $longitude
<b>Listens:</b> $listens_to_display
<b>About Me:</b> $about
eof

	#gets currently logged in user
	my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
	$current_user[0] = param('username') if !$current_user[0];

	#appends option to update account details if profile is that of current user
	if ($user eq $current_user[0]) {
		$details .= <<eof;
<form method="POST" action="">
  <input type="submit" name="update" value="Update Details" class="bitter_button">
</form>
</div>
eof
	} else {
		$details .= "\n</div>\n";
	}

	return $details;
}

#provides interface for sending new bleats
sub bleat_block {
	#ensures same page is reloaded when bleat is sent
	my $display_offset = param('num_displayed') || 0;
	$display_offset += 1 if $display_offset != 0;

	return <<eof;
</td><tr><td>
<div class="bleat_block">
<b>Send a new bleat:</b><form id="bleat_form" method="POST" action="">
<textarea name="bleat_to_send" id="bleat_to_send" onkeydown="auto_submit(event);" style="width: 100%; height: 200px; resize: none;"></textarea>
<input type="button" name="send_bleat" id="send_bleat" value="Send Bleat" onclick="create_bleat();" class="bitter_button">
<input type="hidden" name="num_displayed" value="$display_offset"></form>
</div>

<script type="text/javascript">
  function create_bleat() {
    var user_text = document.getElementById("bleat_to_send").value;
    if (user_text.match(/^\\s*\$/) === null) {
      document.getElementById("bleat_form").submit();
    }
  }

  function auto_submit(e) {
    var user_text = document.getElementById("bleat_to_send").value;
    if (e.keyCode === 13 && user_text.match(/^\\s*\$/) === null) {
      document.getElementById("bleat_form").submit();
    }
  }
</script>

eof
}

#provides option buttons for replying to a bleat and listening/unlistening user
sub append_options {
	my ($bleater, $bleat_id, $current_user, $user_being_viewed) = @_;
	my $user_profile = "$users_dir/$current_user/details.txt";
	my $listens = "";
	open USER, "<", $user_profile or die "Cannot open $user_profile: $!";

	#finds listens of current user
	while (<USER>) {
		$listens = $1 if $_ =~ /^listens: (.+)/;
	}

	close USER;

	$type = "Unlisten" if grep(/$bleater/, $listens);
	$type = "Listen to" if !grep(/$bleater/, $listens);

	#approximates current page for next viewing
	my $display_offset = param('num_displayed') || 0;

	#determines whether current user's profile is being viewed
	$current_page = "home" if $current_user eq $user_being_viewed;
	$current_page = "profile" if $current_user ne $user_being_viewed;

	#constructs form with reply button, listen button and relevant hidden fields
	my $form_to_return = <<eof;

<input type="button" name="reply" value="Reply to $bleater" onclick="reply_field($bleat_id);" class="bitter_button"> <input type="submit" name="listen" value="$type $bleater" class="bitter_button"><input type="hidden" name="previous_page" value="$current_page"><input type="hidden" name="num_displayed" value="$display_offset">
eof

	#appends search info to form if available
	if (defined $search_term) {
		$form_to_return .= <<eof;
<input type="hidden" name="search_phrase" value="$search_term"><input type="hidden" name="search_type" value="$search_type">
eof
	}

	return $form_to_return;
}

#appends bleat to collection of bleats for current user
sub add_bleat {
	my ($current_user, $bleat_to_send) = ($_[0], $_[1]);
	$in_reply_to = $_[2] || '';
	$bleat_to_send = substr($bleat_to_send, 0, 142); #limits length of bleat
	$bleat_to_send =~ s/\s{2,}/ /g; #condenses whitespace

	#finds greatest unique identifier and increments by random number to avoid clashes
	my @bleats = reverse(sort(glob("$bleats_dir/*")));
	$bleats[0] =~ s/$bleats_dir\///;
	$bleats[0] += int(rand(200) + 1);

	#adds bleat identifier to user record
	my $user_bleats = "$users_dir/$current_user/bleats.txt";
	open USER, ">>", $user_bleats or die "Cannot write $user_bleats: $!";
	print USER "$bleats[0]\n";
	close USER;

	#adds bleat to bleats collection
	my $unix_time = time();
	my $bleat_file = "$bleats_dir/$bleats[0]";
	open BLEAT, ">", $bleat_file or die "Cannot write $bleat_file: $!";
	print BLEAT <<eof;
username: $current_user
bleat: $bleat_to_send
time: $unix_time
eof
	print BLEAT "in_reply_to: $in_reply_to\n" if $in_reply_to =~ /^\d{10,}$/;
	close BLEAT;

	#prints javascript to invoke an alert, indicating that bleating was successful
	print <<eof;
<script type="text/javascript">
  window.onload = function() {
    alert("Your bleat has been sent.");
  }
</script>

eof
}

#obtains a user's bleats
sub user_bleats {
	my $bleats_filename = $_[0];
	my $show_relevant = $_[1] || '';
	$displayed_up_to = param('num_displayed') || 0;
	$display_up_to = $displayed_up_to + 16; #displays next 16 results

	#obtains list of user's bleats
	return if $bleats_filename =~ /None\/bleats.txt$/;
	open BLEATS, "<", $bleats_filename or die "Cannot open $bleats_filename: $!";
	push @user_bleats, <BLEATS>;
	close BLEATS;

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
	my $bleats_to_display = format_bleats($user, @user_bleats);

	#ensures same page is viewed if reply is made
	my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
	$current_user[0] = param('username') if !$current_user[0];
	$display_offset = $display_up_to - 15 if $user eq $current_user[0];
	$display_offset = 0 if $user eq $current_user[0] && $display_up_to == 16;
	$display_offset = $display_up_to - 16 if $user ne $current_user[0];
	$display_offset = 0 if $display_offset < 0;

	#appends form to allow the user to type a reply to a bleat using a prompt
	$bleats_to_display .= <<eof;

<form id="reply_to_a_bleat" method="POST" action="">
  <input type="hidden" name="reply_bleat" id="reply_bleat">
  <input type="hidden" name="in_reply_to" id="in_reply_to">
  <input type="hidden" name="num_displayed" value="$display_offset">
  <input type="hidden" name="profile_in_view" value="$users_dir/$user">
</form>
eof

	#appends form for deleting a bleat
	$bleats_to_display .= <<eof;

<form id="delete_a_bleat" method="POST" action="">
  <input type="hidden" name="bleat_to_delete" id="bleat_to_delete">
  <input type="hidden" name="num_displayed" value="$display_offset">
  <input type="hidden" name="profile_in_view" value="$users_dir/$user">
</form>
eof

	#appends form for viewing the next 16 bleats
	$bleats_to_display .= <<eof;

<div align="right">
  <form method="POST" action="">
    <input type="submit" name="next" value="Show more bleats" class="bitter_button">
    <input type="hidden" name="num_displayed" value="$display_up_to">
    <input type="hidden" name="profile_in_view" value="$users_dir/$user">
  </form>
</div>
eof

	return $bleats_to_display;
}

#formats bleats to be displayed in a stylish way
sub format_bleats {
	my ($user, @user_bleats) = @_;
	my $bleats_to_display = "";
	@user_bleats = reverse(sort(@user_bleats)); #reverse chronologically sorts bleats
	$display_up_to = $#user_bleats + 1 if $#user_bleats < 16;

	#appends user's bleats to a string in formatted way
	for $i ($displayed_up_to..$display_up_to - 1) {

		#obtains and reads relevant bleat
		my $bleat = $user_bleats[$i % $#user_bleats]; #wraps to start of bleats
		$bleat =~ s/\D//g;
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
		encode_output($bleat_to_display);
		$bleat_to_display =~ s/\s{2,}/ /g; #condenses whitespace
		$bleat_to_display =~ s/\s*(.+)\s*/$1/; #removes leading and trailing whitespace
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

			encode_output($bleated);
			$bleated =~ s/\s{2,}/ /g; #condenses whitespace
			$bleated =~ s/\s*(.+)\s*/$1/; #removes leading and trailing whitespace
			$bleats_to_display .= " in response to a bleat by <b>$bleater</b>: <i>$bleated</i>";
			close BLEAT;
		}

		#appends rest of info about bleat to string
		$bleats_to_display .= "<br>\n";
		$bleats_to_display .= "<b>Posted:</b> ".scalar localtime($time) if $time;
		$bleats_to_display .= "\n<b>Latitude:</b> $latitude\n" if $latitude;
		$bleats_to_display .= "<b>Longitude:</b> $longitude" if $longitude;
		my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
		$current_user[0] = param('username') if !$current_user[0];

		#appends options to reply, listen/unlisten and delete bleat where appropriate
		$bleats_to_display .= '<form method="POST" action="">';
		if ($bleater ne $current_user[0]) {
			$bleats_to_display .= append_options($bleater, $bleat, $current_user[0], $user);
		} else {
			$bleats_to_display .= delete_bleat_option($bleat, $current_user[0], $user);
		}

		$bleats_to_display .= "</form>\n</div>\n<p>\n";
	}

	#appends javascript to allow the user to type a reply to a bleat using a prompt
	$bleats_to_display .= <<eof;

<script type="text/javascript">
  function reply_field(bleat_id) {
    var msg = prompt("Enter reply:");
    if (msg.match(/^\\s*\$/) === null) {
      document.getElementById("reply_bleat").value = msg;
      document.getElementById("in_reply_to").value = bleat_id;
      document.getElementById("reply_to_a_bleat").submit();
    }
  }
</script>
eof

	#appends javascript to allow confirmation of deletion
	$bleats_to_display .= <<eof;

<script type="text/javascript">
  function confirm_deletion(bleat_id) {
    var response = confirm("Are you sure you want to delete this bleat?");
    if (response === true) {
      document.getElementById("bleat_to_delete").value = bleat_id;
      document.getElementById("delete_a_bleat").submit();
    }
  }
</script>
eof

	return $bleats_to_display;
}

#returns html for a form to delete a bleat posted by user
sub delete_bleat_option {
	my ($bleat_id, $current_user, $user_being_viewed) = @_;

	#approximates current page for next viewing
	my $display_offset = param('num_displayed') || 0;

	#determines whether current user's profile is being viewed
	$current_page = "home" if $current_user eq $user_being_viewed;
	$current_page = "profile" if $current_user ne $user_being_viewed;

	#sets up delete button and javascript to confirm deletion
	my $form_to_return = <<eof;

<input type="button" name="delete_bleat" value="Delete bleat" onclick="confirm_deletion($bleat_id);" class="bitter_button">
eof

	return $form_to_return;
}

#deletes specified bleat from collection and any record of bleat
sub delete_bleat {
	my ($bleat_id, $current_user) = @_;

	#deletes the bleat from the bleat collection
	my $bleat_to_delete = "$bleats_dir/$bleat_id";
	unlink $bleat_to_delete or die "Cannot remove $bleat_to_delete: $!";

	#sets an array contaning all but deleted bleat
	my $user_bleats = "$users_dir/$current_user/bleats.txt";
	open USER, "<", $user_bleats or die "Cannot open $user_bleats: $!";
	while (<USER>) {
		push @new_bleats, $_ if $_ !~ /$bleat_id/;
	}
	close USER;

	#writes out new set of sent bleats
	open BLEATS, ">", $user_bleats or die "Cannot write $user_bleats: $!";
	print BLEATS @new_bleats;
	close BLEATS;

	#deletes the in_reply_to field of all bleats which refer to deleted bleat
	my @all_bleats = glob("$bleats_dir/*");
	foreach $bleat (@all_bleats) {
		open BLEAT, "<", $bleat or die "Cannot open $bleat: $!";
		my @lines = <BLEAT>;
		close BLEAT;

		#modifies bleat file if it is a reply to deleted bleat
		if (grep(/^in_reply_to: $bleat_id/, @lines)) {
			open BLEAT, ">", $bleat or die "Cannot open $bleat: $!";
			foreach (@lines) {
				print BLEAT $_ if $_ !~ /^in_reply_to: $bleat_id/; #skips reply line
			}
			close BLEAT;
		}

	}

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
			$mentioned = 1 if $_ =~ /^bleat:.*$username.*/i;
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

#computes and displays search results
sub display_search_results {
	($search_term, $search_type) = ($_[0], $_[1]);
	$search_term =~ s/\s{2,}/ /g; #condenses whitespace
	$search_term =~ s/(\||\\|\.\.|\/)//g; #sanitises search phrase
	my $search = $search_term;
	encode_output($search_term);
	$displayed_up_to = param('num_displayed') || 0;
	$display_up_to = $displayed_up_to + 16; #displays next 16 results

	#aborts if user did not enter a valid search phrase 
	if (length($search) == 0 || $search eq " ") {
		print "Please enter a valid search phrase.\n";
		return;
	}

	my $i = 0;
	$i = find_user_results($search) if $search_type eq "users";
	$i = find_bleat_results($search) if $search_type eq "bleats";

	#dispays results which matched $search or a message that no results were found
	if (@bleat_matches) {
		my @current_user = $ENV{HTTP_COOKIE} =~ /\buser=([\w]+)/;
		$current_user[0] = param('username') if !$current_user[0];
		print "<b>Found $i bleat matching \"$search_term\":</b>\n" if $i == 1;
		print "<b>Found $i bleats matching \"$search_term\":</b>\n" if $i > 1;
		print format_bleats($current_user[0], @bleat_matches);

		#appends form to allow the user to type a reply to a bleat using a prompt
		print <<eof;

<form id="reply_to_a_bleat" method="POST" action="">
  <input type="hidden" name="reply_bleat" id="reply_bleat">
  <input type="hidden" name="in_reply_to" id="in_reply_to">
  <input type="hidden" name="search_phrase" value="$search_term">
  <input type="hidden" name="search_type" value="$search_type">
</form>
eof

		#appends form for deleting a bleat
		print <<eof;
<form id="delete_a_bleat" method="POST" action="">
  <input type="hidden" name="bleat_to_delete" id="bleat_to_delete">
  <input type="hidden" name="search_phrase" value="$search_term">
  <input type="hidden" name="search_type" value="$search_type">
</form>
eof

	} elsif (%users) {
		print "<b>Found $i user matching \"$search_term\":</b>\n" if $i == 1;
		print "<b>Found $i users matching \"$search_term\":</b>\n" if $i > 1;
		format_user_results($i, %users);
	} else {
		print "No search results found for \"$search_term\"\n";
	}

	#appends form for viewing next 16 results if there were more than 16 results
	if ($i > 16 && !defined $supress) {
		print <<eof;

<div align="center">
  <form method="POST" action="">
    <input type="submit" name="more" value="Show more results" class="bitter_button">
    <input type="hidden" name="num_displayed" value="$display_up_to">
    <input type="hidden" name="search_phrase" value="$search_term">
    <input type="hidden" name="search_type" value="$search_type">
  </form>
</div>
eof
	}

}

#searches for and returns number of results regarding searches for users
sub find_user_results {
	my $search = $_[0];
	my @users = glob("$users_dir/*");
	my $i = 0;

	#finds all users matching $search
	for $user (@users) {
		my $username_to_search = $user;
		$username_to_search =~ s/.*\///;
		my $user_info = "$user/details.txt";

		if (index(lc $username_to_search, lc $search) != -1) {
			#matches user with given username
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
			open USER, "<", $user_info or die "Cannot open $user_info: $!";

			#obtains and checks full name of user
			foreach $line (<USER>) {
				$users{$user} = $1 and $i++ if $line =~ /^full_name: (.*\Q$search\E.*)/i;
			}

			close USER;
		}

	}

	return $i;
}

#searches for and returns number of results regarding searches for bleats
sub find_bleat_results {
	my $search = $_[0];
	my @bleats = glob("$bleats_dir/*");
	my $i = 0;

	#finds all bleats matching $search
	for $bleat (@bleats) {
		open BLEAT, $bleat or die "Cannot open $bleat: $!";

		#extracts the bleat message
		while (<BLEAT>) {
			$bleat_msg = $1 if $_ =~ /^bleat: (.+)/;
		}

		close BLEAT;
		push @bleat_matches, $bleat and $i++ if index(lc $bleat_msg, lc $search) != -1;
	}

	return $i;
}

#formats search results in human-readable form with links to relevant user page
sub format_user_results {
	my ($num_matches, %matches) = @_;
	my $i = 0;

	#prints a form for each match, displaying match and link to profile
	foreach $key (sort keys %matches) {

		#ensures that only 16 matches at a time are displayed
		if ($i >= $displayed_up_to) {
			last if $i == $display_up_to;
			print <<eof;
<p>
<i>$matches{$key}</i>
eof

			$key =~ s/$users_dir\///;
			print <<eof;
<form method="POST" action="">
  Username: <input type="submit" name="view_profile" value="$key" class="bitter_link">
  <input type="hidden" name="profile_to_view" value="$users_dir/$key">
</form>
<br>
eof
		}

		$i++;
	}

	#supresses view more bleats button if end of results reached
	my @arr = keys %matches;
	$supress = 1 if $i == $#arr + 1;
}

#toggles listening/unlistening to specified user
sub listen_to_user {
	my ($user, $current_user, $previous_page) = @_;
	my $user_profile = "$users_dir/$current_user/details.txt";

	#displays appropriate page banner
	if (defined param('search_phrase')) {
		display_page_banner(param('search_phrase'), param('search_type'));
	} else {
		display_page_banner();
	}

	#adds or removes specified user frm listens
	if ($user =~ /^Unlisten (.+)/) {
		$user_to_update = $1;
		open USER, "<", $user_profile or die "Cannot open $user_profile: $!";
		my $i = 0;

		#removes $unlisten_to user from the listen data
		while (<USER>) {
			$_ =~ s/$user_to_update//g;
			$_ =~ s/ $//;
			$lines[$i++] = $_;
		}

		close USER;

		#updates user detail file
		open USER, ">", $user_profile or die "Cannot write $user_profile: $!";
		print USER @lines;
		close USER;
	} elsif ($user =~ /^Listen to (.+)/) {
		$user_to_update = $1;
		open USER, "<", $user_profile or die "Cannot open $user_profile: $!";
		my $i = 0;

		#appends $listen_to user to the listen data
		while (<USER>) {
			if ($_ =~ /^(listens:.*)/) {
				my $current_listens = $1;
				$current_listens .= " $user_to_update\n";
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
	}

	#displays search results page if applicable
	if (defined param('search_phrase')) {
		display_search_results(param('search_phrase'), param('search_type'));
		return;
	}

	display_user_profile("$users_dir/$user_to_update") if $previous_page eq "profile";
	display_user_profile("$users_dir/$current_user") if $previous_page eq "home";
}

#provides a form for updating user profile details
sub update_details {
	my $user = $_[0];
	print "update details form\n";
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
  <link href="bitter.css" rel="stylesheet" type="text/css">
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
			encode_output($value);
			print "$param='$value' ";
		}

		print "-->\n";
	}

	print <<eof;
</body>
</html>
eof
}

#sanitises profile text by escaping all but safe html metacharacters
sub encode_profile_text {
	$_[0] =~ s/\&/&amp;/g;
	$_[0] =~ s/\"/&quot;/g;
	$_[0] =~ s/<(\/?[^bui]+)>/&lt;$1&gt;/gi; #allows only bold, italic and underline
}

#sanitises a given output string by escaping html metacharacters
sub encode_output(\$) {
	$_[0] =~ s/\&/&amp;/g;
	$_[0] =~ s/\"/&quot;/g;
	$_[0] =~ s/\</&lt;/g;
	$_[0] =~ s/\>/&gt;/g;
}
