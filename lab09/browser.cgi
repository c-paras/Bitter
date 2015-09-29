#!/bin/sh

echo Content-type: text/html
echo

#obtains environmental variables
ip=$REMOTE_ADDR
host_address=`host $ip | sed 's/^.* //' | sed 's/.$//'`
browser=$HTTP_USER_AGENT

cat <<eof
<!DOCTYPE html>
<head>
<title>Web Browser IP, Host and Software</title>
</head>
<body>
Your browser is running at IP address: <b>$ip</b>
<p>
Your browser is running on hostname: <b>$host_address</b>
<p>
Your browser identifies as: <b>$browser</b>
<p>
</body>
</html>
eof
