
#
# Table structure for table `mapresult`
#

CREATE TABLE `mapresult` (
  `id` int(11) NOT NULL auto_increment,
  `mapname` varchar(50) NOT NULL default '',
  `redscore` int(11) NOT NULL default '0',
  `bluescore` int(11) NOT NULL default '0',
  `maptime` varchar(6) NOT NULL default '00:00',
  `createddate` datetime NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 ;
