# Manus AI Agent 用户系统

## 概述

Manus AI Agent 现已集成完整的多用户系统，支持用户注册、登录、身份验证和权限管理。系统使用 JWT (JSON Web Token) 进行身份验证，用户信息存储在 MongoDB 中。

## 功能特性

- 用户注册和登录
- 临时用户创建
- JWT 身份验证
- 多种认证类型支持 (密码认证、临时用户)
- 密码哈希存储

## API 接口

### 用户认证

#### 注册用户
```http
POST /api/v1/users/register
Content-Type: application/json

{
    "username": "user123",
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
}
```

#### 用户登录
```http
POST /api/v1/users/login
Content-Type: application/json

{
    "username": "user123",
    "password": "securepassword"
}
```

响应示例：
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "user": {
            "id": "user-uuid",
            "username": "user123",
            "email": "user@example.com",
            "auth_type": "password",
            "full_name": "John Doe",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "last_login_at": "2024-01-01T00:00:00Z"
        }
    }
}
```

#### 创建临时用户
```http
POST /api/v1/users/temporary
```

响应示例：
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "user": {
            "id": "temp-user-uuid",
            "username": "temp_a1b2c3d4",
            "email": "temp_a1b2c3d4@temporary.local",
            "auth_type": "temporary",
            "full_name": "Temporary User a1b2c3d4",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "last_login_at": null
        }
    }
}
```

### 用户信息管理

#### 获取当前用户信息
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

#### 更新当前用户信息
```http
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "username": "newusername",
    "email": "newemail@example.com",
    "full_name": "Jane Doe",
    "password": "newpassword"
}
```

#### 获取指定用户信息
```http
GET /api/v1/users/{user_id}
Authorization: Bearer <access_token>
```



## 认证和授权

### JWT Token 使用

所有需要身份验证的接口都需要在请求头中包含 JWT token：

```http
Authorization: Bearer <access_token>
```



## 环境配置

在 `.env` 文件中添加以下配置：

```env
# JWT 配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```



## 数据模型

### User 模型

```python
class User:
    id: str                    # 用户ID
    username: str              # 用户名
    email: str                 # 邮箱
    hashed_password: str       # 哈希密码
    auth_type: AuthType        # 认证类型 (password/temporary)
    full_name: Optional[str]   # 全名
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    last_login_at: datetime    # 最后登录时间
```

### 认证类型

```python
class AuthType(str, Enum):
    PASSWORD = "password"      # 用户名密码认证
    TEMPORARY = "temporary"    # 临时用户
```

## 安全特性

1. **密码哈希**: 使用 bcrypt 算法哈希存储密码
2. **JWT 签名**: 使用配置的密钥签名 JWT token
3. **Token 过期**: Token 有过期时间限制

## 错误处理

系统会返回标准的错误响应：

```json
{
    "success": false,
    "error": {
        "code": 400,
        "message": "User already exists",
        "details": null
    }
}
```

常见错误代码：
- 400: 请求参数错误
- 401: 未授权访问
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 临时用户说明

### 临时用户特性
- 系统自动生成用户名和邮箱
- 无需手动注册，立即可用
- 生成唯一的临时 token
- 用户名格式：`temp_<random_id>`
- 邮箱格式：`temp_<random_id>@temporary.local`

### 使用场景
- 快速体验系统功能
- 无需注册的快速访问
- 临时会话和测试

### 安全考虑
- 临时用户仍有独立的用户 ID 和认证 token
- 数据隔离与普通用户相同
- 可根据需要设置过期策略

## 与现有系统集成

用户系统已经集成到现有的 session 和 agent 系统中，后续可以：

1. 为每个 session 关联用户
2. 实现用户级别的资源隔离
3. 添加用户使用量统计
4. 基于认证类型实现不同的功能限制 