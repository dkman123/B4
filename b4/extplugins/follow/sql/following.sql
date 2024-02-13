--
-- Estructura de tabla para la tabla `following`
-- Table structure for 'following'
--

CREATE TABLE IF NOT EXISTS `following` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `time_add` int(11) NOT NULL,
  `reason` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `following_client_id` (`client_id`),
  KEY `following_admin_id` (`admin_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 ;
