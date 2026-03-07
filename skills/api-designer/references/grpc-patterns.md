# gRPC Service Patterns

Best practices for gRPC API design using Protocol Buffers. Source of truth for Design, Spec, and Review modes when protocol is gRPC.

## Contents

1. [Proto File Organization](#proto-file-organization)
2. [Service Design](#service-design)
3. [Message Design](#message-design)
4. [Error Handling](#error-handling)
5. [Streaming Patterns](#streaming-patterns)
6. [Versioning](#versioning)

---

## Proto File Organization

### Package Naming

```protobuf
syntax = "proto3";
package mycompany.users.v1;

option go_package = "github.com/mycompany/api/users/v1";
option java_package = "com.mycompany.api.users.v1";
```

- Reverse domain + service + version: `company.service.v1`
- One service per proto file for large APIs
- Shared types in separate `common/` proto files
- Version in package name, not in service name

### File Structure

```
proto/
  common/
    pagination.proto
    error_details.proto
  users/
    v1/
      users_service.proto
      users_messages.proto
  orders/
    v1/
      orders_service.proto
```

## Service Design

### Naming Conventions

- Service: `UserService`, `OrderService` (PascalCase + "Service")
- RPC methods: `GetUser`, `ListUsers`, `CreateUser` (PascalCase verb + noun)
- Request/Response: `GetUserRequest`, `GetUserResponse` (method name + Request/Response)

### Standard Method Patterns

```protobuf
service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty);
}
```

### Custom Methods

```protobuf
rpc ActivateUser(ActivateUserRequest) returns (User);
rpc BatchGetUsers(BatchGetUsersRequest) returns (BatchGetUsersResponse);
```

- Prefix with verb describing the action
- Batch methods for multi-resource operations

## Message Design

### Field Numbering

- Reserve 1-15 for frequently used fields (1-byte encoding)
- Never reuse deleted field numbers; use `reserved`
- Use `reserved 4, 8 to 12;` to prevent reuse

### Field Types

```protobuf
message User {
  string id = 1;
  string name = 2;
  string email = 3;
  UserRole role = 4;
  google.protobuf.Timestamp created_at = 5;
  optional string bio = 6;
  repeated string tags = 7;
  map<string, string> metadata = 8;
}
```

- Use `optional` for fields that may be absent
- Use `repeated` for lists (never nullable)
- Use `map` for key-value pairs
- Use well-known types: `Timestamp`, `Duration`, `Empty`, `FieldMask`

### Update Pattern with FieldMask

```protobuf
message UpdateUserRequest {
  string id = 1;
  User user = 2;
  google.protobuf.FieldMask update_mask = 3;
}
```

- `FieldMask` specifies which fields to update (partial update)
- Prevents overwriting unset fields with defaults

## Error Handling

### Status Codes

| Code | Use |
|------|-----|
| OK (0) | Success |
| INVALID_ARGUMENT (3) | Client sent invalid data |
| NOT_FOUND (5) | Resource does not exist |
| ALREADY_EXISTS (6) | Duplicate create |
| PERMISSION_DENIED (7) | Authenticated but not authorized |
| UNAUTHENTICATED (16) | Missing or invalid credentials |
| RESOURCE_EXHAUSTED (8) | Rate limit or quota exceeded |
| FAILED_PRECONDITION (9) | System not in required state |
| INTERNAL (13) | Unexpected server error |
| UNAVAILABLE (14) | Transient failure, retry |
| DEADLINE_EXCEEDED (4) | Timeout |

### Error Details

```protobuf
import "google/rpc/error_details.proto";

// Attach via status.WithDetails():
// - BadRequest for validation errors
// - RetryInfo for transient failures
// - ErrorInfo for machine-readable codes
```

- Use standard error detail types from `google/rpc/error_details.proto`
- Include `ErrorInfo` with domain, reason, and metadata
- Never expose internal details in error messages

## Streaming Patterns

### Server Streaming

```protobuf
rpc ListEvents(ListEventsRequest) returns (stream Event);
```

Use for: real-time feeds, large result sets, progress updates.

### Client Streaming

```protobuf
rpc UploadChunks(stream UploadChunkRequest) returns (UploadResponse);
```

Use for: file uploads, batch ingestion.

### Bidirectional Streaming

```protobuf
rpc Chat(stream ChatMessage) returns (stream ChatMessage);
```

Use for: real-time bidirectional communication, collaborative editing.

### Rules

- Always handle stream errors and cancellation
- Include keepalive pings for long-lived streams
- Set reasonable deadlines on unary RPCs (default: 30s)
- Streaming RPCs should support backpressure

## Versioning

- Version in package name: `users.v1`, `users.v2`
- Additive changes within a version (new fields, new RPCs) are non-breaking
- Never change field types or numbers within a version
- Use `reserved` for removed fields
- Run both v1 and v2 services during migration period
- Deprecate with `[deprecated = true]` field option
