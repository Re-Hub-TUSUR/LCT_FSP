import { z } from 'zod'

const envSchema = z.object({
  VITE_API_URL: z.string().trim().min(1).default('/api/v1'),
  MODE: z.string(),
  DEV: z.boolean(),
})

const parsed = envSchema.safeParse(import.meta.env)

if (!parsed.success) {
  throw new Error(`Invalid frontend environment: ${z.prettifyError(parsed.error)}`)
}

export const env = {
  apiUrl: parsed.data.VITE_API_URL.replace(/\/+$/, ''),
  mode: parsed.data.MODE,
  isDev: parsed.data.DEV,
} as const
