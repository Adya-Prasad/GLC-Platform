import { API_BASE } from './utils.js';

export async function login(role) {
    try {
        const res = await fetch(`${API_BASE}/auth/login?role=${role}`);
        const user = await res.json();
        localStorage.setItem('glc_user', JSON.stringify(user));
        window.location.href = '/';
    } catch (e) {
        console.error("Login failed", e);
        // Fallback for demo if API fails
        const user = { name: `Demo ${role}`, role, token: 'demo' };
        localStorage.setItem('glc_user', JSON.stringify(user));
        window.location.href = '/';
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
