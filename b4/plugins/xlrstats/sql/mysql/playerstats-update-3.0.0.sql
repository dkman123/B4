# this will give an error message in the b3.log, 
# but the IF I came up with to test if the field exists is giving me an error too
# if you get errors that this field does NOT exist, this command needs to be run once
#ALTER TABLE `%s` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';

ALTER TABLE `%s` CHANGE `id` `id` INT UNSIGNED NOT NULL AUTO_INCREMENT;
