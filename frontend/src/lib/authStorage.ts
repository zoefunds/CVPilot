const ACCESS = 'cvpilot.access_token';
const REFRESH = 'cvpilot.refresh_token';

function safeWindow(): Window | null {
  return typeof window === 'undefined' ? null : window;
}

export const tokenStorage = {
  getAccess(): string | null {
    return safeWindow()?.localStorage.getItem(ACCESS) ?? null;
  },
  getRefresh(): string | null {
    return safeWindow()?.localStorage.getItem(REFRESH) ?? null;
  },
  set(access: string, refresh: string): void {
    const w = safeWindow();
    if (!w) return;
    w.localStorage.setItem(ACCESS, access);
    w.localStorage.setItem(REFRESH, refresh);
  },
  clear(): void {
    const w = safeWindow();
    if (!w) return;
    w.localStorage.removeItem(ACCESS);
    w.localStorage.removeItem(REFRESH);
  },
};
