-- SQL code to update default B3 database tables to B3 version 1.9.0 --
-- --------------------------------------------------------
-- to run from mysql window:  source <filename>
-- STOP B3 before running this, or it will appear to "hang" waiting for exclusive lock

-- rename table groups to usergroups
SELECT Count(*)
INTO @exists
FROM information_schema.tables
WHERE table_schema = 'b3'
    AND table_type = 'BASE TABLE'
    AND table_name = 'usergroups';

SET @query = if(@exists = 0,
    'RENAME TABLE `groups` TO usergroups',
    'SELECT \'nothing to rename\' status');

--select @query;

PREPARE stmt FROM @query;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;
