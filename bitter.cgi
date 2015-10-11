#!/usr/bin/perl -w
#Written by Constantinos Paraskevopoulos in October 2015
#Provides a social media platform analogous to Twitter

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

page_header();
warningsToBrowser(1);

#defines global variables
$debug = 1;
$dataset_size = "small";
$users_dir = "dataset-$dataset_size/users";
$bleats_dir = "dataset-$dataset_size/bleats";
    
display_user_profile();
page_trailer();
exit 0;

#shows formatted details of a user's profile
sub display_user_profile {
	my $n = param('n') || 0;
	my @users = sort(glob("$users_dir/*"));

	#stores paths to user's profile entities
	my $user_to_show  = $users[$n % @users];
	my $details_filename = "$user_to_show/details.txt";
	my $image_filename = "$user_to_show/profile.jpg";
	my $bleats_filename = "$user_to_show/bleats.txt";

	#obtains and prints the user's profile
	print user_details($details_filename, $image_filename);
	print user_bleats($bleats_filename);

	my $next_user = $n + 1;

	#prints form to move to next user
	print <<eof;
<form method="POST" action="">
  <input type="hidden" name="n" value="$next_user">
  <input type="submit" value="Next user" class="bitter_button">
</form>
eof
}

#obtains a user's information and profile image
sub user_details {
	my ($details_filename, $image_filename) = @_;
	open DETAILS, "$details_filename" or die "Cannot open $details_filename: $!";

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
<table>
  <tr>
    <td><img src="$image_filename" alt="user_image"></td>
    <td>
      <b><font size="15">$name</font></b>

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
			open BLEAT, "$bleats_dir/$bleat" or die "Cannot open $bleat: $!";
			$bleats_to_display .= "<div class='bitter_block'>\n";
			my ($reply, $time, $latitude, $longitude) = "";

			#extracts information about the bleat
			foreach $line (<BLEAT>) {
				if ($line =~ /^username: (.+)/) {
					$bleater = $1;
				} elsif ($line =~ /^bleat: (.+)/) {
					$bleat_to_display = $1;
				} elsif ($line =~ /^time: (.+)/) {
					$time = $1;
				} elsif ($line =~ /^in_reply_to: (.+)/) {
					$reply = $1;
				} elsif ($line =~ /^latitude: (.+)/) {
					$latitude = $1;
				} elsif ($line =~ /^longitude: (.+)/) {
					$longitude = $1;
				}
			}

			close BLEAT;
			$bleats_to_display .= "<b>$bleater</b> bleated <i>$bleat_to_display</i>";

			#provides info about original bleat if applicable
			if ($reply ne "") {
				open BLEAT, "$bleats_dir/$reply" or die "Cannot open $reply: $!";

				#extracts information about the original bleat
				foreach $line (<BLEAT>) {
					if ($line =~ /^username: (.+)/) {
						$bleater = $1;
					} elsif ($line =~ /^bleat: (.+)/) {
						$bleated = $1;
					}
				}

				$bleats_to_display .= " in response to a bleat by <b>$bleater</b>: <i>$bleated</i><br>\n";
				close BLEAT;
			} else {
				$bleats_to_display .= "<br>\n";
			}

			#appends rest of info about bleat to string
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
	print <<eof
Content-Type: text/html

<!DOCTYPE html>
<head>
<title>Bitter</title>
<link href="bitter.css" rel="stylesheet">
</head>
<body>
<div class="bitter_heading">Bitter</div>
eof
}

#placed at the bottom of every page
#provides debugging information if global variable $debug is set
sub page_trailer {
	my $html = "";
	$html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
	$html .= "</body>\n</html>";
	print $html;
}
