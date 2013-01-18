<?php
	// Only if You want to debug something 
	error_reporting(0);
	//error_reporting(E_ALL);
	
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
	
	echo "Valid License";
?>