CREATE TABLE IF NOT EXISTS `iso_weapon` (
  `id` INT(11) UNSIGNED NOT NULL, -- AUTO_INCREMENT,
  `description` VARCHAR(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `description` (`description`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- insert records
INSERT INTO `iso_weapon` (id, description) VALUES ('1',  'MOD_WATER');  -- drowning
INSERT INTO `iso_weapon` (id, description) VALUES ('3',  'MOD_LAVA');  -- lava
INSERT INTO `iso_weapon` (id, description) VALUES ('5',  'MOD_TELEFRAG');  -- having someone teleport on top of you
INSERT INTO `iso_weapon` (id, description) VALUES ('6',  'MOD_FALLING');  -- falling damage
INSERT INTO `iso_weapon` (id, description) VALUES ('7',  'MOD_SUICIDE');  -- /kill command
INSERT INTO `iso_weapon` (id, description) VALUES ('9',  'MOD_TRIGGER_HURT');  -- finding well placed hurt
INSERT INTO `iso_weapon` (id, description) VALUES ('10', 'MOD_CHANGE_TEAM');  -- changing team
INSERT INTO `iso_weapon` (id, description) VALUES ('12', 'KNIFE');  -- knife
INSERT INTO `iso_weapon` (id, description) VALUES ('13', 'KNIFE_THROWN');  -- thrown knife
INSERT INTO `iso_weapon` (id, description) VALUES ('14', 'BERETTA');  -- baretta pistol
INSERT INTO `iso_weapon` (id, description) VALUES ('15', 'DEAGLE');  -- DE pistol
INSERT INTO `iso_weapon` (id, description) VALUES ('16', 'SPAS');  -- spas shotgun
INSERT INTO `iso_weapon` (id, description) VALUES ('17', 'UMP45');  -- ump secondary
INSERT INTO `iso_weapon` (id, description) VALUES ('18', 'MP5K');  -- mp5k secondary
INSERT INTO `iso_weapon` (id, description) VALUES ('19', 'LR300');  -- lr300 primary
INSERT INTO `iso_weapon` (id, description) VALUES ('20', 'G36');  -- g36 primary
INSERT INTO `iso_weapon` (id, description) VALUES ('21', 'PSG1');  -- psg1 sniper rifle
INSERT INTO `iso_weapon` (id, description) VALUES ('22', 'HK69');  -- hk69 explosion
INSERT INTO `iso_weapon` (id, description) VALUES ('23', 'BLED');  -- bleed damage
INSERT INTO `iso_weapon` (id, description) VALUES ('24', 'KICKED');  -- player kick/boot
INSERT INTO `iso_weapon` (id, description) VALUES ('25', 'HE_GRENADE');  -- HE grenade
INSERT INTO `iso_weapon` (id, description) VALUES ('28', 'SR8');  -- sr8 sniper rifle
INSERT INTO `iso_weapon` (id, description) VALUES ('30', 'AK103');  -- ak primary
INSERT INTO `iso_weapon` (id, description) VALUES ('31', 'SPLODED');  -- self HE grenade in hand
INSERT INTO `iso_weapon` (id, description) VALUES ('32', 'SLAPPED');  -- slap rcon command
INSERT INTO `iso_weapon` (id, description) VALUES ('33', 'SMITED');  -- smite rcon command
INSERT INTO `iso_weapon` (id, description) VALUES ('34', 'BOMBED');  -- probably bomb mode explosion
INSERT INTO `iso_weapon` (id, description) VALUES ('35', 'NUKED');  -- nuke rcon command
INSERT INTO `iso_weapon` (id, description) VALUES ('36', 'NEGEV');  -- negev primary
INSERT INTO `iso_weapon` (id, description) VALUES ('37', 'HK69_HIT');  -- hk69 direct hit
INSERT INTO `iso_weapon` (id, description) VALUES ('38', 'M4');  -- m4 primary
INSERT INTO `iso_weapon` (id, description) VALUES ('39', 'GLOCK');  -- glock pistol
INSERT INTO `iso_weapon` (id, description) VALUES ('40', 'COLT1911'); -- colt 1911 pistol
INSERT INTO `iso_weapon` (id, description) VALUES ('41', 'MAC11');  -- mac11 secondary
INSERT INTO `iso_weapon` (id, description) VALUES ('42', 'FRF1');  -- frf1 sniper rifle
INSERT INTO `iso_weapon` (id, description) VALUES ('43', 'BENELLI');  -- benelli shotgun secondary
INSERT INTO `iso_weapon` (id, description) VALUES ('44', 'P90');  -- p90 secondary
INSERT INTO `iso_weapon` (id, description) VALUES ('45', 'MAGNUM');  -- magnum pistol
INSERT INTO `iso_weapon` (id, description) VALUES ('46', 'TOD50');  -- the instagib rifle
INSERT INTO `iso_weapon` (id, description) VALUES ('47', 'FLAG');  -- hot potato, flag explosion
INSERT INTO `iso_weapon` (id, description) VALUES ('48', 'GOOMBA');  -- curb stomp, landing on someone's head
