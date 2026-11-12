IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') OR COALESCE(CONVERT(nvarchar(128),(SELECT value FROM sys.extended_properties WHERE class=0 AND name=N'CitibikeWarehouseProject')),N'')<>N'citibike-warehouse' THROW 51000,'Use the protected project deployment entry point.',1;

IF SCHEMA_ID(N'meta') IS NULL EXEC(N'CREATE SCHEMA [meta] AUTHORIZATION dbo');
IF SCHEMA_ID(N'ods') IS NULL EXEC(N'CREATE SCHEMA [ods] AUTHORIZATION dbo');
IF SCHEMA_ID(N'dim') IS NULL EXEC(N'CREATE SCHEMA [dim] AUTHORIZATION dbo');
IF SCHEMA_ID(N'dwd') IS NULL EXEC(N'CREATE SCHEMA [dwd] AUTHORIZATION dbo');
IF SCHEMA_ID(N'dws') IS NULL EXEC(N'CREATE SCHEMA [dws] AUTHORIZATION dbo');
IF SCHEMA_ID(N'ads') IS NULL EXEC(N'CREATE SCHEMA [ads] AUTHORIZATION dbo');
