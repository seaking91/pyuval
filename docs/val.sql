CREATE TABLE `clients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `active` tinyint(1) DEFAULT '1',
  `created` int(11) NOT NULL,
  `secret` varchar(60) NOT NULL DEFAULT '',
  `email` varchar(255) DEFAULT NULL,
  `notes` varchar(100) DEFAULT '',
  `otp` varchar(100) DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `yubikeys` (
  `active` tinyint(1) DEFAULT '1',
  `created` int(11) NOT NULL,
  `modified` int(11) NOT NULL,
  `yk_publicname` varchar(16) NOT NULL,
  `yk_counter` int(11) NOT NULL,
  `yk_use` int(11) NOT NULL,
  `yk_low` int(11) NOT NULL,
  `yk_high` int(11) NOT NULL,
  `nonce` varchar(40) DEFAULT '',
  `notes` varchar(100) DEFAULT '',
  PRIMARY KEY (`yk_publicname`),
  UNIQUE KEY `yk_publicname` (`yk_publicname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;