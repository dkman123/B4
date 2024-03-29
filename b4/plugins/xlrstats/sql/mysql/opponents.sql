CREATE TABLE IF NOT EXISTS `%s` (
  `id` MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `target_id` SMALLINT UNSIGNED NOT NULL DEFAULT '0',
  `killer_id` SMALLINT UNSIGNED NOT NULL DEFAULT '0',
  `kills` SMALLINT UNSIGNED NOT NULL DEFAULT '0',
  `retals` SMALLINT UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `target_id` (`target_id`),
  KEY `killer_id` (`killer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;