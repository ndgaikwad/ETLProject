USE [master];
GO

-- 1. Create a certificate for signing
IF NOT EXISTS (SELECT * FROM sys.certificates WHERE name = 'RunnerDeploySignerCert')
    CREATE CERTIFICATE RunnerDeploySignerCert 
    WITH SUBJECT = 'Certificate for SSIS and DACPAC Runner Management';
GO

-- 2. Create the Stored Procedure
IF OBJECT_ID('dbo.sp_ManageRunnerPermissions') IS NOT NULL 
    DROP PROCEDURE dbo.sp_ManageRunnerPermissions;
GO

CREATE PROCEDURE dbo.sp_ManageRunnerPermissions
    @LoginName NVARCHAR(256),
    @Action NVARCHAR(10),   -- 'GRANT' or 'REVOKE'
    @UserDB NVARCHAR(128) = NULL  -- Optional: Target database for DACPAC
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'GRANT'
    BEGIN
        -- Create Login from Windows
        IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = @LoginName)
            EXEC('CREATE LOGIN [' + @LoginName + '] FROM WINDOWS');

        -- Permission for SSISDB
        EXEC('USE [SSISDB]; 
              IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = ''' + @LoginName + ''')
                  CREATE USER [' + @LoginName + '] FOR LOGIN [' + @LoginName + '];
              ALTER ROLE [ssis_admin] ADD MEMBER [' + @LoginName + '];');

        -- Permission for UserDB (DACPAC) if provided
        IF @UserDB IS NOT NULL
            EXEC('USE [' + @UserDB + ']; 
                  IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = ''' + @LoginName + ''')
                      CREATE USER [' + @LoginName + '] FOR LOGIN [' + @LoginName + '];
                  ALTER ROLE [db_owner] ADD MEMBER [' + @LoginName + '];');
    END
    
    ELSE IF @Action = 'REVOKE'
    BEGIN
        -- 1. Kill active sessions for the runner to allow DROP
        DECLARE @spid INT;
        DECLARE session_cursor CURSOR FOR 
            SELECT session_id FROM sys.dm_exec_sessions WHERE login_name = @LoginName;
        OPEN session_cursor;
        FETCH NEXT FROM session_cursor INTO @spid;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC('KILL ' + @spid);
            FETCH NEXT FROM session_cursor INTO @spid;
        END
        CLOSE session_cursor; DEALLOCATE session_cursor;

        -- 2. Cleanup UserDB if provided
        IF @UserDB IS NOT NULL
            EXEC('USE [' + @UserDB + ']; IF EXISTS (SELECT * FROM sys.database_principals WHERE name = ''' + @LoginName + ''') DROP USER [' + @LoginName + '];');

        -- 3. Cleanup SSISDB
        EXEC('USE [SSISDB]; IF EXISTS (SELECT * FROM sys.database_principals WHERE name = ''' + @LoginName + ''') DROP USER [' + @LoginName + '];');

        -- 4. Drop Login from Master
        IF EXISTS (SELECT * FROM sys.server_principals WHERE name = @LoginName)
            EXEC('DROP LOGIN [' + @LoginName + ']');
    END
END;
GO

-- 3. Secure the procedure
ADD SIGNATURE TO dbo.sp_ManageRunnerPermissions BY CERTIFICATE RunnerDeploySignerCert;
GO

-- 4. Proxy Login for elevated rights
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'RunnerSignerLogin')
BEGIN
    CREATE LOGIN RunnerSignerLogin FROM CERTIFICATE RunnerDeploySignerCert;
    ALTER SERVER ROLE [sysadmin] ADD MEMBER RunnerSignerLogin;
END
GO

-- 5. Grant Execute to your low-privilege GitHub SQL User
GRANT EXECUTE ON dbo.sp_ManageRunnerPermissions TO [Your_Pipeline_SQL_User];
GO

One-Time Manual Test
Before you run your first pipeline, I recommend testing the flow manually in SSMS using the low-privilege user to confirm the certificate signing is working:
-- Log in as your low-privilege 'Your_Pipeline_SQL_User'
-- Then run:
EXEC master.dbo.sp_ManageRunnerPermissions 
    @LoginName = 'DOMAIN\YourRunnerAccount', 
    @Action = 'GRANT', 
    @UserDB = 'MyTargetDB';

-- Verify the login was created in master and the user in SSISDB/UserDB
-- Then run:
EXEC master.dbo.sp_ManageRunnerPermissions 
    @LoginName = 'DOMAIN\YourRunnerAccount', 
    @Action = 'REVOKE', 
    @UserDB = 'MyTargetDB';
