-- SQL code to update default B3 database tables to B3 version 1.10.4 --
-- --------------------------------------------------------

ALTER TABLE `clients` ADD `permmute` TINYINT(1) NOT NULL DEFAULT '0';

