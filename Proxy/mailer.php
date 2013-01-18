<?php

	function mail_att($replyname, $replyto, $mailto, $subject, $message, $att) {
		
		$mime_boundary = "-----=" . md5(uniqid(mt_rand(), 1)); 
		
		$header  ="From:".$replyname."<".$replyto.">\n"; 
		$header .= "Reply-To: ".$reply."\n"; 
		
		$header.= "MIME-Version: 1.0\r\n"; 
		$header.= "Content-Type: multipart/mixed;\r\n"; 
		$header.= " boundary=\"".$mime_boundary."\"\r\n"; 
		
		//$content = "This is a multi-part message in MIME format.\r\n\r\n"; 
		//$content.= "--".$mime_boundary."\r\n"; 
		//$content.= "Content-Type: text/html charset=\"iso-8859-1\"\r\n"; 
		//$content.= "Content-Transfer-Encoding: 8bit\r\n\r\n"; 
		$content = $message."\r\n"; 
		
		if (isset($att)){
			if(is_array($att) AND is_array(current($att))) { 
				foreach($att AS $dat) { 
					$data = chunk_split(base64_encode($dat['data'])); 
					$content.= "--".$mime_boundary."\r\n"; 
					$content.= "Content-Disposition: attachment;\r\n"; 
					$content.= "\tfilename=\"".$dat['name']."\";\r\n"; 
					$content.= "Content-Length: .".$dat['size'].";\r\n"; 
					$content.= "Content-Type: ".$dat['type']."; name=\"".$dat['name']."\"\r\n"; 
					$content.= "Content-Transfer-Encoding: base64\r\n\r\n"; 
					$content.= $data."\r\n"; 
				} 
				$content .= "--".$mime_boundary."--";  
			} else { 
				$data = chunk_split(base64_encode($att['data'])); 
				$content.= "--".$mime_boundary."\r\n"; 
				$content.= "Content-Disposition: attachment;\r\n"; 
				$content.= "\tfilename=\"".$att['name']."\";\r\n"; 
				$content.= "Content-Length: .".$dat['size'].";\r\n"; 
				$content.= "Content-Type: ".$att['type']."; name=\"".$att['name']."\"\r\n"; 
				$content.= "Content-Transfer-Encoding: base64\r\n\r\n"; 
				$content.= $data."\r\n"; 
			}
		}
		
		return mail($mailto, $subject, $content, $header);
	}
	
	$subject    = $_REQUEST["subject"];
	$message    = $_REQUEST["message"];
	$replyto    = $_REQUEST["replyto"];
	$replyname  = $_REQUEST["replyname"];
	
	$mailto   = "glaserfrank@gmail.com";
	
	echo "$subject\n\n";
	echo "$message\n\n";
	echo "$replyname $replyto\n\n";
	
	$att= array(); 
	$att["name"] = $_FILES['logfile']['name']; 
	$att["size"] = $_FILES['logfile']['size']; 
	$att["type"] = $_FILES['logfile']['type']; 
	$att["data"] = implode("",file($_FILES['logfile']['tmp_name'])); 
	
	$result= mail_att($replyname, $replyto, $mailto.','.$replyto, $subject, $message, $att);
	
	if($result) {
	    echo "Nachricht erfolgreich versendet.";
	} else {
	    echo "Fehler: \nDie Nachricht wurde nicht fuer den Versand akzeptiert: \n$result";
	}
?>