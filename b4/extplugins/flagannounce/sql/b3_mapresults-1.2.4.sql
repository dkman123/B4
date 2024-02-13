
#
# add field to table `mapresult`
#

ALTER TABLE `mapresult` ADD `lowplayer` int NOT NULL DEFAULT 0;
ALTER TABLE `mapresult` ADD `highplayer` int NOT NULL DEFAULT 0;
