SET NOCOUNT ON;
DECLARE @catalog nvarchar(max)=(SELECT
 JSON_QUERY(COALESCE((SELECT name FROM sys.schemas WHERE schema_id BETWEEN 5 AND 16383 ORDER BY name FOR JSON PATH),N'[]')) AS schemas,
 JSON_QUERY(COALESCE((SELECT s.name+'.'+t.name AS table_name,c.name AS column_name,
  ty.name+CASE WHEN ty.name IN('nvarchar','nchar') THEN '('+CASE WHEN c.max_length=-1 THEN 'max' ELSE CONVERT(varchar(8),c.max_length/2) END+')'
   WHEN ty.name IN('varchar','char','varbinary','binary') THEN '('+CASE WHEN c.max_length=-1 THEN 'max' ELSE CONVERT(varchar(8),c.max_length) END+')'
   WHEN ty.name IN('decimal','numeric') THEN '('+CONVERT(varchar(8),c.precision)+','+CONVERT(varchar(8),c.scale)+')'
   WHEN ty.name IN('datetime2','datetimeoffset','time') THEN '('+CONVERT(varchar(8),c.scale)+')' ELSE '' END AS sql_type,
  c.is_nullable,c.is_identity,c.is_computed,CONVERT(bit,COALESCE(cc.is_persisted,0)) AS is_persisted,cc.definition,c.collation_name
  FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id JOIN sys.columns c ON c.object_id=t.object_id
  JOIN sys.types ty ON ty.user_type_id=c.user_type_id LEFT JOIN sys.computed_columns cc ON cc.object_id=c.object_id AND cc.column_id=c.column_id
  WHERE t.is_ms_shipped=0 ORDER BY s.name,t.name,c.column_id FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS columns,
 JSON_QUERY(COALESCE((SELECT s.name+'.'+t.name AS table_name,k.name,RTRIM(k.type) AS kind,
  (SELECT STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY ic.key_ordinal)
   FROM sys.index_columns ic JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
   WHERE ic.object_id=k.parent_object_id AND ic.index_id=k.unique_index_id AND ic.key_ordinal>0) AS key_columns
  FROM sys.key_constraints k JOIN sys.tables t ON t.object_id=k.parent_object_id JOIN sys.schemas s ON s.schema_id=t.schema_id
  WHERE t.is_ms_shipped=0 FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS keys,
 JSON_QUERY(COALESCE((SELECT OBJECT_SCHEMA_NAME(f.parent_object_id)+'.'+OBJECT_NAME(f.parent_object_id) AS table_name,f.name,
  (SELECT STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY fc.constraint_column_id)
   FROM sys.foreign_key_columns fc JOIN sys.columns c ON c.object_id=fc.parent_object_id AND c.column_id=fc.parent_column_id WHERE fc.constraint_object_id=f.object_id) AS key_columns,
  OBJECT_SCHEMA_NAME(f.referenced_object_id)+'.'+OBJECT_NAME(f.referenced_object_id) AS reference_table,
  (SELECT STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY fc.constraint_column_id)
   FROM sys.foreign_key_columns fc JOIN sys.columns c ON c.object_id=fc.referenced_object_id AND c.column_id=fc.referenced_column_id WHERE fc.constraint_object_id=f.object_id) AS reference_columns,
  f.delete_referential_action_desc AS delete_action,f.update_referential_action_desc AS update_action,f.is_disabled,f.is_not_trusted
  FROM sys.foreign_keys f FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS foreign_keys,
 JSON_QUERY(COALESCE((SELECT OBJECT_SCHEMA_NAME(c.parent_object_id)+'.'+OBJECT_NAME(c.parent_object_id) AS table_name,
  c.name,c.definition,c.is_disabled,c.is_not_trusted FROM sys.check_constraints c WHERE c.is_ms_shipped=0 FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS checks,
 JSON_QUERY(COALESCE((SELECT s.name+'.'+t.name AS table_name,i.name,
  (SELECT STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY ic.key_ordinal)
   FROM sys.index_columns ic JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
   WHERE ic.object_id=i.object_id AND ic.index_id=i.index_id AND ic.key_ordinal>0) AS key_columns,
  COALESCE((SELECT STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY ic.index_column_id)
   FROM sys.index_columns ic JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
   WHERE ic.object_id=i.object_id AND ic.index_id=i.index_id AND ic.is_included_column=1),N'') AS include_columns,
  i.is_unique,i.is_primary_key,i.type_desc,i.filter_definition,i.is_disabled
  FROM sys.indexes i JOIN sys.tables t ON t.object_id=i.object_id JOIN sys.schemas s ON s.schema_id=t.schema_id
  WHERE t.is_ms_shipped=0 AND i.index_id>0 FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS indexes,
 JSON_QUERY(COALESCE((SELECT s.name+'.'+o.name AS name,RTRIM(o.type) AS type,m.definition,
  CONVERT(bit,COALESCE(tr.is_disabled,0)) AS is_disabled
  FROM sys.objects o JOIN sys.schemas s ON s.schema_id=o.schema_id JOIN sys.sql_modules m ON m.object_id=o.object_id
  LEFT JOIN sys.triggers tr ON tr.object_id=o.object_id WHERE o.is_ms_shipped=0 AND o.type IN('P','TR','FN','IF','TF','V')
  FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')) AS modules
 FOR JSON PATH,WITHOUT_ARRAY_WRAPPER);
SELECT N'__CATALOG_BEGIN__'+@catalog+N'__CATALOG_END__';
