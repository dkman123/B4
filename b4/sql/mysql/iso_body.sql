CREATE TABLE IF NOT EXISTS `iso_body` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL, -- AUTO_INCREMENT,
  `description` VARCHAR(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `description` (`description`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- insert records
INSERT INTO `iso_body` (id, description) VALUES ('1',  'HEAD');
INSERT INTO `iso_body` (id, description) VALUES ('2',  'HELMET');
INSERT INTO `iso_body` (id, description) VALUES ('3',  'TORSO');
INSERT INTO `iso_body` (id, description) VALUES ('4',  'VEST');
INSERT INTO `iso_body` (id, description) VALUES ('5',  'LEFT ARM');
INSERT INTO `iso_body` (id, description) VALUES ('6',  'RIGHT ARM');
INSERT INTO `iso_body` (id, description) VALUES ('7',  'GROIN');
INSERT INTO `iso_body` (id, description) VALUES ('8',  'BUTT');
INSERT INTO `iso_body` (id, description) VALUES ('9',  'LEFT UPPER LEG');
INSERT INTO `iso_body` (id, description) VALUES ('10', 'RIGHT UPPER LEG');
INSERT INTO `iso_body` (id, description) VALUES ('11', 'LEFT LOWER LEG');
INSERT INTO `iso_body` (id, description) VALUES ('12', 'RIGHT LOWER LEG');
INSERT INTO `iso_body` (id, description) VALUES ('13', 'LEFT FOOT');
INSERT INTO `iso_body` (id, description) VALUES ('14', 'RIGHT FOOT');


-- UPDATE `iso_body` SET description = 'LEFT UPPER LEG' WHERE id = '9';
-- UPDATE `iso_body` SET description = 'RIGHT UPPER LEG' WHERE id = '10';
