<?php
	ini_set('display_errors', false);
	error_reporting(0);
 
	if ( floatval($_REQUEST['version']) < 0.9){
		header("X-PHP-Response-Code: 401", true, 401);
		echo "Upgrade Your Plugin";
		return;
	}
	
	//if pregmatch('/wunschliste/',$_Request['url'] )
	//else if pregmatch('/fernsehserien/',$_Request['url'] )
	//else 
	
	echo "Valid License";
?>