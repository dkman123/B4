---- Create procedure to catch temp ban evaders

---- unneeded, i put the logic into the query built within b3

--DROP PROCEDURE IF EXISTS GetClientPenaltiesByIP;

--CREATE PROCEDURE GetClientPenaltiesByIP (IN client_ip VARCHAR(16))
--READS SQL DATA
--SELECT * 
--FROM penalties 
--WHERE (time_expire = -1 OR time_expire > UNIX_TIMESTAMP()) 
--AND client_id IN (SELECT id FROM clients WHERE ip = client_ip);

---- use CALL GetClientPenaltiesByIP('client_ip_here');
