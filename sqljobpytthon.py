import pyodbc
import time

server = 'YOUR_SERVER_NAME'
database = 'msdb'
username = 'YOUR_USERNAME'
password = 'YOUR_PASSWORD'
job_name = 'Your_Job_Name'

conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
)

cursor = conn.cursor()

# Step 1: Start job
cursor.execute("EXEC msdb.dbo.sp_start_job @job_name = ?", job_name)
conn.commit()
print("Job triggered...")

# Step 2: Get job_id
cursor.execute("""
SELECT job_id FROM msdb.dbo.sysjobs WHERE name = ?
""", job_name)
job_id = cursor.fetchone()[0]

# Step 3: Wait for completion
print("Waiting for job to complete...")
while True:
    time.sleep(5)
    
    cursor.execute("""
    SELECT TOP 1 run_status
    FROM msdb.dbo.sysjobhistory
    WHERE job_id = ? AND step_id = 0
    ORDER BY run_date DESC, run_time DESC
    """, job_id)
    
    row = cursor.fetchone()
    if row:
        status = row[0]
        if status in (0, 1):  # Failed or Success
            break

print("Job finished. Fetching step logs...\n")

# Step 4: Fetch step-level logs
cursor.execute("""
SELECT 
    step_id,
    step_name,
    run_status,
    run_date,
    run_time,
    run_duration,
    message
FROM msdb.dbo.sysjobhistory
WHERE job_id = ?
  AND step_id > 0
ORDER BY instance_id DESC
""", job_id)

rows = cursor.fetchall()

# Step 5: Print logs
for row in rows:
    step_id, step_name, run_status, run_date, run_time, run_duration, message = row
    
    status_map = {
        0: "FAILED ❌",
        1: "SUCCESS ✅",
        2: "RETRY 🔁",
        3: "CANCELLED ⛔",
        4: "IN PROGRESS ⏳"
    }
    
    print(f"Step {step_id}: {step_name}")
    print(f"Status: {status_map.get(run_status, run_status)}")
    print(f"Date: {run_date} Time: {run_time}")
    print(f"Duration: {run_duration}")
    print(f"Message: {message}")
    print("-" * 50)

cursor.close()
conn.close()
