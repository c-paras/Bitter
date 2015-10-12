#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);

#prints response header and start of html
print <<eof;
Content-type: text/html

<!DOCTYPE html>
<head>
  <title>A Guessing Game Player</title>
</head>
<body>
eof

warningsToBrowser(1);
$guess = param('guess') || 50;
$min_guess = param('min_guess') || 0;
$max_guess = param('max_guess') || 100;

if (defined param('higher')) {
	#guesses a higher number
	$min_guess = $guess + 1;
	$guess = ceil(($guess + $max_guess) / 2);
} elsif (defined param('lower')) {
	#guesses a lower number
	$max_guess = $guess - 1;
	$guess = floor(($guess + $min_guess) / 2);
} elsif (defined param('correct')) {
	#ends the game
	print <<eof;
<form method="POST" action="">
  I win!!!!
  <input type="submit" name="play_again" value="Play Again">
</form>
</body>
</html>
eof
	exit 0;
}

#prints user form for indicating correctness of guess
print <<eof;
<form method="POST" action="">
  My guess is: $guess
  <input type="submit" name="higher" value="Higher?">
  <input type="submit" name="correct" value="Correct?">
  <input type="submit" name="lower" value="Lower?">
  <input type="hidden" name="guess" value="$guess">
  <input type="hidden" name="min_guess" value="$min_guess">
  <input type="hidden" name="max_guess" value="$max_guess">
</form>
</body>
</html>
eof

#returns the ceiling of a real number
sub ceil {
	my $num = $_[0];
	my $new = int($num);
	return $new if $new >= $num;
	return $new + 1 if $new < $num;
}

#returns the floor of a real number
sub floor {
	my $num = $_[0];
	my $new = int($num);
	return $new if $new <= $num;
	return $new - 1 if $new > $num;
}
