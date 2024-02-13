-- SQL code to update default B3 database tables to B3 version 1.10.3 --
-- --------------------------------------------------------

-- Alter the login field of the client table (email can be no longer than 254 characters)
ALTER TABLE `clients` ADD `app` VARCHAR(32) NOT NULL DEFAULT '';

-- the country 2 letter iso code
ALTER TABLE `clients` ADD `isocode` CHAR(2) NOT NULL DEFAULT '';

