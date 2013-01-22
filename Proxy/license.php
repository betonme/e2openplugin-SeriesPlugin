<?php
	// Only if You want to debug something 
	error_reporting(0);
	//error_reporting(E_ALL);

	// buffer all upcoming output
	ob_start();

	echo "Valid License";

	// get the size of the output
	$size = ob_get_length();

	// send headers to tell the browser to close the connection
	header("Content-Length: $size");
	header('Connection: close');

	// flush all output
	ob_end_flush();
	ob_flush();
	flush();

	// close current session
	if (session_id()) session_write_close();

	/******** background process starts here ********/

	// Google Analytics without utilizing the clients
	// 25.04.202 by Frank Glaser
	// http://tecjunkie.blogspot.de/2012/04/google-analytics-without-utilizing.html
	// Very helpfull:
	// https://developers.google.com/analytics/resources/articles/gaTrackingTroubleshooting?hl=de-DE#gifParameters
	// http://www.slideshare.net/yuhuibc/how-to-check-google-analytics-tags-7532272
	$GA_Account = 'MO-31168065-1';

	include('ga.php');
	
	// check preconditions
	if (! isset($_GET['url'])) {
		header('HTTP/1.0 400 Bad Request');
		echo 'Parameter missing';
		exit(1);
	}
	
	$GA_Variable = 'Url';
	$GA_Value = $_GET['url'];
	
	trackPageView($GA_Account, 'SeriesPlugin Proxy', $GA_Variable, $GA_Value);
?>