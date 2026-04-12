# MCP Central Docs Update: FastMCP 3.x Unified Gateway

**Update Type**: Architecture Enhancement  
**Target**: MCP Central Documentation Repository  
**Priority**: Critical - Fleet-Wide Impact  
**Date**: March 4, 2026  

---

## 🎯 Update Summary

FastMCP 3.x introduces the **Unified Gateway pattern** - a revolutionary architectural improvement that consolidates MCP protocol and HTTP API services into a single FastAPI application. This update requires immediate documentation updates to support fleet-wide migrations.

---

## 📝 Documentation Updates Required

### 1. Architecture Section Updates

#### New Section: "Unified Gateway Pattern"
```markdown
## FastMCP 3.x Unified Gateway

The Unified Gateway pattern consolidates MCP protocol and HTTP API services into a single FastAPI application, providing:

- Single process deployment
- Shared state management
- Unified lifecycle management
- Reduced resource usage

### Implementation
```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI(lifespan=lifespan_manager)
mcp = FastMCP.from_fastapi(app, name="My Server")
```

### Transport Modes
- **stdio**: MCP protocol only (legacy compatibility)
- **http**: HTTP API only (webapp-only deployments)
- **dual**: Both MCP and HTTP (recommended for new deployments)
```

#### Update Existing: "Server Architecture"
```markdown
# BEFORE
"FastMCP servers typically run as stdio processes..."

# AFTER  
"FastMCP 3.x servers can run in multiple modes:
- Legacy stdio transport for AI agents
- HTTP API for web applications  
- Dual mode for unified deployments"
```

### 2. Quick Start Guide Updates

#### Update "Creating Your First Server"
```markdown
# FastMCP 3.x Quick Start

## Step 1: Dependencies
```bash
pip install fastmcp>=3.0.0 fastapi uvicorn
```

## Step 2: Create Unified Server
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting unified gateway...")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
mcp = FastMCP.from_fastapi(app, name="My Server")

@mcp.tool()
def hello():
    return "Hello from unified gateway!"

@app.get("/api/v1/status")
async def status():
    return {"status": "unified"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Step 3: Run in Dual Mode
```bash
python server.py --mode dual --port 8080
```
```

### 3. Best Practices Section

#### New Section: "Unified Gateway Best Practices"
```markdown
## Unified Gateway Best Practices

### State Management
- Use global state for shared data between MCP and HTTP interfaces
- Implement proper cleanup in lifespan managers
- Consider thread safety for concurrent access

### Performance Optimization
- Leverage FastAPI's async capabilities
- Use connection pooling for external services
- Implement proper error boundaries

### Security
- Add authentication middleware for HTTP endpoints
- Validate inputs for both MCP tools and HTTP routes
- Implement rate limiting for public APIs
```

### 4. Migration Guide Section

#### New Section: "Migrating to FastMCP 3.x"
```markdown
## Migration Guide: FastMCP 2.x → 3.x

### Automatic Migration Script
```bash
# Install migration tool
pip install fastmcp-migration

# Migrate existing server
fastmcp-migrate --source server.py --output server_v3.py
```

### Manual Migration Steps
1. Update dependencies to fastmcp>=3.0.0
2. Refactor to use FastMCP.from_fastapi()
3. Implement lifespan management
4. Update deployment scripts
5. Test all transport modes

### Common Issues
- Import order: FastAPI before FastMCP
- Lifespan context managers required
- Route registration order matters
```

---

## 🔧 Code Examples for Documentation

### Basic Server Example
```python
# docs/examples/basic-unified-server.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting unified gateway...")
    yield
    # Cleanup
    print("🛑 Shutting down...")

app = FastAPI(
    title="My MCP Server",
    description="Unified Gateway Example",
    lifespan=lifespan
)

mcp = FastMCP.from_fastapi(app, name="My Server")

@mcp.tool()
def get_status():
    """Get server status - accessible by AI agents"""
    return {"status": "running", "mode": "unified"}

@app.get("/api/v1/status")
async def get_status_http():
    """Get server status - accessible by webapps"""
    return {"status": "running", "mode": "unified"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Advanced Webapp Integration
```python
# docs/examples/webapp-integration.py
from typing import Dict, Any
from fastapi import FastAPI
from fastmcp import FastMCP
from fastapi.responses import StreamingResponse

# Shared state for both interfaces
_shared_state: Dict[str, Any] = {
    "telemetry": {},
    "connected_clients": 0
}

app = FastAPI()
mcp = FastMCP.from_fastapi(app, name="Robot Controller")

@mcp.tool()
def get_telemetry():
    """MCP tool for AI agents"""
    return _shared_state["telemetry"]

@app.get("/api/v1/telemetry")
async def get_telemetry_http():
    """HTTP endpoint for webapps"""
    return _shared_state["telemetry"]

@app.get("/api/v1/video/stream")
async def video_stream():
    """Video streaming for webapps"""
    return StreamingResponse(
        generate_video_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

def update_telemetry(data):
    """Update shared state from hardware"""
    _shared_state["telemetry"] = data
    # Both MCP and HTTP interfaces see updates immediately
```

---

## 📋 Implementation Checklist

### Documentation Updates
- [ ] **Architecture Guide**: Add Unified Gateway section
- [ ] **Quick Start**: Update with FastMCP 3.x examples
- [ ] **Best Practices**: Add unified gateway patterns
- [ ] **Migration Guide**: Complete 2.x → 3.x migration steps
- [ ] **API Reference**: Document new transport modes
- [ ] **Examples**: Add unified gateway code samples

### Code Examples
- [ ] **Basic Server**: Simple unified gateway example
- [ ] **Webapp Integration**: HTTP + MCP integration
- [ ] **State Management**: Shared state patterns
- [ ] **Streaming**: Video/media streaming examples
- [ ] **Error Handling**: Robust error management
- [ ] **Testing**: Unit and integration test examples

### Migration Resources
- [ ] **Migration Tool**: Automated migration script
- [ ] **Checklist**: Step-by-step migration guide
- [ ] **Troubleshooting**: Common issues and solutions
- [ ] **Performance**: Benchmarks and optimization tips

---

## 🎯 Target Audience Impact

### For MCP Server Developers
- **Immediate Need**: Understanding new architecture pattern
- **Learning Curve**: Moderate - familiar FastAPI concepts
- **Benefits**: Simplified deployment, better performance

### For Webapp Developers  
- **Immediate Need**: Updated API integration patterns
- **Learning Curve**: Low - standard HTTP APIs
- **Benefits**: Single endpoint, consistent interfaces

### For System Administrators
- **Immediate Need**: Updated deployment procedures
- **Learning Curve**: Low - fewer processes to manage
- **Benefits**: Simplified operations, reduced resource usage

---

## 🚀 Rollout Plan

### Phase 1: Documentation Updates (Week 1)
- Update architecture sections
- Add migration guide
- Create code examples
- Update quick start guide

### Phase 2: Community Communication (Week 2)
- Blog post announcement
- Documentation release notes
- Community forum discussions
- Webinar on new features

### Phase 3: Tooling Support (Week 3)
- Release migration tools
- Update IDE extensions
- Update CLI tools
- Add validation scripts

### Phase 4: Fleet Migration Support (Week 4-6)
- Provide migration consulting
- Create troubleshooting guides
- Offer office hours support
- Monitor adoption metrics

---

## 📊 Success Metrics

### Documentation Metrics
- [ ] **100%** of architecture sections updated
- [ ] **10+** new code examples added
- [ ] **95%** positive feedback on migration guide
- [ ] **0** critical documentation bugs

### Community Metrics
- [ ] **80%** of developers aware of Unified Gateway
- [ ] **60%** of new servers using unified pattern
- [ ] **90%** successful migration rate
- [ ] **50%** reduction in support tickets for deployment issues

---

## 🔗 Related Resources

### Internal Resources
- [FastMCP 3.x Release Notes](internal/releases/fastmcp-3.0)
- [Unified Gateway Design Document](internal/design/unified-gateway)
- [Migration Test Results](internal/testing/migration-results)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Async Python Best Practices](https://docs.python.org/3/library/asyncio.html)

---

## 🎉 Conclusion

The FastMCP 3.x Unified Gateway represents the **most significant architectural improvement** in MCP server development since the initial release. This documentation update is **critical for supporting the ecosystem transition** and ensuring successful fleet-wide migrations.

**Priority**: CRITICAL - Complete documentation updates before major community announcement.

**Timeline**: 2 weeks for full documentation update and community communication.
