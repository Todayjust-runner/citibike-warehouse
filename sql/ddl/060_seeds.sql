IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') OR COALESCE(CONVERT(nvarchar(128),(SELECT value FROM sys.extended_properties WHERE class=0 AND name=N'CitibikeWarehouseProject')),N'')<>N'citibike-warehouse' THROW 51000,'Use the protected project deployment entry point.',1;

SET IDENTITY_INSERT dim.bike_type ON;
INSERT dim.bike_type(bike_type_key,bike_type_code,bike_type_label,is_unknown,is_recognized) VALUES(0,NULL,N'未知车型',1,0),(1,N'classic_bike',N'普通自行车',0,1),(2,N'electric_bike',N'电助力车',0,1);
SET IDENTITY_INSERT dim.bike_type OFF;
SET IDENTITY_INSERT dim.member_type ON;
INSERT dim.member_type(member_type_key,member_type_code,member_type_label,is_unknown,is_recognized) VALUES(0,NULL,N'未知会员骑行类型',1,0),(1,N'member',N'member',0,1),(2,N'casual',N'casual',0,1);
SET IDENTITY_INSERT dim.member_type OFF;
INSERT dim.hour(hour_key,hour_label) VALUES
(0,'00:00'),
(1,'01:00'),
(2,'02:00'),
(3,'03:00'),
(4,'04:00'),
(5,'05:00'),
(6,'06:00'),
(7,'07:00'),
(8,'08:00'),
(9,'09:00'),
(10,'10:00'),
(11,'11:00'),
(12,'12:00'),
(13,'13:00'),
(14,'14:00'),
(15,'15:00'),
(16,'16:00'),
(17,'17:00'),
(18,'18:00'),
(19,'19:00'),
(20,'20:00'),
(21,'21:00'),
(22,'22:00'),
(23,'23:00');
