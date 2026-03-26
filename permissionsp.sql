/* 1. The SQL Stored Procedure (Run once on SQL Server)
 Create this in a utility database (or master) 
using a sysadmin account.Using WITH EXECUTE AS OWNER 
allows the GitHub Runner to trigger this even if it doesn't have high permissions itself.


--Trustworthy Database Property: Because the procedure needs to 
--perform "high-privileged" actions outside of the master database 
--(like modifying logins or reaching into SSISDB), 
--the master database must be set to TRUSTWORTHY. 
--This allows the EXECUTE AS OWNER context to "leave" the database:
sql
ALTER DATABASE [master] SET TRUSTWORTHY ON;

add sql user execute permission

USE [master];
GRANT EXECUTE ON dbo.sp_ManageRunnerPermissions TO [YourSqlUser];


*/
CREATE PROCEDURE dbo.sp_ManageRunnerPermissions
    @LoginName NVARCHAR(256),
    @Action NVARCHAR(10) -- 'GRANT' or 'REVOKE'
WITH EXECUTE AS OWNER
AS
BEGIN
    IF @Action = 'GRANT'
    BEGIN
        IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = @LoginName)
            EXEC('CREATE LOGIN [' + @LoginName + '] FROM WINDOWS');

        USE [SSISDB];
        IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = @LoginName)
            EXEC('CREATE USER [' + @LoginName + '] FOR LOGIN [' + @LoginName + ']');
        
        ALTER ROLE [ssis_admin] ADD MEMBER @LoginName;
    END
    ELSE IF @Action = 'REVOKE'
    BEGIN
        USE [SSISDB];
        IF EXISTS (SELECT * FROM sys.database_principals WHERE name = @LoginName)
            ALTER ROLE [ssis_admin] DROP MEMBER @LoginName;
    END
END
