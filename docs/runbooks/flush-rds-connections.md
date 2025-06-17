# RDS Connection Alarm Runbook: Flushing Idle Connections

## Overview

This runbook provides instructions for handling RDS connection alarms,
by identifying and terminating idle database connections that are
preventing proper resource management.

## When to Use This Runbook

Use this runbook when:

- RDS connection alarm has been triggered
- Database connection count is approaching or has exceeded limits
- Applications are experiencing connection timeouts
- Database performance is degraded due to connection exhaustion

## Prerequisites

- Access to the `navigator-scripts` repository
- Proper AWS credentials and permissions
- Access to the bastion host
- PostgreSQL client installed

## Connection Setup

### Step 1: Connect to the Database via Bastion

Use the `nav-stack-connect` script to establish a connection
through the bastion host.

For detailed connection instructions, refer to the [nav-stack-connect tutorial](https://github.com/climatepolicyradar/navigator-scripts/blob/main/docs/nav-stack-connect.md).

## Diagnosis Steps

### Step 2: Analyze Current Connections

Once connected to the PostgreSQL database,
run the following query to view all active connections grouped by their status:

```sql
SELECT
  datname AS database,
  usename AS username,
  application_name,
  client_addr,
  state,
  count(*) AS connection_count
FROM
  pg_stat_activity
GROUP BY
  datname, usename, application_name, client_addr, state
ORDER BY
  connection_count DESC;
```

### Step 3: Interpret the Results

Look for concerning patterns in the output:

- **`idle in transaction`** - These are the most problematic as they:
  - Hold locks that block other operations
  - Prevent PostgreSQL from performing garbage collection
  - Indicate uncommitted/unrolled back transactions
- **`idle`** - Less critical but still consuming connection slots
- **`active`** - Currently executing queries (generally normal)

Example output showing a problem state:

```markdown
database | username | application_name | client_addr | state | connection_count
-----------+-----------------+------------------------+--------------+---------------------+------------------
navigator | navigator_admin | | 10.0.137.94 | idle in transaction | 36
navigator | navigator_admin | | 10.0.161.224 | idle in transaction | 31
navigator | navigator_admin | | 10.0.139.147 | idle | 7
```

In this example, 67 "idle in transaction" connections indicate a serious issue.

## Resolution Steps

### Step 4: Terminate Idle Connections

If you identify a high number of problematic connections, terminate them using:

#### For "idle in transaction" connections (most critical)

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction';
```

#### For all idle connections (use with caution)

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state IN ('idle', 'idle in transaction');
```

### Step 5: Verify Resolution

Re-run the connection analysis query from Step 2 to confirm connections
have been terminated and the count has decreased.

## Post-Resolution Actions

### Step 6: Identify Root Cause

1. **Identify Source IPs**
   Note the `client_addr` values from the problematic connections
2. **Map IPs to Services**
   Determine which applications/services these IPs belong to
3. **Review Application Logs**
   Check for transaction handling issues in the identified services

### Step 7: Preventive Measures

Document findings and consider:

- Reviewing application connection pooling settings
- Implementing connection timeouts
- Adding transaction timeout configurations
- Monitoring for uncommitted transactions

## Important Notes

⚠️ **Caution**: Terminating connections will abort any in-progress transactions.
Ensure you understand the impact before executing termination commands.

⚠️ **Root Cause**: Simply terminating connections treats the symptom, not the cause.
Always investigate why connections are being left in an idle state.

## Monitoring

After resolution, monitor:

- RDS connection metrics in CloudWatch
- Application error logs for connection failures
- Database performance metrics

## Escalation

If the issue persists or recurs frequently:

1. Investigate application code for transaction management issues
2. Review connection pooling configurations
3. Consider increasing RDS connection limits if appropriate
4. Escalate to the database team for further analysis

---

**Last Updated**: 2025-06-17  
**Maintained By**: Application Team
