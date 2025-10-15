-- Pipeline Builder Database Schema

-- Store pipeline configurations
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pipeline_configurations' AND xtype='U')
BEGIN
    CREATE TABLE pipeline_configurations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        workspace_id NVARCHAR(255) NOT NULL,
        pipeline_name NVARCHAR(255) NOT NULL,
        pipeline_id NVARCHAR(255),  -- Fabric pipeline ID after deployment
        source_type NVARCHAR(50) NOT NULL,  -- 'azure_sql', 'blob_storage', 'db2', 'api'
        source_config NVARCHAR(MAX),  -- JSON with connection details (encrypted)
        medallion_enabled BIT DEFAULT 1,
        bronze_table NVARCHAR(255),
        silver_table NVARCHAR(255),
        gold_table NVARCHAR(255),
        schedule NVARCHAR(50) DEFAULT 'manual',  -- 'manual', 'hourly', 'daily', 'weekly'
        status NVARCHAR(50) DEFAULT 'draft',  -- 'draft', 'deployed', 'failed', 'running'
        created_by NVARCHAR(255) NOT NULL,
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        deployed_at DATETIME2,
        fabric_pipeline_json NVARCHAR(MAX),  -- Full Fabric pipeline definition
        ai_conversation NVARCHAR(MAX),  -- Conversation history with Claude
        CONSTRAINT FK_pipeline_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
END
GO

-- Store pipeline execution history
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pipeline_executions' AND xtype='U')
BEGIN
    CREATE TABLE pipeline_executions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        pipeline_config_id INT NOT NULL,
        execution_id NVARCHAR(255),  -- Fabric execution ID
        status NVARCHAR(50) DEFAULT 'running',  -- 'running', 'succeeded', 'failed', 'cancelled'
        start_time DATETIME2 DEFAULT GETDATE(),
        end_time DATETIME2,
        error_message NVARCHAR(MAX),
        rows_processed INT,
        duration_seconds INT,
        triggered_by NVARCHAR(255),
        CONSTRAINT FK_execution_pipeline FOREIGN KEY (pipeline_config_id) REFERENCES pipeline_configurations(id)
    );
END
GO

-- Store transformation definitions
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pipeline_transformations' AND xtype='U')
BEGIN
    CREATE TABLE pipeline_transformations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        pipeline_config_id INT NOT NULL,
        layer NVARCHAR(20) NOT NULL,  -- 'bronze', 'silver', 'gold'
        transformation_type NVARCHAR(50),  -- 'deduplication', 'type_conversion', 'join', 'aggregation'
        transformation_logic NVARCHAR(MAX),  -- SQL or PySpark code
        notebook_name NVARCHAR(255),
        notebook_id NVARCHAR(255),  -- Fabric notebook ID after deployment
        execution_order INT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE(),
        CONSTRAINT FK_transformation_pipeline FOREIGN KEY (pipeline_config_id) REFERENCES pipeline_configurations(id)
    );
END
GO

-- Store source connections (with encrypted credentials)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='source_connections' AND xtype='U')
BEGIN
    CREATE TABLE source_connections (
        id INT IDENTITY(1,1) PRIMARY KEY,
        workspace_id NVARCHAR(255) NOT NULL,
        connection_name NVARCHAR(255) NOT NULL,
        source_type NVARCHAR(50) NOT NULL,  -- 'azure_sql', 'blob_storage', 'db2'
        connection_string NVARCHAR(MAX),  -- Encrypted connection string
        host NVARCHAR(255),
        port INT,
        database_name NVARCHAR(255),
        username NVARCHAR(255),
        password_encrypted NVARCHAR(MAX),  -- Encrypted password
        additional_config NVARCHAR(MAX),  -- JSON for extra config
        created_by NVARCHAR(255) NOT NULL,
        created_at DATETIME2 DEFAULT GETDATE(),
        last_validated DATETIME2,
        validation_status NVARCHAR(50),  -- 'valid', 'invalid', 'unknown'
        validation_error NVARCHAR(MAX),
        CONSTRAINT FK_connection_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
END
GO

-- Store AI conversation history (for debugging and improvement)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ai_conversations' AND xtype='U')
BEGIN
    CREATE TABLE ai_conversations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        pipeline_config_id INT,
        user_email NVARCHAR(255) NOT NULL,
        message_role NVARCHAR(20) NOT NULL,  -- 'user', 'assistant'
        message_content NVARCHAR(MAX) NOT NULL,
        timestamp DATETIME2 DEFAULT GETDATE(),
        tokens_used INT,
        CONSTRAINT FK_conversation_pipeline FOREIGN KEY (pipeline_config_id) REFERENCES pipeline_configurations(id)
    );
END
GO

-- Create indexes for better performance
CREATE INDEX IX_pipeline_workspace ON pipeline_configurations(workspace_id);
CREATE INDEX IX_pipeline_created_by ON pipeline_configurations(created_by);
CREATE INDEX IX_pipeline_status ON pipeline_configurations(status);
CREATE INDEX IX_execution_pipeline ON pipeline_executions(pipeline_config_id);
CREATE INDEX IX_execution_status ON pipeline_executions(status);
CREATE INDEX IX_connection_workspace ON source_connections(workspace_id);
CREATE INDEX IX_conversation_pipeline ON ai_conversations(pipeline_config_id);
GO

PRINT 'Pipeline Builder database schema created successfully';
