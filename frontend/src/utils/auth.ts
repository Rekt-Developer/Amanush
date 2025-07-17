// Authentication utility functions
import type { User, UserRole } from '../api/auth'

/**
 * Check if user has specific permission
 */
export function hasPermission(user: User | null, permission: string): boolean {
  if (!user || !user.is_active) return false
  
  // Admin has all permissions
  if (user.role === 'admin') return true
  
  // Define role-based permissions
  const rolePermissions: Record<UserRole, string[]> = {
    admin: ['*'], // Admin has all permissions
    user: [
      'read:profile',
      'update:profile',
      'change:password',
      'create:session',
      'read:session',
      'update:session',
      'delete:session',
      'upload:file',
      'read:file',
      'delete:file'
    ]
  }
  
  const userPermissions = rolePermissions[user.role] || []
  return userPermissions.includes('*') || userPermissions.includes(permission)
}

/**
 * Check if user can access admin features
 */
export function canAccessAdmin(user: User | null): boolean {
  return hasPermission(user, 'admin:access')
}

/**
 * Check if user can manage other users
 */
export function canManageUsers(user: User | null): boolean {
  return hasPermission(user, 'manage:users') || user?.role === 'admin'
}

/**
 * Check if user can manage sessions
 */
export function canManageSessions(user: User | null): boolean {
  return hasPermission(user, 'manage:sessions')
}

/**
 * Check if user can upload files
 */
export function canUploadFiles(user: User | null): boolean {
  return hasPermission(user, 'upload:file')
}

/**
 * Check if user can view specific user's data
 */
export function canViewUser(currentUser: User | null, targetUserId: string): boolean {
  if (!currentUser || !currentUser.is_active) return false
  
  // Users can view their own data
  if (currentUser.id === targetUserId) return true
  
  // Admins can view all users
  return currentUser.role === 'admin'
}

/**
 * Check if user can edit specific user's data
 */
export function canEditUser(currentUser: User | null, targetUserId: string): boolean {
  if (!currentUser || !currentUser.is_active) return false
  
  // Users can edit their own data
  if (currentUser.id === targetUserId) return true
  
  // Admins can edit all users
  return currentUser.role === 'admin'
}

/**
 * Check if user can delete specific user
 */
export function canDeleteUser(currentUser: User | null, targetUserId: string): boolean {
  if (!currentUser || !currentUser.is_active) return false
  
  // Users cannot delete themselves
  if (currentUser.id === targetUserId) return false
  
  // Only admins can delete users
  return currentUser.role === 'admin'
}

/**
 * Get user display name
 */
export function getUserDisplayName(user: User | null): string {
  if (!user) return 'Guest'
  return user.username || user.email || 'Unknown User'
}

/**
 * Get user role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    admin: 'Administrator',
    user: 'User'
  }
  return roleNames[role] || role
}

/**
 * Check if user account is expired or needs attention
 */
export function getUserAccountStatus(user: User | null): {
  isValid: boolean
  isActive: boolean
  needsAttention: boolean
  message?: string
} {
  if (!user) {
    return {
      isValid: false,
      isActive: false,
      needsAttention: true,
      message: 'No user data available'
    }
  }
  
  if (!user.is_active) {
    return {
      isValid: false,
      isActive: false,
      needsAttention: true,
      message: 'Account is deactivated'
    }
  }
  
  return {
    isValid: true,
    isActive: true,
    needsAttention: false
  }
}

/**
 * Format user creation date
 */
export function formatUserDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return 'Invalid date'
  }
}

/**
 * Generate user avatar URL or initials
 */
export function getUserAvatar(user: User | null): {
  type: 'initials' | 'url'
  value: string
} {
  if (!user) {
    return {
      type: 'initials',
      value: 'G'
    }
  }
  
  // Generate initials from username or email
  const name = user.username || user.email || 'U'
  const initials = name
    .split(/[\s@]/)
    .map(part => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('')
  
  return {
    type: 'initials',
    value: initials || 'U'
  }
}

/**
 * Validate user input for registration/profile update
 */
export function validateUserInput(data: {
  username?: string
  email?: string
  password?: string
}): {
  isValid: boolean
  errors: Record<string, string>
} {
  const errors: Record<string, string> = {}
  
  // Username validation
  if (data.username !== undefined) {
    if (!data.username || data.username.trim().length < 3) {
      errors.username = 'Username must be at least 3 characters long'
    } else if (!/^[a-zA-Z0-9_-]+$/.test(data.username)) {
      errors.username = 'Username can only contain letters, numbers, underscores, and hyphens'
    }
  }
  
  // Email validation
  if (data.email !== undefined) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!data.email || !emailRegex.test(data.email)) {
      errors.email = 'Please enter a valid email address'
    }
  }
  
  // Password validation
  if (data.password !== undefined) {
    if (!data.password || data.password.length < 6) {
      errors.password = 'Password must be at least 6 characters long'
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
} 