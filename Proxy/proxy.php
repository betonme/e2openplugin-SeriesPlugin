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
	$GA_Variable = '';
	$GA_Value = '';
	include('ga.php');


	/*
	Copyright (c) 2011 Manuel Strehl
	
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	
	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.
	
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
	*/
	
	// check preconditions
	if (! isset($_GET['url'])) {
		header('HTTP/1.0 400 Bad Request');
		header('Content-Type: application/json');
		echo 'null';
		exit(1);
	}
	
	// allow requests only to these domains
	$whitelist = array('www.wunschliste.de', 'www.fernsehserien.de');
	 
	// cache ressources for 1 day = one hour * 24 * 1
	$cache_duration = 60*60 *24*1;
	$then = mktime() - $cache_duration;
	$expires = $then + 2*$cache_duration;
	$max_age = $cache_duration;
	
	$url = $_GET['url'];
	$db = new PDO("sqlite:".dirname(__FILE__)."/cache.sqlite");
	$stm = $db->prepare('select 1 from cache'); // this is the test
	if ($stm === False) {
			// set up the table
			$db->exec('CREATE TABLE cache (url TEXT,
																		 type TEXT,
																		 content BLOB,
																		 age INTEGER,
																		 UNIQUE(url))');
	}
	
	// Fetch entry from DB
	$stm = $db->prepare("SELECT content, type, age FROM cache WHERE url = ? AND age > ?");
	$stm->execute(array($url, $then));
	$entry = $stm->fetch(PDO::FETCH_ASSOC);
	
	// no entry found in cache
	if ($entry === False) {
			// prune cache
			$stm = $db->prepare('DELETE FROM cache WHERE url = ? OR age < ?');
			$stm->execute(array($url, $then));
	
			// fetch a current version
			$entry = fetch_entry($url);
	
			if ($entry['type'] !== NULL) {
					$stm = $db->prepare("INSERT INTO cache ( url, type, content, age )
																	VALUES (?, ?, ?, strftime('%s', 'now'))");
					$stm->execute(array($url, $entry['type'], $entry['content']));
			} else {
					// something went wrong
					$entry = array(
							'type' => 'application/json',
							'content' => 'null',
					);
			}
			global $GA_Variable, $GA_Value;
			$GA_Variable = 'Cached';
			$GA_Value = 'Yes';
	} else {
			$expires = $entry['age'] + $cache_duration;
			$max_age = $entry['age'] - $then;
			global $GA_Variable, $GA_Value;
			$GA_Variable = 'Cached';
			$GA_Value = 'No';
	}
	
	header('Content-Type: '.$entry['type']);
	header('Expires: '.date('r', $expires));
	header('Cache-Control: max-age='.$max_age);
	echo $entry['content'];
	
	
	/**
	 * Fetch a ressource
	 * @param string $url The URL of the ressource
	 * @return array MIME type and actual content
	 */
	function fetch_entry($url) {
			global $whitelist;
			$host = parse_url($url, PHP_URL_HOST);
			$accepted = False;
			foreach ($whitelist as $test) {
					// check the host against each whitelist entry
					if ($test === $host) {
							$accepted = True;
							break;
					}
			}
			$t = $c = NULL;
	
			if ($accepted) {
					$ch = curl_init();
					curl_setopt($ch, CURLOPT_URL, $url);
					curl_setopt($ch, CURLOPT_USERAGENT, "My little cacher");
					curl_setopt($ch, CURLOPT_HEADER, 1); // we want the HTTP headers, too
					curl_setopt($ch, CURLOPT_RETURNTRANSFER, true); // we need the stuff as 
																													// string, not printed out
					curl_setopt($ch, CURLOPT_TIMEOUT, 10); // set a timeout for safety
	
					// the output is normalized to UNIX line endings (ASCII x10)
					$output = str_replace("\r\n", "\n", curl_exec($ch));
					curl_close($ch);
	
					// if there is output, try to find out the MIME type and determine the
					// content
					if ($output) {
							list($h, $c) = explode("\n\n", $output, 2);
							$h = explode("\n", $h);
							$t = "text/plain";
							foreach ($h as $line) {
									if (substr(strtolower($line), 0, 13) === "content-type:") {
											$t = trim(preg_replace('/^Content-Type:\s*(.*)$/i', '$1', $line));
											break;
									}
							}
					}
			} else {
					$t = 'application/json';
					$c = '{"error":"forbidden"}';
			}
			return array(
					'type' => $t,
					'content' => $c
			);
	}
	
	trackPageView($GA_Account, 'SeriesPlugin Proxy', $GA_Variable, $GA_Value);
	
	// Only if You want to debug something 
	//print_r(error_get_last());
	
	/* The PDO class does not come with a function for closing a connection, and so any PDO connection will sit idle until you explicitly dispose of it. */
	unset($db);
?>