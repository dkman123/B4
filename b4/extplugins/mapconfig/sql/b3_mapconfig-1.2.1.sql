
#
# Table structure for table `mapconfig`
#

CREATE TABLE `mapconfig` (
  `id` int(11) NOT NULL auto_increment,
  `mapname` varchar(50) NOT NULL default '',
  `capturelimit` int(11) NOT NULL default '8',
  `g_suddendeath` int(11) NOT NULL default '0',
  `g_gear` varchar(100) NOT NULL default '0',
  `g_gravity` int(11) NOT NULL default '800',
  `g_friendlyfire` int(11) NOT NULL default '2',
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 ;

#
# unique map name index
#
CREATE UNIQUE INDEX mapconfig_mapname_ux
ON mapconfig(mapname);

#
# Dumping data for table `links`
#s

INSERT INTO `mapconfig` (mapname) VALUES ('ut4_turnpike');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_paris');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_algiers');
INSERT INTO `mapconfig` (mapname, g_gear) VALUES ('ut4_barn', 'FGHIJKLMNZacefghijklQR');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_paris');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_bohemia');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_kingdom');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_austria');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_abbey');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_prague');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_cascade');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_mandolin');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_uptown');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_kingpin');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_city6', 'FGIJKLMZacefghijklQUV');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_elgin');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_ghosttown');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_swim');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_ramelle');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_raiders');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_riyadh');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_eagle');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_suburbs');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_thingley');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_tombs');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_docks');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_ricochet');
INSERT INTO `mapconfig` (mapname) VALUES ('ut4_casa');



