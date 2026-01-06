import { API_BASE } from './utils.js';

export async function login(role, name, passcode) {
    try {
        const res = await fetch(`${API_BASE}/auth/login?role=${role}&name=${encodeURIComponent(name)}&passcode=${passcode}`);
        const data = await res.json();

        // Check for errors
        if (data.error || data.status === 'passcode_mismatch' || data.status === 'error') {
            return {
                success: false,
                status: data.status,
                error: data.error
            };
        }

        // Success - save user data
        localStorage.setItem('glc_user', JSON.stringify(data));
        return {
            success: true,
            status: data.status,
            name: data.name
        };
    } catch (e) {
        console.error("Login failed", e);
        return {
            success: false,
            status: 'error',
            error: 'Network error - please try again'
        };
    }
}

export function logout() {
    localStorage.removeItem('glc_user');
    window.location.href = '/login';
}

export function requireAuth() {
    if (!localStorage.getItem('glc_user')) {
        window.location.href = '/login';
        return null;
    }
    return JSON.parse(localStorage.getItem('glc_user'));
}
