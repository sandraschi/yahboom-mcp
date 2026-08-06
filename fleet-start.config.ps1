# Per-repo fleet start config for yahboom-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'yahboom-mcp'
    BackendPort  = 10892
    FrontendPort = 10893
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\yahboom-mcp\webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'yahboom_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10892' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
