CREATE TABLE `yubikeys` (
  `serialnr` int(11) NOT NULL,
  `publicname` varchar(16) NOT NULL,
  `created` varchar(24) NOT NULL,
  `internalname` varchar(12) NOT NULL,
  `aeskey` text,
  `lockcode` varchar(12) NOT NULL,
  `creator` varchar(8) NOT NULL,
  `active` tinyint(1) DEFAULT '1',
  `hardware` tinyint(1) DEFAULT '1',
  `user` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`publicname`),
  UNIQUE KEY `publicname` (`publicname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;