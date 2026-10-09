/** Local compose publishes the admin proxy here. The live site uses the subdomain instead. */
const LOCAL_ADMIN_PORT = '8082'

/** The admin subdomain (admin.localhost, admin.айти-кадры.рф, and its punycode name). */
export function isAdminHost(hostname?: string, port?: string): boolean {
  const host = hostname ?? (typeof window === 'undefined' ? '' : window.location.hostname)
  const currentPort = port ?? (typeof window === 'undefined' ? '' : window.location.port)
  return host === 'admin' || host.startsWith('admin.') || currentPort === LOCAL_ADMIN_PORT
}
